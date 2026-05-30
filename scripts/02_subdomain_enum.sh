#!/usr/bin/env bash
# ============================================================
# PHASE 2 — Subdomain Enumeration
# DNS bruteforce + CT log + permutation
# ============================================================
set -euo pipefail

APEX1="flynas.com"
APEX2="chi.gov.sa"
OUT="./results/osint"
mkdir -p "$OUT"
WL="./wordlists/subdomains_govsa.txt"

GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; NC='\033[0m'
banner() { echo -e "\n${CYAN}[*] $1${NC}"; }
ok()     { echo -e "${GREEN}[+] $1${NC}"; }
warn()   { echo -e "${YELLOW}[!] $1${NC}"; }

# ── 2.1 DNS Bruteforce (Python async) ─────────────────────────
banner "2.1 DNS Bruteforce"
for apex in "$APEX1" "$APEX2"; do
    outfile="$OUT/subdomains_$apex.txt"
    echo "  Bruteforcing *.$apex with $(wc -l < "$WL") words..."
    python3 << PYEOF > "$outfile" 2>/dev/null
import socket, asyncio, sys

async def check(sem, sub, apex, found):
    fqdn = f"{sub}.{apex}"
    async with sem:
        try:
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(None, socket.gethostbyname, fqdn)
            found.append((fqdn, res))
        except: pass

async def main():
    apex = "$apex"
    with open("$WL") as f:
        words = [l.strip() for l in f if l.strip() and not l.startswith('#')]
    sem = asyncio.Semaphore(50)
    found = []
    await asyncio.gather(*[check(sem, w, apex, found) for w in words])
    for fqdn, ip in sorted(found):
        print(f"{fqdn},{ip}")

asyncio.run(main())
PYEOF
    count=$(wc -l < "$outfile")
    ok "Found $count live subdomains for $apex → $outfile"
    head -20 "$outfile" 2>/dev/null || true
done

# ── 2.2 Permutation Generation ────────────────────────────────
banner "2.2 Permutation Subdomain Generation"
python3 << 'PYEOF'
prefixes = ["api","dev","staging","uat","test","beta","admin","portal",
            "auth","login","sso","internal","mail","smtp","ftp","vpn",
            "app","mobile","m","web","cdn","static","assets","media",
            "git","jenkins","ci","db","monitoring","grafana","kibana",
            "help","support","docs","status","health","metrics","backup"]
apexes = ["flynas.com","chi.gov.sa"]
out = []
for apex in apexes:
    # prefix.apex
    for p in prefixes:
        out.append(f"{p}.{apex}")
    # prefix-env.apex
    for p in ["api","app","portal","admin"]:
        for env in ["dev","staging","uat","test","prod","v1","v2"]:
            out.append(f"{p}-{env}.{apex}")
for sub in sorted(set(out)):
    print(sub)
PYEOF

# ── 2.3 Wildcard Detection ────────────────────────────────────
banner "2.3 Wildcard DNS Detection"
for apex in "$APEX1" "$APEX2"; do
    random_sub="notexist-$(date +%s)-test.$apex"
    ip=$(python3 -c "import socket; print(socket.gethostbyname('$random_sub'))" 2>/dev/null || echo "NXDOMAIN")
    if [ "$ip" = "NXDOMAIN" ]; then
        ok "$apex — No wildcard DNS (NXDOMAIN for random sub)"
    else
        warn "$apex — WILDCARD DNS detected! All subs resolve to $ip (filter results)"
    fi
done

# ── 2.4 Virtual Host Discovery ────────────────────────────────
banner "2.4 Virtual Host Fuzzing (requires Saudi IP)"
cat << 'EOF'
# Run this from your device with Saudi IP:
# Uses the discovered IP and fuzzes Host headers

FLYNAS_IP="20.105.216.45"
for sub in $(cat ./results/osint/subdomains_flynas.com.txt | cut -d, -f1); do
    code=$(curl -sk -o /dev/null -w "%{http_code}" \
           --resolve "$sub:443:$FLYNAS_IP" \
           -H "Host: $sub" \
           "https://$FLYNAS_IP/" 2>/dev/null)
    [ "$code" != "000" ] && echo "$code $sub"
done
EOF

ok "Phase 2 complete → $OUT/subdomains_*.txt"

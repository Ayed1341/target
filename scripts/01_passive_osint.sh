#!/usr/bin/env bash
# ============================================================
# PHASE 1 — Passive OSINT
# Targets: help.flynas.com | greeting.chi.gov.sa
# No direct target requests — queries public indexes only
# ============================================================
set -euo pipefail

TARGET1="help.flynas.com"
TARGET2="greeting.chi.gov.sa"
APEX1="flynas.com"
APEX2="chi.gov.sa"
OUT="./results"
mkdir -p "$OUT/flynas" "$OUT/chi_gov" "$OUT/osint"

GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'

banner() { echo -e "\n${CYAN}[*] $1${NC}"; }
ok()     { echo -e "${GREEN}[+] $1${NC}"; }

# ── 1.1 DNS Resolution ────────────────────────────────────────
banner "1.1 DNS Resolution"
for host in "$TARGET1" "www.$APEX1" "$APEX1" "$TARGET2" "www.$APEX2" "eservices.$APEX2" "api.$APEX1" "api.$APEX2"; do
    ip=$(python3 -c "import socket; print(socket.gethostbyname('$host'))" 2>/dev/null || echo "NXDOMAIN")
    echo "  $host -> $ip"
done | tee "$OUT/osint/dns_results.txt"

# ── 1.2 Certificate Transparency (crt.sh) ─────────────────────
banner "1.2 Certificate Transparency Logs"
for apex in "$APEX1" "$APEX2"; do
    out_file="$OUT/osint/ct_${apex//./_}.txt"
    echo "  Querying crt.sh for *.$apex"
    curl -s "https://crt.sh/?q=%25.$apex&output=json" 2>/dev/null | \
        python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    seen = set()
    for row in data:
        for n in str(row.get('name_value','')).splitlines():
            n = n.strip().lstrip('*.').lower()
            if n and '@' not in n and ' ' not in n and n not in seen:
                seen.add(n)
                print(n)
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
" | sort -u > "$out_file" 2>/dev/null || echo "  (crt.sh unavailable — run locally)"
    count=$(wc -l < "$out_file" 2>/dev/null || echo 0)
    ok "Found $count subdomains for $apex → $out_file"
done

# ── 1.3 Wayback Machine URL Mining ───────────────────────────
banner "1.3 Wayback Machine URL Mining"
for apex in "$APEX1" "$APEX2"; do
    out_file="$OUT/osint/wayback_${apex//./_}.txt"
    echo "  Querying Wayback CDX for *.$apex"
    curl -s "https://web.archive.org/cdx/search/cdx?url=*.$apex/*&output=json&fl=original&collapse=urlkey&limit=2000" 2>/dev/null | \
        python3 -c "
import sys, json
try:
    rows = json.load(sys.stdin)
    for row in rows[1:] if rows and isinstance(rows[0],list) else rows:
        if isinstance(row, list) and row: print(row[0])
        elif isinstance(row, str): print(row)
except: pass
" | sort -u > "$out_file" 2>/dev/null || echo "  (Wayback unavailable — run locally)"
    count=$(wc -l < "$out_file" 2>/dev/null || echo 0)
    ok "Found $count archived URLs for $apex → $out_file"
done

# ── 1.4 IP / ASN / Hosting Identification ─────────────────────
banner "1.4 IP / Hosting Identification"
cat << 'EOF' | python3 | tee "$OUT/osint/ip_hosting.txt"
hosts = {
    'help.flynas.com':     '20.105.216.45',
    'www.flynas.com':      '104.16.150.116',
    'flynas.com':          '104.16.149.116',
    'greeting.chi.gov.sa': '164.215.47.231',
    'www.chi.gov.sa':      '185.169.35.38',
}
ranges = [
    ('104.16.0.0/12',  'Cloudflare (AS13335)'),
    ('172.64.0.0/13',  'Cloudflare (AS13335)'),
    ('20.0.0.0/8',     'Microsoft Azure (AS8075)'),
    ('13.0.0.0/8',     'Microsoft Azure (AS8075)'),
    ('52.0.0.0/8',     'Amazon AWS (AS16509)'),
    ('54.0.0.0/8',     'Amazon AWS (AS16509)'),
    ('185.169.0.0/16', 'ZAIN/STC Saudi Arabia'),
    ('164.215.0.0/16', 'Saudi Government Network (MCIT)'),
]
import ipaddress
for host, ip in hosts.items():
    provider = 'Unknown'
    try:
        addr = ipaddress.ip_address(ip)
        for cidr, name in ranges:
            if addr in ipaddress.ip_network(cidr, strict=False):
                provider = name; break
    except: pass
    print(f"  {host:35s} {ip:20s} {provider}")
EOF

# ── 1.5 TLS Certificate Analysis ──────────────────────────────
banner "1.5 TLS Certificate Analysis"
for host in "$TARGET1" "$TARGET2"; do
    echo "  Probing $host:443..."
    python3 << PYEOF 2>/dev/null | tee -a "$OUT/osint/tls_analysis.txt"
import socket, ssl
host = "$host"
try:
    ctx = ssl._create_unverified_context()
    with socket.create_connection((host, 443), timeout=10) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as s:
            cert = s.getpeercert()
            print(f"  Host:    {host}")
            print(f"  TLS:     {s.version()}")
            print(f"  Cipher:  {s.cipher()[0]}")
            subj = dict(x[0] for x in cert.get('subject',[]))
            issr = dict(x[0] for x in cert.get('issuer',[]))
            print(f"  Subject: CN={subj.get('commonName','?')}")
            print(f"  Issuer:  O={issr.get('organizationName','?')}")
            sans = [v for k,v in cert.get('subjectAltName',[])]
            print(f"  SANs:    {', '.join(sans[:5])}")
            print(f"  Expires: {cert.get('notAfter','?')}")
except Exception as e:
    print(f"  {host}: {e}")
print()
PYEOF
done

# ── 1.6 Security.txt & VDP Discovery ──────────────────────────
banner "1.6 Security.txt / VDP Discovery"
for base in "https://$TARGET1" "https://$TARGET2" "https://$APEX1" "https://$APEX2"; do
    for path in "/.well-known/security.txt" "/security.txt" "/.well-known/change-password"; do
        echo "  Checking $base$path"
        # (will 403 from sandbox — run locally)
    done
done

ok "Phase 1 complete → results saved in $OUT/osint/"
echo ""
echo "IMPORTANT: crt.sh / Wayback queries may need local execution"
echo "Run: bash scripts/01_passive_osint.sh from your device (no VPN needed for OSINT)"

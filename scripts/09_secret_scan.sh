#!/usr/bin/env bash
# ============================================================
# PHASE 9 — Secret & Credential Detection
# Scans JS files, HTML pages, and common config paths
# ============================================================
set -euo pipefail

TARGET1="https://help.flynas.com"
TARGET2="https://greeting.chi.gov.sa"
OUT="./results"

UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
banner() { echo -e "\n${CYAN}[*] $1${NC}"; }
ok()     { echo -e "${GREEN}[+] $1${NC}"; }
warn()   { echo -e "${YELLOW}[!] $1${NC}"; }
high()   { echo -e "${RED}[!!] $1${NC}"; }

scan_for_secrets() {
    local content="$1" source="$2" out="$3"
    python3 << PYEOF 2>/dev/null
import re, sys, math
from collections import Counter

content = open('/tmp/scan_content.txt', encoding='utf-8', errors='replace').read()
source = "$source"
out_file = "$out"

def entropy(s):
    if not s: return 0
    c = Counter(s)
    return -sum((v/len(s))*math.log2(v/len(s)) for v in c.values())

PATTERNS = {
    "AWS Access Key":     (r"AKIA[0-9A-Z]{16}", 3.0),
    "AWS Secret Key":     (r"(?i)aws.{0,20}secret.{0,20}['\"][0-9a-zA-Z/+]{40}['\"]", 3.5),
    "Google API Key":     (r"AIza[0-9A-Za-z\-_]{35}", 3.5),
    "Google OAuth":       (r"[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com", 3.0),
    "GitHub PAT":         (r"ghp_[0-9a-zA-Z]{36}|github_pat_[0-9a-zA-Z_]{82}", 3.5),
    "Slack Token":        (r"xox[baprs]-[0-9a-zA-Z\-]{10,}", 3.5),
    "Stripe Secret":      (r"sk_live_[0-9a-zA-Z]{24}", 4.0),
    "Stripe Publishable": (r"pk_live_[0-9a-zA-Z]{24}", 3.5),
    "SendGrid Key":       (r"SG\.[0-9a-zA-Z\-_.]{22}\.[0-9a-zA-Z\-_.]{43}", 4.0),
    "Twilio SID":         (r"AC[0-9a-fA-F]{32}", 3.5),
    "JWT Token":          (r"eyJ[0-9a-zA-Z_-]+\.[0-9a-zA-Z_-]+\.[0-9a-zA-Z_-]+", 3.0),
    "Bearer Token":       (r"[Bb]earer\s+[0-9a-zA-Z\-_.~+/]+=*", 2.5),
    "Basic Auth":         (r"Basic\s+[0-9a-zA-Z+/]+=*", 2.5),
    "Private Key":        (r"-----BEGIN (RSA|EC|PGP|DSA) PRIVATE KEY", 0),
    "Zendesk Token":      (r"(?i)zendesk.{0,10}['\"][0-9a-zA-Z_\-]{20,}['\"]", 2.5),
    "Generic API Key":    (r"(?i)(api_key|apikey|access_key|auth_token)\s*[:=]\s*['\"][^'\"]{16,}['\"]", 3.0),
    "Generic Password":   (r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{8,}['\"]", 2.5),
    "Database URL":       (r"(?i)(mysql|postgres|mongodb|redis)://[^'\"\s<>]+", 2.0),
    "S3 Bucket":          (r"s3://[a-zA-Z0-9\-_.]+|s3\.amazonaws\.com/[a-zA-Z0-9\-_.]+", 2.0),
    "Internal IP":        (r"\b(?:192\.168|10\.\d+|172\.(?:1[6-9]|2\d|3[01]))\.\d+\.\d+\b", 1.5),
    "IDOR ID":            (r"(?i)/(?:ticket|user|account|order|booking|invoice)/(\d{4,})", 1.0),
}

found = []
for name, (pattern, min_entropy) in PATTERNS.items():
    for m in re.finditer(pattern, content):
        val = m.group(0)
        e = entropy(val)
        if e >= min_entropy or name in ["Private Key", "IDOR ID", "S3 Bucket", "Database URL"]:
            found.append(f"  [{name}] (entropy={e:.1f}): {val[:100]}")

if found:
    with open(out_file, 'a') as f:
        f.write(f"\n=== Secrets in {source} ===\n")
        for item in found:
            f.write(item + "\n")
            print(item)
else:
    print(f"  No secrets in {source}")
PYEOF
}

scan_url() {
    local url="$1" label="$2" out="$3"
    echo "  Scanning: $url"
    curl -sk -A "$UA" --max-time 20 -L "$url" 2>/dev/null > /tmp/scan_content.txt
    size=$(wc -c < /tmp/scan_content.txt)
    [ "$size" -eq 0 ] && warn "  No content from $url" && return
    scan_for_secrets "" "$label ($url)" "$out"
}

banner "9.1 Secret Scan — HTML pages"
for pair in "flynas:$TARGET1" "chi_gov:$TARGET2"; do
    name="${pair%%:*}"; url="${pair#*:}"
    out="$OUT/$name/secrets.txt"
    echo "Secret Scan Results" > "$out"
    scan_url "$url" "main_page" "$out"
done

banner "9.2 Secret Scan — JavaScript files"
for pair in "flynas:$TARGET1" "chi_gov:$TARGET2"; do
    name="${pair%%:*}"; url="${pair#*:}"
    out="$OUT/$name/secrets.txt"
    js_file="$OUT/$name/js_files.txt"
    [ ! -f "$js_file" ] && warn "  No JS file list for $name (run phase 7 first)" && continue

    while IFS= read -r js_url; do
        [ -z "$js_url" ] && continue
        [[ "$js_url" != http* ]] && js_url="${url%/}/$js_url"
        scan_url "$js_url" "$(basename $js_url)" "$out"
    done < "$js_file"
done

banner "9.3 Secret Scan — Sensitive paths"
for pair in "flynas:$TARGET1" "chi_gov:$TARGET2"; do
    name="${pair%%:*}"; url="${pair#*:}"
    out="$OUT/$name/secrets.txt"
    for path in "/.env" "/config.json" "/api/config" "/.git/config" "/composer.json" "/package.json"; do
        status=$(curl -sk -o /tmp/scan_content.txt -w "%{http_code}" \
            -A "$UA" --max-time 10 "${url%/}${path}" 2>/dev/null)
        if [ "$status" = "200" ]; then
            high "  PATH EXPOSED: $path (HTTP 200)" | tee -a "$out"
            scan_for_secrets "" "$path" "$out"
        fi
    done
done

rm -f /tmp/scan_content.txt
ok "Phase 9 complete — review $OUT/*/secrets.txt"

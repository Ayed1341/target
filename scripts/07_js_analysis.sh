#!/usr/bin/env bash
# ============================================================
# PHASE 7 — JavaScript Intelligence Extraction
# Endpoints, secrets, sourcemaps, webpack chunks
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

extract_js_files() {
    local url="$1" out_dir="$2"
    echo "  Extracting JS files from $url..."
    curl -sk -A "$UA" --max-time 15 -L "$url" 2>/dev/null | \
        grep -oE 'src="[^"]+\.js[^"]*"' | \
        sed 's/src="//;s/"//' | \
        sort -u | head -50 > "$out_dir/js_files.txt"
    count=$(wc -l < "$out_dir/js_files.txt")
    ok "  Found $count JS files"
    cat "$out_dir/js_files.txt"
}

analyze_js_content() {
    local js_url="$1" out="$2"
    content=$(curl -sk -A "$UA" --max-time 15 "$js_url" 2>/dev/null)
    [ -z "$content" ] && return

    # Extract API endpoints
    echo "$content" | grep -oE '(\/api\/|\/v[0-9]+\/|\/rest\/)[^"'"'"' <>{}\[\]]+' | \
        sort -u >> "$out/api_endpoints.txt" 2>/dev/null || true

    # Extract fetch/axios calls
    echo "$content" | grep -oE "(fetch|axios\.(get|post|put|delete))\(['\"][^'\"]+['\"]" | \
        grep -oE "['\"][^'\"]+['\"]$" | tr -d "'\""  >> "$out/api_endpoints.txt" 2>/dev/null || true

    # Secret detection patterns
    python3 << PYEOF 2>/dev/null
import re, sys, math
from collections import Counter

content = """$(echo "$content" | head -2000 | sed 's/\\/\\\\/g; s/"""/'"'"''"'"''"'"'/g')"""

patterns = {
    "AWS Key":        r"AKIA[0-9A-Z]{16}",
    "Google API":     r"AIza[0-9A-Za-z\-_]{35}",
    "JWT Token":      r"eyJ[0-9a-zA-Z_-]+\.[0-9a-zA-Z_-]+\.[0-9a-zA-Z_-]+",
    "Bearer Token":   r"[Bb]earer\s+[0-9a-zA-Z\-_.~+/]+=*",
    "API Key generic":r"(?i)(api_key|apikey|access_key|auth_token)\s*[:=]\s*['\"][^'\"]{16,}['\"]",
    "Password":       r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
    "Private Key":    r"-----BEGIN (RSA|EC|PGP) PRIVATE KEY",
    "DB URL":         r"(?i)(mysql|postgres|mongodb|redis)://[^\s'\"<]+",
    "S3 Bucket":      r"s3\.amazonaws\.com/[a-zA-Z0-9\-_.]+",
    "Internal IP":    r"\b(192\.168|10\.\d+|172\.1[6-9]|172\.2\d|172\.3[01])\.\d+\.\d+\b",
}

def entropy(s):
    if not s: return 0
    c = Counter(s)
    return -sum((v/len(s))*math.log2(v/len(s)) for v in c.values())

found = False
for name, pat in patterns.items():
    for m in re.finditer(pat, content):
        val = m.group(0)
        if entropy(val) > 2.5 or name in ["JWT Token","Private Key","AWS Key"]:
            print(f"  SECRET [{name}]: {val[:80]}")
            found = True
if not found:
    print("  No secrets detected in this file")
PYEOF

    # Check for sourcemap
    if curl -sk --head -A "$UA" --max-time 10 "${js_url}.map" 2>/dev/null | grep -q "200"; then
        high "  SOURCEMAP EXPOSED: ${js_url}.map"
        echo "${js_url}.map" >> "$out/exposed_sourcemaps.txt"
    fi
}

banner "7.1 JS File Discovery"
for pair in "flynas:$TARGET1" "chi_gov:$TARGET2"; do
    name="${pair%%:*}"; url="${pair#*:}"
    banner "JS Discovery — $url"
    extract_js_files "$url" "$OUT/$name"
done

banner "7.2 JS Content Analysis"
for pair in "flynas:$TARGET1" "chi_gov:$TARGET2"; do
    name="${pair%%:*}"; url="${pair#*:}"
    banner "Analyzing JS files for $name"
    > "$OUT/$name/api_endpoints.txt"
    > "$OUT/$name/exposed_sourcemaps.txt"
    while IFS= read -r js_file; do
        [ -z "$js_file" ] && continue
        # Make absolute URL if needed
        if [[ "$js_file" != http* ]]; then
            js_file="${url%/}/$js_file"
        fi
        echo "  Analyzing: $js_file"
        analyze_js_content "$js_file" "$OUT/$name"
    done < "$OUT/$name/js_files.txt"

    sort -u -o "$OUT/$name/api_endpoints.txt" "$OUT/$name/api_endpoints.txt"
    count=$(wc -l < "$OUT/$name/api_endpoints.txt")
    ok "  Found $count unique API endpoints for $name"
done

ok "Phase 7 complete"

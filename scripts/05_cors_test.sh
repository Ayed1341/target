#!/usr/bin/env bash
# ============================================================
# PHASE 5 — CORS Misconfiguration Testing
# 6 bypass patterns per target
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

test_cors() {
    local url="$1" origin="$2" label="$3" out="$4"
    response=$(curl -sk -I -A "$UA" \
        -H "Origin: $origin" \
        -H "Access-Control-Request-Method: GET" \
        --max-time 15 "$url" 2>/dev/null)

    acao=$(echo "$response" | grep -i "^access-control-allow-origin:" | head -1 | tr -d '\r')
    acac=$(echo "$response" | grep -i "^access-control-allow-credentials:" | head -1 | tr -d '\r')
    status=$(echo "$response" | grep "^HTTP" | head -1)

    if [ -n "$acao" ]; then
        if echo "$acao" | grep -qi "$origin\|^\*$"; then
            high "  CORS VULNERABLE [$label]:" | tee -a "$out"
            high "    Origin sent: $origin" | tee -a "$out"
            high "    ACAO: $acao" | tee -a "$out"
            high "    ACAC: $acac" | tee -a "$out"
            high "    PoC: curl -H 'Origin: $origin' -I '$url'" | tee -a "$out"
        else
            warn "  [$label] ACAO present but not reflected: $acao" | tee -a "$out"
        fi
    else
        ok "  [$label] No CORS reflection for '$origin'" | tee -a "$out"
    fi
}

cors_test_target() {
    local url="$1" name="$2" host="$3" apex="$4"
    local out="$OUT/$name/cors_test.txt"
    echo "CORS Test Results — $url" > "$out"
    echo "Date: $(date)" >> "$out"
    echo "" >> "$out"

    banner "CORS Tests for $url"

    # Pattern 1: Reflected origin
    test_cors "$url" "https://$host" "REFLECTED_ORIGIN" "$out"

    # Pattern 2: Null origin
    test_cors "$url" "null" "NULL_ORIGIN" "$out"

    # Pattern 3: Attacker prefix (evil.target.com)
    test_cors "$url" "https://evil.$apex" "EVIL_SUBDOMAIN_PREFIX" "$out"

    # Pattern 4: Attacker suffix (target.com.evil.com)
    test_cors "$url" "https://$apex.evil.com" "APEX_SUFFIX" "$out"

    # Pattern 5: HTTP protocol downgrade
    test_cors "$url" "http://$host" "HTTP_PROTO_DOWNGRADE" "$out"

    # Pattern 6: Arbitrary subdomain
    test_cors "$url" "https://attacker.$apex" "ARBITRARY_SUBDOMAIN" "$out"
}

banner "5.1 CORS Testing — help.flynas.com"
cors_test_target "$TARGET1" "flynas" "help.flynas.com" "flynas.com"

banner "5.2 CORS Testing — greeting.chi.gov.sa"
cors_test_target "$TARGET2" "chi_gov" "greeting.chi.gov.sa" "chi.gov.sa"

ok "Phase 5 complete — review $OUT/*/cors_test.txt"

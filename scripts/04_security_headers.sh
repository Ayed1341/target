#!/usr/bin/env bash
# ============================================================
# PHASE 4 — Security Headers Audit + CSP Analysis
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

audit_headers() {
    local url="$1" out="$2"
    echo "  Auditing: $url" | tee -a "$out"
    headers=$(curl -sk -I -A "$UA" --max-time 15 "$url" 2>/dev/null)
    score=0; max=100

    declare -A CHECKS=(
        ["strict-transport-security"]="20"
        ["content-security-policy"]="20"
        ["x-content-type-options"]="10"
        ["x-frame-options"]="10"
        ["referrer-policy"]="5"
        ["permissions-policy"]="5"
        ["x-xss-protection"]="5"
        ["cache-control"]="5"
        ["cross-origin-opener-policy"]="10"
        ["cross-origin-resource-policy"]="10"
    )

    for header in "${!CHECKS[@]}"; do
        weight="${CHECKS[$header]}"
        val=$(echo "$headers" | grep -i "^$header:" | head -1 | cut -d' ' -f2-)
        if [ -n "$val" ]; then
            score=$((score + weight))
            ok "  [PRESENT] $header: ${val:0:60}" | tee -a "$out"
        else
            warn "  [MISSING] $header (weight: -$weight pts)" | tee -a "$out"
        fi
    done

    echo "  Header Security Score: $score/$max" | tee -a "$out"
    [ "$score" -lt 40 ] && high "  LOW SCORE ($score/100) — multiple headers missing!" | tee -a "$out"
    echo "" | tee -a "$out"
}

analyze_csp() {
    local url="$1" out="$2"
    echo "  Analyzing CSP for $url..."
    csp=$(curl -sk -I -A "$UA" --max-time 15 "$url" 2>/dev/null | \
          grep -i "^content-security-policy:" | head -1 | cut -d' ' -f2-)

    if [ -z "$csp" ]; then
        high "  No CSP header — XSS fully unmitigated" | tee -a "$out"
        return
    fi
    echo "  CSP: $csp" | tee -a "$out"

    # Check weaknesses
    for weakness in "unsafe-inline" "unsafe-eval" "data:" "http:" "*"; do
        if echo "$csp" | grep -qi "$weakness"; then
            high "  CSP WEAKNESS: '$weakness' found" | tee -a "$out"
        fi
    done

    # Check missing directives
    for directive in "default-src" "script-src" "object-src" "base-uri"; do
        if ! echo "$csp" | grep -qi "$directive"; then
            warn "  CSP: missing '$directive'" | tee -a "$out"
        fi
    done
}

check_info_disclosure() {
    local url="$1" out="$2"
    echo "  Checking information disclosure headers..."
    headers=$(curl -sk -I -A "$UA" --max-time 15 "$url" 2>/dev/null)
    for h in "server" "x-powered-by" "x-aspnet-version" "x-generator" "x-debug"; do
        val=$(echo "$headers" | grep -i "^$h:" | head -1)
        [ -n "$val" ] && high "  INFO LEAK: $val" | tee -a "$out"
    done
}

banner "4.1 Security Header Audit"
for pair in "flynas:$TARGET1" "chi_gov:$TARGET2"; do
    name="${pair%%:*}"; url="${pair#*:}"
    banner "Header Audit — $url"
    audit_headers "$url" "$OUT/$name/security_headers.txt"
done

banner "4.2 CSP Analysis"
for pair in "flynas:$TARGET1" "chi_gov:$TARGET2"; do
    name="${pair%%:*}"; url="${pair#*:}"
    banner "CSP — $url"
    analyze_csp "$url" "$OUT/$name/csp_analysis.txt"
done

banner "4.3 Information Disclosure Check"
for pair in "flynas:$TARGET1" "chi_gov:$TARGET2"; do
    name="${pair%%:*}"; url="${pair#*:}"
    check_info_disclosure "$url" "$OUT/$name/security_headers.txt"
done

ok "Phase 4 complete → results in $OUT/"

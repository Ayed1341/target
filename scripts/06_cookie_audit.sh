#!/usr/bin/env bash
# ============================================================
# PHASE 6 — Cookie Security Audit
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

audit_cookies() {
    local url="$1" out="$2"
    echo "Cookie Audit — $url" | tee -a "$out"
    echo "─────────────────────────────────────" | tee -a "$out"

    # Collect all Set-Cookie headers
    cookies=$(curl -sk -c /dev/null -D - -A "$UA" --max-time 15 -L "$url" 2>/dev/null | \
              grep -i "^Set-Cookie:" || true)

    if [ -z "$cookies" ]; then
        warn "  No cookies set by $url"
        echo "  No cookies found" >> "$out"
        return
    fi

    echo "$cookies" | while IFS= read -r cookie_line; do
        name=$(echo "$cookie_line" | sed 's/Set-Cookie: //i' | cut -d'=' -f1 | tr -d ' ')
        echo "" | tee -a "$out"
        ok "  Cookie: $name" | tee -a "$out"
        echo "  Raw: $cookie_line" >> "$out"

        # Check Secure flag
        if echo "$cookie_line" | grep -qi "Secure"; then
            ok "    [PASS] Secure flag present" | tee -a "$out"
        else
            high "    [FAIL] Missing Secure flag — cookie transmittable over HTTP" | tee -a "$out"
        fi

        # Check HttpOnly flag
        if echo "$cookie_line" | grep -qi "HttpOnly"; then
            ok "    [PASS] HttpOnly flag present" | tee -a "$out"
        else
            high "    [FAIL] Missing HttpOnly flag — accessible via JavaScript (XSS)" | tee -a "$out"
        fi

        # Check SameSite attribute
        if echo "$cookie_line" | grep -qi "SameSite=Strict"; then
            ok "    [PASS] SameSite=Strict" | tee -a "$out"
        elif echo "$cookie_line" | grep -qi "SameSite=Lax"; then
            warn "    [WEAK] SameSite=Lax (consider Strict)" | tee -a "$out"
        elif echo "$cookie_line" | grep -qi "SameSite=None"; then
            high "    [WARN] SameSite=None — cross-site requests allowed (check Secure)" | tee -a "$out"
        else
            high "    [FAIL] Missing SameSite — CSRF risk" | tee -a "$out"
        fi

        # Check cookie name prefix
        if echo "$name" | grep -q "^__Host-"; then
            ok "    [PASS] __Host- prefix (strongest)" | tee -a "$out"
        elif echo "$name" | grep -q "^__Secure-"; then
            ok "    [PASS] __Secure- prefix" | tee -a "$out"
        else
            warn "    [INFO] No secure prefix (__Host- or __Secure-)" | tee -a "$out"
        fi

        # Check Max-Age / Expires
        if echo "$cookie_line" | grep -qi "Max-Age\|Expires"; then
            ok "    [INFO] Persistent cookie (has expiry)" | tee -a "$out"
        else
            ok "    [INFO] Session cookie (no persistent expiry)" | tee -a "$out"
        fi
    done
    echo "" | tee -a "$out"
}

banner "6.1 Cookie Audit — help.flynas.com"
audit_cookies "$TARGET1" "$OUT/flynas/cookie_audit.txt"

banner "6.2 Cookie Audit — greeting.chi.gov.sa"
audit_cookies "$TARGET2" "$OUT/chi_gov/cookie_audit.txt"

ok "Phase 6 complete"

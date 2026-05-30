#!/usr/bin/env bash
# ============================================================
# PHASE 3 — WAF Detection + Technology Fingerprinting
# Run from Saudi IP / KSA VPN
# ============================================================
set -euo pipefail

TARGET1="https://help.flynas.com"
TARGET2="https://greeting.chi.gov.sa"
OUT="./results"
mkdir -p "$OUT/flynas" "$OUT/chi_gov"

UA_BROWSER="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
UA_BOT="Googlebot/2.1 (+http://www.google.com/bot.html)"

GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
banner() { echo -e "\n${CYAN}[*] $1${NC}"; }
ok()     { echo -e "${GREEN}[+] $1${NC}"; }
warn()   { echo -e "${YELLOW}[!] $1${NC}"; }
high()   { echo -e "${RED}[!!] $1${NC}"; }

waf_check() {
    local url="$1" out="$2"
    echo "  Checking WAF on $url..."
    headers=$(curl -sk -I -A "$UA_BROWSER" --max-time 15 "$url" 2>/dev/null)

    # Server header
    server=$(echo "$headers" | grep -i "^server:" | head -1)
    echo "  Server: $server" | tee -a "$out"

    # WAF indicators
    for indicator in cf-ray x-iinfo x-sucuri-id x-cache x-amz-cf-id \
                     x-varnish x-akamai x-cdn x-waf x-firewall \
                     x-datadome-cid x-reblaze; do
        val=$(echo "$headers" | grep -i "^$indicator:" | head -1)
        [ -n "$val" ] && echo "  WAF-Header: $val" | tee -a "$out"
    done

    # Status code
    status=$(echo "$headers" | grep "^HTTP" | head -1)
    echo "  Status: $status" | tee -a "$out"
    echo "" | tee -a "$out"
}

tech_detect() {
    local url="$1" out="$2"
    echo "  Detecting technologies on $url..."
    body=$(curl -sk -A "$UA_BROWSER" \
           -H "Accept: text/html,application/xhtml+xml,*/*" \
           -H "Accept-Language: ar,en-US;q=0.7,en;q=0.3" \
           --max-time 15 -L "$url" 2>/dev/null)
    headers=$(curl -sk -I -A "$UA_BROWSER" --max-time 15 "$url" 2>/dev/null)

    # Header-based detection
    echo "$headers" | grep -iE "x-powered-by|x-aspnet|x-generator|x-drupal|x-wordpress" | \
        while read line; do echo "  Tech-Header: $line" | tee -a "$out"; done

    # Body-based detection
    declare -A SIGS=(
        ["React"]="__reactFiber|data-reactroot|react\.development"
        ["Vue.js"]="__vue__|v-bind:|vue\.runtime"
        ["Angular"]="ng-version|_nghost|angular\.min"
        ["Next.js"]="__NEXT_DATA__|/_next/static"
        ["Nuxt.js"]="__nuxt|_nuxt/"
        ["WordPress"]="wp-content|wp-includes|wp-json"
        ["Drupal"]="Drupal\.settings|drupal\.js"
        ["Joomla"]="joomla|option=com_"
        ["SharePoint"]="_layouts/|_vti_bin"
        ["jQuery"]="jquery\.min\.js|jQuery\.fn"
        ["Bootstrap"]="bootstrap\.min\.css"
        ["PHP"]="\.php\b|PHPSESSID"
        ["ASP.NET"]="__VIEWSTATE|asp\.net|aspx"
        ["Zendesk"]="zendesk\.com|zdassets\.com|zopim"
        ["Freshdesk"]="freshdesk\.com|freshwidget"
        ["Salesforce"]="salesforce\.com|force\.com"
        ["Google Analytics"]="google-analytics\.com|gtag\("
        ["CloudFront"]="cloudfront\.net|x-amz-cf"
    )

    for tech in "${!SIGS[@]}"; do
        if echo "$body$headers" | grep -qiE "${SIGS[$tech]}"; then
            ok "Technology detected: $tech" | tee -a "$out"
        fi
    done
}

js_links() {
    local url="$1" out="$2"
    echo "  Extracting JS files from $url..."
    curl -sk -A "$UA_BROWSER" --max-time 15 -L "$url" 2>/dev/null | \
        grep -oE 'src="[^"]+\.js[^"]*"' | sed 's/src="//;s/"//' | \
        sort -u | head -30 | tee "$out/js_files.txt"
}

# ── Run for both targets ──────────────────────────────────────
banner "3.1 WAF Detection"
for pair in "flynas:$TARGET1" "chi_gov:$TARGET2"; do
    name="${pair%%:*}"; url="${pair#*:}"
    banner "WAF Check — $url"
    waf_check "$url" "$OUT/$name/waf_detect.txt"
done

banner "3.2 Technology Fingerprinting"
for pair in "flynas:$TARGET1" "chi_gov:$TARGET2"; do
    name="${pair%%:*}"; url="${pair#*:}"
    banner "Tech Detect — $url"
    tech_detect "$url" "$OUT/$name/tech_stack.txt"
done

banner "3.3 JavaScript File Discovery"
for pair in "flynas:$TARGET1" "chi_gov:$TARGET2"; do
    name="${pair%%:*}"; url="${pair#*:}"
    banner "JS Files — $url"
    js_links "$url" "$OUT/$name"
done

# ── 3.4 Googlebot UA test (WAF bypass check) ─────────────────
banner "3.4 Googlebot UA Test (WAF Bypass Check)"
for url in "$TARGET1" "$TARGET2"; do
    echo "  Testing $url with Googlebot UA..."
    code=$(curl -sk -o /dev/null -w "%{http_code}" -A "$UA_BOT" "$url" 2>/dev/null)
    echo "  Status: $code"
    if [ "$code" = "200" ]; then
        warn "WAF bypass possible with Googlebot UA — site responds 200!"
    fi
done

ok "Phase 3 complete → results in $OUT/"

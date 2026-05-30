#!/usr/bin/env bash
# ============================================================
# PHASE 8 — API Endpoint Discovery + GraphQL Probing
# ============================================================
set -euo pipefail

TARGET1="https://help.flynas.com"
TARGET2="https://greeting.chi.gov.sa"
OUT="./results"
WL="./wordlists/api_paths.txt"

UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
banner() { echo -e "\n${CYAN}[*] $1${NC}"; }
ok()     { echo -e "${GREEN}[+] $1${NC}"; }
warn()   { echo -e "${YELLOW}[!] $1${NC}"; }
high()   { echo -e "${RED}[!!] $1${NC}"; }

probe_api_path() {
    local base="$1" path="$2" out="$3"
    url="${base%/}${path}"
    response=$(curl -sk -A "$UA" \
        -H "Accept: application/json,*/*" \
        -o /tmp/api_resp.txt \
        -w "%{http_code} %{size_download}" \
        --max-time 10 "$url" 2>/dev/null)
    code=$(echo "$response" | cut -d' ' -f1)
    size=$(echo "$response" | cut -d' ' -f2)

    case "$code" in
        200|201)
            high "  [200] $path ($size bytes)" | tee -a "$out"
            # Check if JSON response
            if cat /tmp/api_resp.txt 2>/dev/null | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
                ok "    → Valid JSON response"
            fi
            ;;
        400|401|405)
            warn "  [$code] $path — endpoint exists (auth required / bad method)" | tee -a "$out"
            ;;
        403)
            warn "  [403] $path — forbidden (endpoint exists)" | tee -a "$out"
            ;;
        301|302|307)
            location=$(curl -sk -I -A "$UA" --max-time 10 "$url" 2>/dev/null | grep -i "^Location:" | head -1)
            warn "  [$code] $path → $location" | tee -a "$out"
            ;;
    esac
}

probe_graphql() {
    local url="$1" out="$2"
    echo "  Testing GraphQL introspection at $url..."
    result=$(curl -sk -A "$UA" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json" \
        -d '{"query":"{__schema{types{name fields{name type{name kind}}}}}"}' \
        --max-time 15 "$url" 2>/dev/null)

    if echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('__schema',{}).get('types',[]))" 2>/dev/null | grep -q "\["; then
        high "  GRAPHQL INTROSPECTION ENABLED: $url" | tee -a "$out"
        echo "$result" | python3 -c "
import sys, json
d = json.load(sys.stdin)
types = d.get('data',{}).get('__schema',{}).get('types',[])
user_types = [t['name'] for t in types if not t['name'].startswith('__')]
print(f'  Types ({len(user_types)}): {user_types[:15]}')
" 2>/dev/null | tee -a "$out"
    else
        ok "  No introspection response from $url"
    fi
}

banner "8.1 API Path Probing"
for pair in "flynas:$TARGET1" "chi_gov:$TARGET2"; do
    name="${pair%%:*}"; url="${pair#*:}"
    out="$OUT/$name/api_discovery.txt"
    banner "API Discovery — $url"
    > "$out"

    # Common API paths
    api_paths=(
        "/api" "/api/v1" "/api/v2" "/api/v3"
        "/rest" "/rest/v1"
        "/v1" "/v2" "/v3"
        "/api/users" "/api/user" "/api/me" "/api/profile"
        "/api/auth" "/api/login" "/api/token"
        "/api/tickets" "/api/orders" "/api/bookings"
        "/api/search" "/api/config" "/api/admin"
        "/api/health" "/api/status" "/api/ping"
        "/.well-known/openid-configuration"
        "/swagger.json" "/openapi.json" "/api-docs"
        "/swagger-ui" "/api/swagger.json"
        "/actuator" "/actuator/health" "/actuator/env"
    )

    # If wordlist exists, use it
    if [ -f "$WL" ]; then
        while IFS= read -r path; do
            [ -z "$path" ] && continue
            probe_api_path "$url" "$path" "$out"
        done < "$WL"
    else
        for path in "${api_paths[@]}"; do
            probe_api_path "$url" "$path" "$out"
        done
    fi
done

banner "8.2 GraphQL Probing"
for pair in "flynas:$TARGET1" "chi_gov:$TARGET2"; do
    name="${pair%%:*}"; url="${pair#*:}"
    out="$OUT/$name/api_discovery.txt"
    for gql_path in "/graphql" "/graphiql" "/api/graphql" "/v1/graphql" "/query" "/gql"; do
        probe_graphql "${url%/}${gql_path}" "$out"
    done
done

ok "Phase 8 complete"

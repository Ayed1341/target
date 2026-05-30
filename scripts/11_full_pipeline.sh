#!/usr/bin/env bash
# ============================================================
# PHASE 11 — Full Pipeline Master Script
# Runs all phases in sequence and generates final report
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
OUT="$BASE_DIR/results"
REPORT_OUT="$OUT/final_reports"
LOG="$OUT/pipeline_$(date +%Y%m%d_%H%M%S).log"

GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'; BOLD='\033[1m'
banner() { echo -e "\n${CYAN}${BOLD}[*] $1${NC}" | tee -a "$LOG"; }
ok()     { echo -e "${GREEN}[+] $1${NC}" | tee -a "$LOG"; }
warn()   { echo -e "${YELLOW}[!] $1${NC}" | tee -a "$LOG"; }
sep()    { echo -e "${CYAN}$(printf '═%.0s' {1..60})${NC}" | tee -a "$LOG"; }

mkdir -p "$OUT/flynas" "$OUT/chi_gov" "$OUT/osint" "$REPORT_OUT"

sep
echo -e "${BOLD}${CYAN}  RED TEAM FULL PIPELINE — v3.0${NC}" | tee -a "$LOG"
echo -e "${BOLD}  Targets: help.flynas.com | greeting.chi.gov.sa${NC}" | tee -a "$LOG"
echo -e "${BOLD}  Output: $OUT${NC}" | tee -a "$LOG"
echo -e "${BOLD}  Log: $LOG${NC}" | tee -a "$LOG"
sep

START_TIME=$(date +%s)

run_phase() {
    local num="$1" script="$2" desc="$3"
    banner "PHASE $num — $desc"
    if [ -f "$SCRIPT_DIR/$script" ]; then
        bash "$SCRIPT_DIR/$script" 2>&1 | tee -a "$LOG" || warn "Phase $num had errors — continuing"
    else
        warn "Script not found: $script"
    fi
    echo "" | tee -a "$LOG"
}

# Check for Saudi IP (required for active phases)
banner "0. Preflight Check"
country=$(curl -s --max-time 5 "https://ipapi.co/country/" 2>/dev/null || echo "UNKNOWN")
ip=$(curl -s --max-time 5 "https://ipapi.co/ip/" 2>/dev/null || echo "unknown")
echo "  Egress IP: $ip | Country: $country" | tee -a "$LOG"
if [ "$country" != "SA" ]; then
    warn "Not connected from Saudi IP (current: $country)"
    warn "Some target-specific content may be geo-blocked"
    warn "Recommended: Connect via KSA VPN before running active phases"
    read -p "  Continue anyway? [y/N] " -n 1 -r
    echo
    [[ ! $REPLY =~ ^[Yy]$ ]] && echo "Aborted." && exit 1
fi

# Phase execution
run_phase 1 "01_passive_osint.sh" "Passive OSINT"
run_phase 2 "02_subdomain_enum.sh" "Subdomain Enumeration"
run_phase 3 "03_tech_fingerprint.sh" "WAF + Tech Fingerprinting"
run_phase 4 "04_security_headers.sh" "Security Headers + CSP"
run_phase 5 "05_cors_test.sh" "CORS Misconfiguration"
run_phase 6 "06_cookie_audit.sh" "Cookie Security"
run_phase 7 "07_js_analysis.sh" "JavaScript Analysis"
run_phase 8 "08_api_discovery.sh" "API + GraphQL Discovery"
run_phase 9 "09_secret_scan.sh" "Secret Scanning"
run_phase 10 "10_vuln_poc.sh" "Vulnerability PoC"

# Run Python mega framework
banner "PHASE 11 — Advanced Python Framework (redteam.py)"
if [ -f "$BASE_DIR/redteam.py" ]; then
    python3 "$BASE_DIR/redteam.py" \
        --target "https://help.flynas.com" \
        --target "https://greeting.chi.gov.sa" \
        --output "$REPORT_OUT" \
        --workers 10 \
        --rate 2.0 \
        --depth 3 \
        2>&1 | tee -a "$LOG" || warn "redteam.py had errors"
else
    warn "redteam.py not found at $BASE_DIR"
fi

# Final summary
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINS=$((ELAPSED / 60))
SECS=$((ELAPSED % 60))

sep
banner "PIPELINE COMPLETE"
ok "Total time: ${MINS}m ${SECS}s"
ok "Results directory: $OUT"
ok "Final reports: $REPORT_OUT"
echo "" | tee -a "$LOG"

# Count findings
echo "  Findings summary:" | tee -a "$LOG"
for name in flynas chi_gov; do
    echo "  [$name]:" | tee -a "$LOG"
    for f in "$OUT/$name"/*.txt; do
        [ -f "$f" ] || continue
        count=$(wc -l < "$f")
        echo "    $(basename $f): $count lines" | tee -a "$LOG"
    done
done

# List reports
echo "" | tee -a "$LOG"
echo "  Generated reports:" | tee -a "$LOG"
ls "$REPORT_OUT"/ 2>/dev/null | while read f; do
    echo "    $REPORT_OUT/$f" | tee -a "$LOG"
done

sep
ok "Open HTML report:"
echo "  open $REPORT_OUT/redteam_report_*.html"
sep

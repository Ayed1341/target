#!/usr/bin/env bash
# ============================================================
# Advanced Bug Bounty Recon – Full Automated Run
# Targets: help.flynas.com  |  greeting.chi.gov.sa
#
# RUN FROM YOUR OWN DEVICE (Termux / Linux / macOS)
# with a Saudi IP or KSA VPN connection
# ============================================================
set -e

OUTPUT_BASE="./ADVANCED_OUTPUT"

echo "[*] Installing Python dependencies..."
pip install aiohttp requests rich 2>/dev/null || true

echo ""
echo "==========================================================="
echo "  TARGET 1: help.flynas.com (Microsoft Azure, Cloudflare)"
echo "==========================================================="
python advanced_recon.py \
  --target "https://help.flynas.com/" \
  --output "$OUTPUT_BASE/flynas" \
  --workers 6 \
  --rate 2.0 \
  --depth 3 \
  --timeout 25 \
  --scope "flynas.com" "*.flynas.com"

echo ""
echo "==========================================================="
echo "  TARGET 2: greeting.chi.gov.sa (Saudi Gov Network)"
echo "==========================================================="
python advanced_recon.py \
  --target "https://greeting.chi.gov.sa/" \
  --output "$OUTPUT_BASE/chi_gov" \
  --workers 5 \
  --rate 1.5 \
  --depth 3 \
  --timeout 25 \
  --scope "chi.gov.sa" "*.chi.gov.sa"

echo ""
echo "==========================================================="
echo "  Reports saved to $OUTPUT_BASE/"
echo "  Open the .html files in a browser for full interactive report"
echo "==========================================================="
ls -lh "$OUTPUT_BASE"/flynas/ "$OUTPUT_BASE"/chi_gov/ 2>/dev/null

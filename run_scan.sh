#!/usr/bin/env bash
# ============================================================
# TITAN_HUNTER – Auto-run script for greeting.chi.gov.sa
# Run this on YOUR own device (Termux/Linux/macOS)
# ============================================================
set -e

TARGET="https://greeting.chi.gov.sa/"
OUTPUT_DIR="./TITAN_OUTPUT"

echo "[*] Installing dependencies..."
pip install aiohttp requests rich 2>/dev/null || pip3 install aiohttp requests rich 2>/dev/null

echo "[*] Starting TITAN_HUNTER full scan against $TARGET"
python titan_hunter.py \
  --target "$TARGET" \
  --scan \
  --report \
  --workers 5 \
  --rate 2.0 \
  --depth 3 \
  --timeout 20 \
  --ua chrome \
  --output "$OUTPUT_DIR"

echo ""
echo "[+] Reports saved to $OUTPUT_DIR/reports/"
echo "[+] Done. Review the JSON and Markdown reports."

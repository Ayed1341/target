#!/data/data/com.termux/files/usr/bin/bash
# AYED NETWORK MASTER PRO — one-command Termux setup & launcher.
# Installs Python + the real huawei-lte-api (so SCRAM+RSA login, 5G/band
# WRITES and full Autopilot all work), downloads the latest engine, runs it.
#
# Usage in Termux:
#   curl -L -o run_termux.sh https://raw.githubusercontent.com/Ayed1341/target/claude/upgrade-v40-s4y1i/run_termux.sh
#   bash run_termux.sh
set -e

BRANCH="claude/upgrade-v40-s4y1i"
RAW="https://raw.githubusercontent.com/Ayed1341/target/${BRANCH}/zain_h155_manager.py"

echo "== AYED NETWORK MASTER PRO — Termux setup =="

# 1) Python
if ! command -v python >/dev/null 2>&1; then
  echo "[*] Installing Python..."
  pkg update -y && pkg install -y python
fi

# 2) Python deps — huawei-lte-api pulls pycryptodomex (compiles in Termux),
#    which is what enables the encrypted writes this firmware requires.
echo "[*] Installing Python packages (huawei-lte-api, requests)..."
pip install --upgrade pip >/dev/null 2>&1 || true
pip install huawei-lte-api requests

# 3) Get the latest tool
echo "[*] Downloading the manager..."
curl -fL -o h155.py "$RAW"

echo
echo "== Ready =="
echo "Connect this phone to the ROUTER's Wi-Fi, then it will start."
echo "Tip: full menu = 'python h155.py --help' ; autopilot = 'python h155.py autopilot'"
echo
python h155.py "$@"

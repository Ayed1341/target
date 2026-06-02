# Run on your phone with Termux (guaranteed login — real huawei-lte-api)

Your H155/H115 firmware uses **SCRAM + RSA** login, which needs the maintained
`huawei-lte-api` library (it depends on the compiled `pycryptodomex` module).
That module can't be bundled into the Kivy APK, but it installs perfectly in
**Termux**, where the full command-line tool (all 119 features + autopilot)
runs with real data.

## 1. Install Termux
Install **Termux from F-Droid** (https://f-droid.org/packages/com.termux/) —
NOT the Play Store version (it's outdated).

## 2. One-time setup — ONE command (paste into Termux)
```bash
curl -L -o run_termux.sh https://raw.githubusercontent.com/Ayed1341/target/claude/upgrade-v40-s4y1i/run_termux.sh && bash run_termux.sh
```
This installs Python + `huawei-lte-api` (which pulls `pycryptodomex`, compiled
in Termux) — so **SCRAM+RSA login, 5G/band WRITES, and full Autopilot all
work** here, unlike the APK. It then downloads and launches the tool.

<details><summary>Manual steps (if you prefer)</summary>

```bash
pkg update -y && pkg install -y python
pip install huawei-lte-api requests
curl -L -o h155.py \
  https://raw.githubusercontent.com/Ayed1341/target/claude/upgrade-v40-s4y1i/zain_h155_manager.py
```
</details>

### What works in Termux that the APK can't
- **Enable 5G (EN-DC)** and **LTE/5G band lock** (encrypted writes) — `max-ca`, `endc`, `nr-lock`, `ca-best`…
- **Full Smart Autopilot** that actually *changes* bands/CA/5G, not just monitors.
- 15 new PRO tools: `full-cell`, `enodeb`, `db-log`, `outage`, `sla`,
  `speed-cons`, `band-cap`, `handover`, `distance`, `webdash` (LAN web
  dashboard), `telegram`, `prometheus`, `max-ca`, `peak-hours`, `trend`.

## 3. Run it
Connect the phone to the **router's Wi-Fi**, then:
```bash
python h155.py
```
- It will print: `Using huawei-lte-api (auto SCRAM/firmware detection)` →
  `Authenticated via huawei-lte-api!`
- Now every read returns real data (RSRP, band, WAN, cells…), and the smart
  autopilot works.

### Useful one-liners
```bash
python h155.py status        # full dashboard
python h155.py autopilot     # smart auto-everything (Ctrl+C to stop)
python h155.py dashboard     # live all-in-one view
python h155.py ca-best       # benchmark & lock best 4G+4G aggregation
python h155.py --help        # full menu (all 119 tools)
```

## Update later
```bash
curl -L -o h155.py \
  https://raw.githubusercontent.com/Ayed1341/target/claude/upgrade-v40-s4y1i/zain_h155_manager.py
```

## Why not the APK?
The APK runs the same engine and its **speed test / monitoring work**, but the
SCRAM+RSA login needs `pycryptodomex`, which Buildozer/python-for-android can't
compile into the APK. Termux uses a full CPython where it installs normally —
so it's the reliable path for full router control.

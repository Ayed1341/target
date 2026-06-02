# Zain H155 Manager — Android App (.apk)

A touch GUI for the Zain H155 router manager. It **reuses the exact same
optimization engine** as the command-line tool (`zain_h155_manager.py`) — the
smart autopilot, best-CA, best-tower, status and speed-test logic are all the
real code, just with a phone UI on top.

## How to get the APK (GitHub Actions)

1. Go to the repo's **Actions** tab → **Build Android APK**.
2. Click **Run workflow** (branch `claude/upgrade-v40-s4y1i`), or just push a
   change under `android/`.
3. Wait ~20–40 min for the first build (it downloads the Android SDK/NDK).
4. Open the finished run → **Artifacts** → download **`h155-manager-apk`**.
5. Unzip it → you get `h155manager-…-debug.apk`.

## Install on Android 14

- Copy the `.apk` to your phone.
- Tap it → allow **"Install unknown apps"** for your file manager/browser when
  prompted → **Install**.
- It is a *debug* APK (self-signed). That is normal for sideloading; Play Store
  is not involved.

## Using it

1. Connect the phone to the **router's Wi-Fi**.
2. Open the app → enter the admin password → **Connect**.
3. Tap **Status**, **Auto-Tune**, **Best CA**, **Best Tower**, **Speed Test**,
   or start **Smart Autopilot** (runs the same 50+ tactics in the background).

## What differs from the CLI (honest notes)

- **Simplified GUI** — exposes the key actions + autopilot, not all 119 menu
  items. The underlying engine is identical and complete.
- **Latency uses TCP-connect** instead of `ping` (stock Android blocks raw
  ICMP from the app sandbox). MTU/traceroute tactics that need the `ping`
  binary simply no-op — the engine handles that gracefully.
- **Cleartext HTTP** to `192.168.8.1` is required (the router API is HTTP).
  python-for-android's manifest enables this by default; if a build can't
  reach the router, enable `android:usesCleartextTraffic="true"` in the
  generated manifest.
- **`huawei-lte-api`** is included for SCRAM login on newer firmware. If a CI
  build ever fails while fetching it, remove it from `requirements` in
  `buildozer.spec` — the engine then falls back to its built-in manual login.

## Build locally instead (optional)

On a Linux machine with Buildozer installed:

```bash
cp zain_h155_manager.py android/engine.py
cd android
buildozer android debug      # APK lands in android/bin/
```

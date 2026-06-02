[app]

# Application
title = Zain H155 Manager
package.name = h155manager
package.domain = org.routerpro

# Source — engine.py is copied in from the repo root by the CI workflow
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
source.main = main.py

version = 40.4

# Pure-python + requests stack. huawei-lte-api gives SCRAM login on newer
# H155 firmware; if a build ever fails fetching it, remove it from this list
# and the engine falls back to its built-in manual XML login.
requirements = python3,kivy==2.3.0,requests,urllib3,certifi,idna,charset-normalizer,xmltodict,huawei-lte-api

orientation = portrait
fullscreen = 0

# ── Android ──
# Cleartext HTTP to the router (192.168.8.1) is required; the python-for-android
# SDL2 manifest enables android:usesCleartextTraffic by default.
# targetSdk 34 installs and runs fine on Android 14/15/16 (S24 Ultra = arm64-v8a).
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE
android.api = 34
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a
android.allow_backup = True
android.accept_sdk_license = True

# Misc
log_level = 2

[buildozer]
log_level = 2
warn_on_root = 0

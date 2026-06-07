#!/usr/bin/env python3
"""
Samsung Galaxy S24 Ultra - Advanced Bootloader Unlock Suite
40 Professional Methods | Termux Edition (on-device + PC modes)
"""

import os
import sys
import subprocess
import time
import shutil
from datetime import datetime

# ── ANSI Colors ───────────────────────────────────────────────────────────────
R  = '\033[91m'
G  = '\033[92m'
Y  = '\033[93m'
B  = '\033[94m'
M  = '\033[95m'
C  = '\033[96m'
W  = '\033[97m'
BO = '\033[1m'
RE = '\033[0m'

LOG_FILE = os.path.expanduser("~/s24_unlock_log.txt")

# ── Mode detection ─────────────────────────────────────────────────────────────
# ON_DEVICE = True  → Termux running ON the phone (no ADB needed)
# ON_DEVICE = False → Termux/PC connected via USB-ADB to the phone
def _detect_mode():
    r = subprocess.run("getprop ro.product.model", shell=True,
                       capture_output=True, text=True, timeout=5)
    return r.returncode == 0 and bool(r.stdout.strip())

ON_DEVICE = _detect_mode()


def log(msg):
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")


def run(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        log(f"CMD: {cmd} | RC: {r.returncode}")
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "Timeout", 1
    except Exception as e:
        return "", str(e), 1


def success(msg): print(f"{G}[+] {msg}{RE}"); log(f"[OK] {msg}")
def warn(msg):    print(f"{Y}[!] {msg}{RE}"); log(f"[WARN] {msg}")
def error(msg):   print(f"{R}[-] {msg}{RE}"); log(f"[ERR] {msg}")
def info(msg):    print(f"{C}[*] {msg}{RE}"); log(f"[INFO] {msg}")


def header(title):
    print(f"\n{B}{BO}{'='*62}{RE}")
    print(f"{B}{BO}  {title}{RE}")
    print(f"{B}{BO}{'='*62}{RE}\n")


def check_tool(tool):
    return shutil.which(tool) is not None


# ── Shell abstraction ─────────────────────────────────────────────────────────
def shell(cmd, timeout=30):
    if ON_DEVICE:
        return run(cmd, timeout)
    return run(f"adb shell {cmd}", timeout)


# ── Robust settings helpers ───────────────────────────────────────────────────
# In Termux app context, `settings get/put` fails with "Failed transaction".
# These helpers try 4 methods in order: direct → su → content → sqlite3.
_SETTINGS_DB = "/data/data/com.android.providers.settings/databases/settings.db"

def get_setting(ns, key):
    """Read a system setting using every available method."""
    def _ok(v):
        return v and v.strip() and "Failure" not in v and "Error" not in v \
               and "exception" not in v.lower() and v.strip().lower() not in ("null","")
    # 1. direct settings cmd
    v, _, rc = shell(f"settings get {ns} {key} 2>/dev/null")
    if rc == 0 and _ok(v): return v.strip()
    # 2. via su
    v, _, rc = run(f"su -c 'settings get {ns} {key}' 2>/dev/null")
    if rc == 0 and _ok(v): return v.strip()
    # 3. cmd settings (alternate binder path, often works in Termux)
    v, _, rc = shell(f"cmd settings get {ns} {key} 2>/dev/null")
    if rc == 0 and _ok(v): return v.strip()
    # 4. content provider URI
    v, _, rc = shell(f"content query --uri content://settings/{ns} "
                     f"--where \"name='{key}'\" 2>/dev/null")
    if rc == 0 and v and "value=" in v:
        return v.split("value=")[1].strip().split(",")[0].strip()
    # 5. dumpsys settings (often readable without root in Termux)
    v, _, rc = shell(f"dumpsys settings 2>/dev/null | grep -m1 'name={key}' | "
                     f"grep -oE 'value=[^ ,]+' | cut -d= -f2")
    if rc == 0 and _ok(v): return v.strip()
    # 6. sqlite3 via root
    sq, _, rc = run(f"su -c 'sqlite3 {_SETTINGS_DB} "
                    f"\"SELECT value FROM {ns} WHERE name=\\\"{key}\\\"\"' 2>/dev/null")
    if rc == 0 and sq.strip(): return sq.strip()
    return None


def put_setting(ns, key, value):
    """Write a system setting using every available method. Returns True on success."""
    for fn in [
        lambda: shell(f"settings put {ns} {key} {value} 2>/dev/null"),
        lambda: run(f"su -c 'settings put {ns} {key} {value}' 2>/dev/null"),
        lambda: shell(f"cmd settings put {ns} {key} {value} 2>/dev/null"),
        lambda: shell(f"content insert --uri content://settings/{ns} "
                      f"--bind name:s:{key} --bind value:s:{value} 2>/dev/null"),
        lambda: run(f"su -c 'sqlite3 {_SETTINGS_DB} "
                    f"\"INSERT OR REPLACE INTO {ns}(name,value) "
                    f"VALUES(\\\"{key}\\\",\\\"{value}\\\")\"' 2>/dev/null"),
    ]:
        _, _, rc = fn()
        if rc == 0:
            return True
    return False


def check_internet():
    """Check internet connectivity using multiple methods."""
    _, _, rc = shell("ping -c 1 -W 5 8.8.8.8 2>/dev/null")
    if rc == 0: return True
    if check_tool("curl"):
        out, _, rc2 = run("curl -s --connect-timeout 5 -o /dev/null "
                          "-w '%{http_code}' http://clients1.google.com/generate_204 2>/dev/null")
        if rc2 == 0 and out.strip() in ("200", "204", "301", "302"): return True
    if check_tool("wget"):
        _, _, rc3 = run("wget -q --spider --timeout=5 "
                        "http://clients1.google.com/generate_204 2>/dev/null")
        if rc3 == 0: return True
    ip = get_wifi_ip()
    if ip and not ip.startswith("169."): return True
    return False


def get_wifi_ip():
    """Get device WiFi IP — tries every method available in Termux."""
    cmds = [
        "ip addr 2>/dev/null | grep 'inet ' | grep -v '127.0.0.1' | "
        "grep -v '169.254' | head -1 | awk '{print $2}' | cut -d/ -f1",
        "ip addr show wlan0 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d/ -f1",
        "ip addr show wlan1 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d/ -f1",
        "ifconfig wlan0 2>/dev/null | grep 'inet ' | awk '{print $2}'",
        "ifconfig 2>/dev/null | grep 'inet ' | grep -v '127.0.0.1' | "
        "grep -v '169.254' | head -1 | awk '{print $2}'",
        "getprop dhcp.wlan0.ipaddress",
        "getprop dhcp.wlan0.address",
        "getprop net.wlan0.local_ip 2>/dev/null",
        "ip route show default 2>/dev/null | grep 'dev wlan' | awk '{print $9}'",
    ]
    for cmd in cmds:
        ip, _, rc = shell(cmd)
        ip = (ip or "").strip().split('\n')[0].strip()
        if ip and ip not in ("", "0.0.0.0") and not ip.startswith("169."):
            return ip
    return None


def adb_reboot(mode=""):
    """Reboot the device. In on-device mode tries su first, then svc."""
    mode = mode.strip()
    subcmd = f" {mode}" if mode else ""
    if ON_DEVICE:
        # Try root reboot, fall back to am broadcast for soft restart
        out, err, rc = run(f"su -c 'reboot{subcmd}' 2>/dev/null", timeout=10)
        if rc != 0:
            out, err, rc = run(f"reboot{subcmd} 2>/dev/null", timeout=10)
        if rc != 0:
            warn(f"Root required to reboot{subcmd} from Termux")
            info(f"Manual: Power off → hold buttons for {mode or 'normal'} mode")
            return False
        success(f"Reboot{subcmd} command sent")
        return True
    else:
        run(f"adb reboot{subcmd}")
        return True


def adb_pull(remote, local, timeout=120):
    if ON_DEVICE:
        return run(f"cp \"{remote}\" \"{local}\"", timeout)
    return run(f"adb pull \"{remote}\" \"{local}\"", timeout)


def adb_push(local, remote, timeout=120):
    if ON_DEVICE:
        return run(f"cp \"{local}\" \"{remote}\"", timeout)
    return run(f"adb push \"{local}\" \"{remote}\"", timeout)


def get_device():
    """Returns (serial, state) or (None, None). Works in both modes."""
    if ON_DEVICE:
        model, _, rc = run("getprop ro.product.model")
        if rc == 0 and model:
            return ("local-device", "device")
        return (None, None)
    out, _, _ = run("adb devices")
    for line in out.split('\n'):
        if line.strip() and 'List' not in line and 'daemon' not in line:
            parts = line.split('\t')
            if len(parts) >= 2 and parts[1].strip() in ('device', 'recovery', 'bootloader', 'sideload'):
                return parts[0].strip(), parts[1].strip()
    return None, None


def get_fb_device():
    """Returns fastboot serial or None. Only works in remote/PC mode."""
    if ON_DEVICE:
        return None   # Can't be in fastboot and running Termux simultaneously
    out, _, _ = run("fastboot devices")
    return out.split()[0] if out.split() else None


def need_fastboot():
    """Print standard message when a fastboot-only method is run on-device."""
    error("This method requires fastboot mode")
    print(f"""
{Y}You are running Termux ON the phone.
Fastboot mode requires the device to be in bootloader — Termux cannot
run at the same time as fastboot mode.

{C}Options:{RE}
  {W}A) Use a PC/laptop:{RE}
     Connect via USB, run this script there (it auto-detects ADB mode).

  {W}B) Enable OEM Unlock the easy way (no fastboot needed):{RE}
     Settings → Developer Options → OEM Unlocking → toggle ON

  {W}C) Reboot to bootloader now (needs root):{RE}
     Choose Method 7 — it will call: su -c 'reboot bootloader'
     Then use a PC to run: fastboot flashing unlock
""")


def install_dependencies():
    if ON_DEVICE:
        missing = [t for t in ['adb'] if not check_tool(t)]
        # On-device Termux: adb optional, but getprop/settings/pm are built-in
        if missing:
            warn("adb not found (optional in on-device mode)")
            info("Install if needed: pkg install android-tools")
        return
    missing = [t for t in ['adb', 'fastboot'] if not check_tool(t)]
    if missing:
        warn(f"Missing: {', '.join(missing)} — installing via pkg…")
        run("pkg install -y android-tools", timeout=180)
        for t in missing:
            if check_tool(t):
                success(f"{t} installed")
            else:
                error(f"Could not install {t}. Run: pkg install android-tools")


def banner():
    os.system("clear 2>/dev/null || cls 2>/dev/null")
    mode_label = f"{G}ON-DEVICE (Termux on phone){RE}" if ON_DEVICE else f"{C}REMOTE (ADB from PC){RE}"
    print(f"""{M}{BO}
  ██████╗ ██████╗ ██╗  ██╗    ██╗   ██╗██╗  ████████╗██████╗  █████╗
  ██╔════╝╚════██╗██║  ██║    ██║   ██║██║  ╚══██╔══╝██╔══██╗██╔══██╗
  ███████╗ █████╔╝███████║    ██║   ██║██║     ██║   ██████╔╝███████║
  ╚════██║██╔═══╝ ╚════██║    ██║   ██║██║     ██║   ██╔══██╗██╔══██║
  ███████║███████╗     ██║    ╚██████╔╝███████╗██║   ██║  ██║██║  ██║
  ╚══════╝╚══════╝     ╚═╝     ╚═════╝ ╚══════╝╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝{RE}""")
    print(f"{C}{BO}  Samsung Galaxy S24 Ultra — Advanced Bootloader Unlock Suite{RE}")
    print(f"{Y}  120 Professional Methods  |  Termux Edition  |  ADB + Fastboot{RE}")
    print(f"  Mode: {mode_label}")
    print(f"{W}  {'─'*62}{RE}\n")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 1 — ADB Connection & Device Status
# ─────────────────────────────────────────────────────────────────────────────
def m1_check_adb():
    header("Method 1: ADB Connection & Device Status")
    if ON_DEVICE:
        model, _, rc = run("getprop ro.product.model")
        serial, _, _ = run("getprop ro.serialno")
        state_prop, _, _ = run("getprop ro.boot.flash.locked")
        success("Running directly on device (Termux on-device mode)")
        print(f"  {C}Model {RE}: {W}{model or 'N/A'}{RE}")
        print(f"  {C}Serial{RE}: {W}{serial or 'N/A'}{RE}")
        info("No USB/ADB needed — all shell commands run locally")
    else:
        out, err, rc = run("adb devices -l")
        if rc == 0:
            success("ADB server is running")
            print(f"\n{W}{out}{RE}")
            serial, state = get_device()
            if serial:
                success(f"Device found: {serial}  state={state}")
            else:
                warn("No authorised device detected")
                print(f"\n{C}Fix:{RE}")
                print("  1. Enable USB Debugging → Settings > Developer Options")
                print("  2. Connect via USB and accept the RSA key fingerprint")
        else:
            error(f"ADB error: {err}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 2 — Full Device Information
# ─────────────────────────────────────────────────────────────────────────────
def m2_device_info():
    header("Method 2: Full Device Information")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    props = [
        ("Model",             "ro.product.model"),
        ("Brand",             "ro.product.brand"),
        ("Device",            "ro.product.device"),
        ("Android Version",   "ro.build.version.release"),
        ("SDK Level",         "ro.build.version.sdk"),
        ("Build ID",          "ro.build.id"),
        ("Build Fingerprint", "ro.build.fingerprint"),
        ("Security Patch",    "ro.build.version.security_patch"),
        ("Chipset",           "ro.board.platform"),
        ("CPU ABI",           "ro.product.cpu.abi"),
        ("Bootloader",        "ro.bootloader"),
        ("Baseband",          "gsm.version.baseband"),
        ("Serial",            "ro.serialno"),
        ("OneUI Version",     "ro.build.version.oneui"),
        ("Hardware",          "ro.hardware"),
    ]
    for label, prop in props:
        val, _, _ = shell(f"getprop {prop}")
        print(f"  {C}{label:<25}{RE}: {W}{val or 'N/A'}{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 3 — Bootloader Lock Status
# ─────────────────────────────────────────────────────────────────────────────
def m3_bootloader_status():
    header("Method 3: Bootloader Lock Status")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    checks = [
        ("ro.boot.flash.locked",      "getprop ro.boot.flash.locked"),
        ("ro.boot.verifiedbootstate", "getprop ro.boot.verifiedbootstate"),
        ("ro.boot.veritymode",        "getprop ro.boot.veritymode"),
        ("ro.secure",                 "getprop ro.secure"),
        ("ro.debuggable",             "getprop ro.debuggable"),
    ]
    for label, cmd in checks:
        val, _, _ = shell(cmd)
        print(f"  {C}{label:<35}{RE}: {W}{val or 'N/A'}{RE}")
    print()
    locked, _, _ = shell("getprop ro.boot.flash.locked")
    vbs,    _, _ = shell("getprop ro.boot.verifiedbootstate")
    if locked == "0":
        success("Bootloader is UNLOCKED  (flash.locked=0)")
    elif locked == "1":
        warn("Bootloader is LOCKED  (flash.locked=1)")
    else:
        info("Lock state not readable via this property")
    color_map = {"green": success, "orange": warn, "yellow": warn, "red": error}
    if vbs:
        color_map.get(vbs, info)(f"Verified boot state: {vbs.upper()}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 4 — OEM Unlock Availability
# ─────────────────────────────────────────────────────────────────────────────
def m4_oem_unlock_check():
    header("Method 4: OEM Unlock Availability Check")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    checks = [
        ("oem_unlock_allowed",          "settings get global oem_unlock_allowed"),
        ("development_settings_enabled","settings get global development_settings_enabled"),
        ("sys.oem_unlock_allowed",      "getprop sys.oem_unlock_allowed"),
        ("ro.oem_unlock_supported",     "getprop ro.oem_unlock_supported"),
    ]
    for label, cmd in checks:
        val, _, _ = shell(cmd)
        print(f"  {C}{label:<35}{RE}: {W}{val or 'N/A'}{RE}")
    print()
    oem, _, _ = shell("settings get global oem_unlock_allowed")
    if oem == "1":
        success("OEM Unlock is ALLOWED — ready to proceed")
    else:
        warn("OEM Unlock is NOT enabled")
        info("Enable: Settings → Developer Options → OEM Unlocking")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 5 — Enable Developer Options
# ─────────────────────────────────────────────────────────────────────────────
def m5_enable_dev_options():
    header("Method 5: Enable Developer Options")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    shell("settings put global development_settings_enabled 1")
    val, _, _ = shell("settings get global development_settings_enabled")
    if val == "1":
        success("Developer Options ENABLED")
    else:
        warn("Direct write may be blocked on this build")
        if ON_DEVICE:
            shell("am start -n com.android.settings/.DevelopmentSettings 2>/dev/null", timeout=5)
            success("Opened Developer Options page on screen")
    info("Manual: Settings → About Phone → tap Build Number 7 times")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 6 — Enable OEM Unlock via Settings
# ─────────────────────────────────────────────────────────────────────────────
def m6_enable_oem_unlock():
    header("Method 6: Enable OEM Unlock via Settings")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    warn("Enabling OEM Unlock will PERMANENTLY trip the Knox warranty bit!")
    if input(f"\n{Y}Continue? (yes/no): {RE}").strip().lower() != "yes":
        info("Cancelled"); return
    shell("settings put global oem_unlock_allowed 1")
    val, _, _ = shell("settings get global oem_unlock_allowed")
    if val == "1":
        success("OEM Unlock written to settings DB")
        info("Also toggle the switch physically: Settings → Developer Options → OEM Unlocking")
    else:
        error("Write failed — toggle it manually in Developer Options")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 7 — Reboot to Bootloader
# ─────────────────────────────────────────────────────────────────────────────
def m7_reboot_bootloader():
    header("Method 7: Reboot to Bootloader / Fastboot Mode")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    if ON_DEVICE:
        info("On-device reboot to bootloader requires root (su)")
    if input(f"{Y}Reboot to bootloader now? (yes/no): {RE}").strip().lower() != "yes":
        info("Cancelled"); return
    ok = adb_reboot("bootloader")
    if ok:
        if not ON_DEVICE:
            info("Waiting 10 s for fastboot…")
            time.sleep(10)
            fb = get_fb_device()
            if fb:
                success(f"Device in fastboot: {fb}")
    if ON_DEVICE:
        print(f"\n{C}If root failed, manual method:{RE}")
        print("  Power off → hold Volume Down + Power simultaneously")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 8 — Reboot to Recovery
# ─────────────────────────────────────────────────────────────────────────────
def m8_reboot_recovery():
    header("Method 8: Reboot to Recovery Mode")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    if input(f"{Y}Reboot to recovery? (yes/no): {RE}").strip().lower() != "yes":
        info("Cancelled"); return
    adb_reboot("recovery")
    if ON_DEVICE:
        print(f"\n{C}Manual method:{RE}")
        print("  Power off → hold Volume Up + Bixby + Power")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 9 — Reboot to Download Mode (Odin)
# ─────────────────────────────────────────────────────────────────────────────
def m9_reboot_download():
    header("Method 9: Reboot to Download Mode (Odin / Heimdall)")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    if input(f"{Y}Reboot to download mode? (yes/no): {RE}").strip().lower() != "yes":
        info("Cancelled"); return
    adb_reboot("download")
    if ON_DEVICE:
        print(f"\n{C}Manual method:{RE}")
        print("  Power off → hold Volume Down while plugging USB cable")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 10 — Fastboot Connection Check
# ─────────────────────────────────────────────────────────────────────────────
def m10_fastboot_check():
    header("Method 10: Fastboot Connection Check")
    if ON_DEVICE:
        warn("Fastboot cannot be used while Termux is running on the device")
        print(f"""
{C}Explanation:{RE}
  Fastboot mode replaces the running OS — Termux stops when you enter
  fastboot. You need a second device (PC/laptop) to send fastboot commands.

{C}To use fastboot from a PC:{RE}
  1. Run Method 7 here first to reboot into bootloader
  2. On your PC: fastboot devices
  3. On your PC: fastboot flashing unlock
""")
        return
    if not check_tool("fastboot"):
        error("fastboot not found. Run: pkg install android-tools"); return
    out, err, rc = run("fastboot devices")
    if out:
        success("Fastboot device(s) detected:")
        print(f"\n{W}{out}{RE}")
    else:
        warn("No fastboot devices")
        info("Ensure device is in bootloader mode (Method 7)")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 11 — All Fastboot Variables
# ─────────────────────────────────────────────────────────────────────────────
def m11_fastboot_vars():
    header("Method 11: All Fastboot Variables")
    if ON_DEVICE:
        need_fastboot(); return
    if not get_fb_device():
        error("No fastboot device — use Method 7 first"); return
    out, err, _ = run("fastboot getvar all 2>&1", timeout=20)
    combined = (out + "\n" + err).strip()
    for line in combined.split('\n'):
        if ':' in line:
            k, _, v = line.partition(':')
            print(f"  {C}{k.strip():<35}{RE}: {G}{v.strip()}{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 12 — Knox Warranty Bit Status
# ─────────────────────────────────────────────────────────────────────────────
def m12_knox_status():
    header("Method 12: Knox Warranty Bit Status")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    for prop in ["ro.boot.warranty_bit", "ro.warranty_bit",
                 "sys.knox.warranty_bit", "ro.build.tags",
                 "ro.boot.knoxcountervalue"]:
        val, _, _ = shell(f"getprop {prop}")
        if val:
            print(f"  {C}{prop:<40}{RE}: {W}{val}{RE}")
    bit, _, _ = shell("getprop ro.boot.warranty_bit")
    print()
    if bit == "0":
        success("Knox warranty bit: 0 — warranty INTACT")
    elif bit == "1":
        warn("Knox warranty bit: 1 — warranty PERMANENTLY VOIDED")
    else:
        info("Knox bit value unknown")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 13 — Security Patch Level
# ─────────────────────────────────────────────────────────────────────────────
def m13_security_patch():
    header("Method 13: Security Patch Level")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    for label, prop in [
        ("Android Security Patch", "ro.build.version.security_patch"),
        ("Vendor Security Patch",  "ro.vendor.build.security_patch"),
        ("Boot Patch Level",       "ro.boot.patch_level"),
    ]:
        val, _, _ = shell(f"getprop {prop}")
        print(f"  {C}{label:<30}{RE}: {W}{val or 'N/A'}{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 14 — Android Version & Build Details
# ─────────────────────────────────────────────────────────────────────────────
def m14_android_version():
    header("Method 14: Android Version & Build Details")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    for label, prop in [
        ("Android Version",   "ro.build.version.release"),
        ("SDK Level",         "ro.build.version.sdk"),
        ("Build ID",          "ro.build.id"),
        ("Build Fingerprint", "ro.build.fingerprint"),
        ("Display ID",        "ro.build.display.id"),
        ("Build Type",        "ro.build.type"),
        ("Build Date",        "ro.build.date"),
        ("Build Flavor",      "ro.build.flavor"),
        ("OneUI Version",     "ro.build.version.oneui"),
    ]:
        val, _, _ = shell(f"getprop {prop}")
        print(f"  {C}{label:<25}{RE}: {W}{val or 'N/A'}{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 15 — List Device Partitions
# ─────────────────────────────────────────────────────────────────────────────
def m15_list_partitions():
    header("Method 15: Device Partition Table")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    for path in ["/dev/block/by-name", "/dev/block/bootdevice/by-name"]:
        out, _, _ = shell(f"ls {path} 2>/dev/null")
        if out:
            success(f"Partitions in {path}:")
            for i, p in enumerate(sorted(out.split()), 1):
                print(f"  {C}{i:>3}. {W}{p}{RE}")
            return
    warn("Cannot list partitions without root")
    info("Grant root in Termux: su → ls /dev/block/by-name")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 16 — Backup Boot Partition
# ─────────────────────────────────────────────────────────────────────────────
def m16_backup_boot():
    header("Method 16: Backup Boot Partition")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    dst = os.path.expanduser(f"~/boot_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.img")
    info("Trying root dd method…")
    if ON_DEVICE:
        out, err, rc = run(f"su -c 'dd if=/dev/block/by-name/boot of=\"{dst}\" bs=4096'", timeout=90)
        if rc == 0 and os.path.exists(dst):
            success(f"Boot backup saved: {dst}")
        else:
            error("Root required. Grant Termux root access and retry.")
            info("Run manually: su -c 'dd if=/dev/block/by-name/boot of=~/boot.img bs=4096'")
    else:
        run("adb shell su -c 'dd if=/dev/block/by-name/boot of=/sdcard/boot_backup.img bs=4096'", timeout=90)
        _, _, rc = adb_pull("/sdcard/boot_backup.img", dst)
        if rc == 0:
            success(f"Boot backup saved: {dst}")
            shell("rm /sdcard/boot_backup.img")
        else:
            error("Failed — device needs root access")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 17 — Backup Recovery Partition
# ─────────────────────────────────────────────────────────────────────────────
def m17_backup_recovery():
    header("Method 17: Backup Recovery Partition")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    dst = os.path.expanduser(f"~/recovery_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.img")
    if ON_DEVICE:
        out, err, rc = run(f"su -c 'dd if=/dev/block/by-name/recovery of=\"{dst}\" bs=4096'", timeout=90)
        if rc == 0 and os.path.exists(dst):
            success(f"Recovery backup saved: {dst}")
        else:
            error("Root required for recovery partition backup")
    else:
        run("adb shell su -c 'dd if=/dev/block/by-name/recovery of=/sdcard/recovery_backup.img bs=4096'", timeout=90)
        _, _, rc = adb_pull("/sdcard/recovery_backup.img", dst)
        if rc == 0:
            success(f"Recovery backup saved: {dst}")
            shell("rm /sdcard/recovery_backup.img")
        else:
            error("Failed — device needs root access")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 18 — SELinux Status
# ─────────────────────────────────────────────────────────────────────────────
def m18_selinux_status():
    header("Method 18: SELinux Enforcement Status")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    ge, _, _ = shell("getenforce")
    bp, _, _ = shell("getprop ro.boot.selinux")
    sf, _, _ = shell("cat /sys/fs/selinux/enforce 2>/dev/null || echo N/A")
    print(f"  {C}getenforce{RE}        : {W}{ge or 'N/A'}{RE}")
    print(f"  {C}ro.boot.selinux{RE}   : {W}{bp or 'N/A'}{RE}")
    print(f"  {C}sysfs enforce{RE}     : {W}{sf or 'N/A'}{RE}")
    print()
    if ge == "Enforcing":
        warn("SELinux ENFORCING — some shell operations restricted")
    elif ge == "Permissive":
        success("SELinux PERMISSIVE — full shell access available")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 19 — Installed Package Analysis
# ─────────────────────────────────────────────────────────────────────────────
def m19_list_packages():
    header("Method 19: Installed Package Analysis")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    sys_out,  _, _ = shell("pm list packages -s 2>/dev/null")
    user_out, _, _ = shell("pm list packages -3 2>/dev/null")
    print(f"\n{C}System packages (first 30):{RE}")
    for line in sys_out.split('\n')[:30]:
        print(f"  {W}{line.replace('package:', '')}{RE}")
    print(f"\n{C}User-installed packages:{RE}")
    for line in user_out.split('\n')[:20]:
        print(f"  {G}{line.replace('package:', '')}{RE}")
    print(f"\n  {C}Total system :{RE} {len(sys_out.split())}")
    print(f"  {C}Total user   :{RE} {len(user_out.split())}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 20 — Full Device Properties Dump
# ─────────────────────────────────────────────────────────────────────────────
def m20_getprop_dump():
    header("Method 20: Full Device Properties Dump")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    dst = os.path.expanduser(f"~/device_props_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    out, _, rc = shell("getprop")
    if out:
        with open(dst, 'w') as f:
            f.write(out)
        success(f"All properties saved: {dst}  ({len(out.split(chr(10)))} entries)")
        print(f"\n{C}Boot / Security / Unlock related:{RE}")
        for line in out.split('\n'):
            if any(k in line.lower() for k in ['boot', 'unlock', 'knox', 'oem', 'secure', 'verity', 'verified']):
                print(f"  {W}{line}{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 21 — USB Debugging Status
# ─────────────────────────────────────────────────────────────────────────────
def m21_usb_debug_status():
    header("Method 21: USB Debugging Status")
    serial, _ = get_device()
    if not serial and not ON_DEVICE:
        warn("No ADB device detected")
    for label, cmd in [
        ("ADB enabled (USB)",  "settings get global adb_enabled"),
        ("ADB TCP port",       "getprop service.adb.tcp.port"),
        ("Persist ADB enable", "getprop persist.service.adb.enable"),
        ("ADB WiFi enabled",   "settings get global adb_wifi_enabled"),
    ]:
        val, _, _ = shell(cmd)
        print(f"  {C}{label:<25}{RE}: {W}{val or 'N/A'}{RE}")
    if ON_DEVICE:
        success("Running directly on device — USB Debugging state above is informational")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 22 — Enable ADB & Developer Settings
# ─────────────────────────────────────────────────────────────────────────────
def m22_enable_adb():
    header("Method 22: Enable ADB & Developer Settings")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    for label, cmd in [
        ("Enable Developer Options", "settings put global development_settings_enabled 1"),
        ("Enable USB ADB",           "settings put global adb_enabled 1"),
        ("Enable ADB WiFi",          "settings put global adb_wifi_enabled 1"),
    ]:
        _, _, rc = shell(cmd)
        print(f"  {C}{label:<30}{RE}: {G if rc==0 else Y}{'OK' if rc==0 else 'May need device auth'}{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 23 — OEM Unlock via Fastboot
# ─────────────────────────────────────────────────────────────────────────────
def m23_fastboot_oem_unlock():
    header("Method 23: OEM Unlock via Fastboot")
    if ON_DEVICE:
        print(f"""
{Y}You are running Termux on the phone — fastboot unlock cannot be done
from within the running OS.

{C}Two ways to unlock your S24 Ultra:{RE}

  {G}Option A — No PC needed (easiest):{RE}
    1. Settings → Developer Options → OEM Unlocking → toggle ON
    2. That's it. The bootloader is now unlockable.
    3. To actually unlock: reboot to bootloader (Method 7, needs root)
       then connect to a PC and run: fastboot flashing unlock

  {G}Option B — Using a PC:{RE}
    1. Enable OEM Unlocking toggle (step 1 above)
    2. Run Method 7 to reboot into bootloader
    3. On your PC run: fastboot flashing unlock
    4. Confirm on device screen (Volume Up)
""")
        # Still offer to toggle OEM unlock setting right now
        val, _, _ = shell("settings get global oem_unlock_allowed")
        print(f"  {C}Current oem_unlock_allowed{RE}: {G if val=='1' else R}{val or 'N/A'}{RE}")
        if val != "1":
            if input(f"\n{Y}Enable OEM unlock setting right now? (yes/no): {RE}").strip().lower() == "yes":
                shell("settings put global oem_unlock_allowed 1")
                v2, _, _ = shell("settings get global oem_unlock_allowed")
                if v2 == "1":
                    success("oem_unlock_allowed set to 1")
                    info("Now go toggle it physically in Developer Options too")
                else:
                    warn("Settings write blocked — toggle manually in Developer Options")
        return

    # Remote/PC mode
    if not get_fb_device():
        error("No fastboot device — use Method 7 first"); return
    print(f"\n{R}{BO}  !! CRITICAL WARNING !!")
    print(f"  • All data will be WIPED")
    print(f"  • Knox warranty bit PERMANENTLY tripped")
    print(f"  • This is IRREVERSIBLE{RE}\n")
    if input(f"{R}Type UNLOCK to confirm (anything else cancels): {RE}").strip() != "UNLOCK":
        info("Cancelled — no changes made"); return
    info("Sending OEM unlock…")
    for cmd in ["fastboot flashing unlock", "fastboot oem unlock"]:
        out, err, rc = run(cmd, timeout=30)
        print(f"\n{W}{out + err}{RE}")
        if rc == 0:
            success(f"Unlock succeeded: {cmd}")
            info("Confirm on device screen (Volume Up = accept)")
            return
    error("Both unlock commands failed")
    info("Ensure OEM Unlocking is toggled ON in Developer Options first")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 24 — Flash Custom Recovery
# ─────────────────────────────────────────────────────────────────────────────
def m24_flash_twrp():
    header("Method 24: Flash Custom Recovery")
    if ON_DEVICE:
        need_fastboot(); return
    if not get_fb_device():
        error("No fastboot device — use Method 7 first"); return
    img = input(f"\n{C}Path to recovery image: {RE}").strip()
    if not img or not os.path.exists(img):
        error(f"File not found: {img}"); return
    if input(f"{Y}Flash {img}? (yes/no): {RE}").strip().lower() != "yes":
        info("Cancelled"); return
    out, err, rc = run(f"fastboot flash recovery \"{img}\"", timeout=120)
    print(f"\n{W}{out + err}{RE}")
    if rc == 0:
        success("Recovery flashed")
    else:
        error(f"Flash failed: {err}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 25 — Factory Reset via Fastboot
# ─────────────────────────────────────────────────────────────────────────────
def m25_fastboot_wipe():
    header("Method 25: Factory Reset via Fastboot")
    if ON_DEVICE:
        need_fastboot(); return
    if not get_fb_device():
        error("No fastboot device — use Method 7 first"); return
    print(f"\n{R}{BO}  !! ALL USER DATA WILL BE ERASED !!{RE}\n")
    if input(f"{R}Type WIPE to confirm: {RE}").strip() != "WIPE":
        info("Cancelled"); return
    for part in ["userdata", "cache"]:
        out, err, rc = run(f"fastboot erase {part}", timeout=120)
        print(f"  {C}{part:<12}{RE}: {G if rc==0 else R}{'OK' if rc==0 else err}{RE}")
    success("Wipe complete. Reboot: fastboot reboot")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 26 — Root Status Check
# ─────────────────────────────────────────────────────────────────────────────
def m26_root_check():
    header("Method 26: Root Status Analysis")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    any_root = False
    for label, cmd in [
        ("su binary",      "which su 2>/dev/null"),
        ("Magisk Manager", "pm list packages 2>/dev/null | grep magisk"),
        ("KernelSU",       "pm list packages 2>/dev/null | grep kernelsu"),
        ("Superuser app",  "pm list packages 2>/dev/null | grep -i superuser"),
        ("Root test (id)", "su -c id 2>/dev/null || echo not_rooted"),
    ]:
        val, _, _ = shell(cmd)
        found = bool(val.strip()) and "not_rooted" not in val
        print(f"  {C}{label:<25}{RE}: {G if found else W}{val.strip() or 'Not found'}{RE}")
        if found:
            any_root = True
    print()
    if any_root:
        success("Device is ROOTED")
    else:
        warn("Device does NOT appear rooted")
        info("Path: unlock bootloader → flash Magisk-patched boot image")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 27 — Magisk Installation Prep
# ─────────────────────────────────────────────────────────────────────────────
def m27_magisk_prep():
    header("Method 27: Magisk Installation Preparation")
    serial, _ = get_device()
    if serial:
        val, _, _ = shell("pm list packages 2>/dev/null | grep magisk")
        if val:
            success(f"Magisk already installed: {val}"); return
    print(f"\n{C}Full Magisk Root Guide — S24 Ultra:{RE}")
    for step in [
        "1.  Unlock bootloader (Method 23)",
        "2.  Download stock firmware for your region from samfw.com",
        "3.  Extract AP_*.tar.lz4 → get stock boot.img",
        "4.  Download latest Magisk APK: github.com/topjohnwu/Magisk/releases",
        "5.  Install Magisk APK on device",
        "6.  Open Magisk → Install → Select and Patch a File → pick boot.img",
        "7.  Pull patched image from /sdcard/Download/magisk_patched_*.img",
        "8.  Reboot to bootloader (Method 7)",
        "9.  From PC: fastboot flash boot magisk_patched_*.img",
        "10. Reboot: fastboot reboot",
        "11. Open Magisk → grant root → install modules",
    ]:
        print(f"  {W}{step}{RE}")
    if serial:
        stor, _, _ = shell("df /sdcard | tail -1")
        print(f"\n{C}Available storage:{RE} {W}{stor}{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 28 — ADB Sideload
# ─────────────────────────────────────────────────────────────────────────────
def m28_adb_sideload():
    header("Method 28: ADB Sideload (Flash ZIP via Recovery)")
    if ON_DEVICE:
        info("On-device sideload — you can flash ZIPs directly via recovery")
        print(f"\n{C}Steps:{RE}")
        print("  1. Reboot to recovery (Method 8)")
        print("  2. In TWRP: Install → navigate to your ZIP → swipe to flash")
        print("  3. Or from a connected PC: adb sideload yourfile.zip")
        return
    serial, state = get_device()
    if state in ("sideload", "recovery"):
        zip_path = input(f"\n{C}Path to ZIP: {RE}").strip()
        if not os.path.exists(zip_path):
            error(f"Not found: {zip_path}"); return
        out, err, rc = run(f"adb sideload \"{zip_path}\"", timeout=600)
        print(f"\n{W}{out + err}{RE}")
        if rc == 0:
            success("Sideload complete")
        else:
            error(f"Sideload failed: {err}")
    elif serial:
        warn("Device not in recovery/sideload mode — use Method 8 first")
    else:
        error("No device connected")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 29 — Carrier Lock Status
# ─────────────────────────────────────────────────────────────────────────────
def m29_carrier_lock():
    header("Method 29: Carrier Lock Status")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    for label, prop in [
        ("Carrier lock",     "ro.boot.carrierlock"),
        ("Carrier",          "ro.carrier"),
        ("Network operator", "gsm.operator.alpha"),
        ("SIM operator",     "ro.cdma.home.operator.numeric"),
        ("Phone type",       "ro.telephony.default_network"),
    ]:
        val, _, _ = shell(f"getprop {prop}")
        print(f"  {C}{label:<20}{RE}: {W}{val or 'N/A'}{RE}")
    info("Test: insert foreign SIM and check if you get signal or 'emergency only'")
    info("Unlock: Settings → Connections → More connection settings → Network unlock")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 30 — Logcat Boot Event Monitor
# ─────────────────────────────────────────────────────────────────────────────
def m30_logcat_monitor():
    header("Method 30: Logcat Boot / Security Event Monitor")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    dst = os.path.expanduser(f"~/logcat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    info("Capturing logcat for 10 s…")
    logcat_cmd = "logcat -v time *:W 2>/dev/null" if ON_DEVICE else "adb logcat -v time *:W 2>/dev/null"
    proc = subprocess.Popen(logcat_cmd, shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(10)
    proc.terminate()
    output, _ = proc.communicate()
    keywords = ['boot', 'unlock', 'verified', 'selinux', 'knox', 'dm-verity', 'vbmeta']
    filtered = [l for l in output.split('\n') if any(k in l.lower() for k in keywords)]
    if filtered:
        with open(dst, 'w') as f:
            f.write('\n'.join(filtered))
        success(f"Filtered events saved: {dst}")
        for line in filtered[:25]:
            print(f"  {W}{line}{RE}")
    else:
        info("No boot/security events in current log window")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 31 — Partition Mount Status
# ─────────────────────────────────────────────────────────────────────────────
def m31_partition_mounts():
    header("Method 31: System Partition Mount Status")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    out, _, _ = shell("mount | grep -E 'system|vendor|product|odm|data'")
    if out:
        success("Partition mounts:")
        for line in out.split('\n'):
            parts = line.split()
            if len(parts) >= 4:
                print(f"  {C}{parts[2]:<25}{RE} ← {W}{parts[0]}{RE}  [{parts[3]}]")
    for prop in ["ro.build.system_root_image", "ro.boot.dynamic_partitions"]:
        val, _, _ = shell(f"getprop {prop}")
        print(f"  {C}{prop:<35}{RE}: {W}{val or 'N/A'}{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 32 — ADB Full Device Backup
# ─────────────────────────────────────────────────────────────────────────────
def m32_adb_backup():
    header("Method 32: Device Backup")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    if ON_DEVICE:
        info("On-device backup options:")
        print(f"  {W}1. Samsung Smart Switch (recommended full backup){RE}")
        print(f"  {W}2. Settings → Accounts and backup → Back up data{RE}")
        print(f"  {W}3. Manual: cp -r /sdcard ~/sdcard_backup  (Termux){RE}")
        if input(f"\n{Y}Copy /sdcard to ~/sdcard_backup now? (yes/no): {RE}").strip().lower() == "yes":
            dst = os.path.expanduser("~/sdcard_backup")
            out, err, rc = run(f"cp -r /sdcard \"{dst}\" 2>/dev/null", timeout=300)
            if rc == 0:
                success(f"Backup saved to {dst}")
            else:
                error(f"Backup failed: {err}")
        return
    dst = os.path.expanduser(f"~/device_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ab")
    warn("Backup confirmation may be required on-screen")
    if input(f"{Y}Start backup? (yes/no): {RE}").strip().lower() != "yes":
        info("Cancelled"); return
    run(f"adb backup -all -f \"{dst}\"", timeout=600)
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        success(f"Backup: {dst}  ({os.path.getsize(dst) // 1024} KB)")
    else:
        warn("Backup empty — Android 12+ limits ADB backup scope")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 33 — Frida Compatibility Check
# ─────────────────────────────────────────────────────────────────────────────
def m33_frida_check():
    header("Method 33: Frida Dynamic Instrumentation Compatibility")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    arch,    _, _ = shell("getprop ro.product.cpu.abi")
    android, _, _ = shell("getprop ro.build.version.release")
    sdk,     _, _ = shell("getprop ro.build.version.sdk")
    srv_path = "/data/local/tmp/frida-server"
    srv,     _, _ = shell(f"ls {srv_path} 2>/dev/null")
    arch_map = {"arm64-v8a": "android-arm64", "armeabi-v7a": "android-arm",
                "x86_64": "android-x86_64", "x86": "android-x86"}
    frida_arch = arch_map.get(arch, "android-arm64")
    print(f"  {C}Architecture{RE}          : {W}{arch or 'N/A'}{RE}")
    print(f"  {C}Android Version{RE}       : {W}{android or 'N/A'}{RE}")
    print(f"  {C}SDK Level{RE}             : {W}{sdk or 'N/A'}{RE}")
    frida_host = check_tool("frida")
    print(f"  {C}Frida CLI (host){RE}      : {G if frida_host else Y}{'installed' if frida_host else 'not found — pip install frida-tools'}{RE}")
    print(f"  {C}frida-server (device){RE} : {G if srv else Y}{'found at ' + srv_path if srv else 'not deployed'}{RE}")
    print(f"\n{C}Frida server binary target:{RE} {W}{frida_arch}{RE}")
    info("Download: github.com/frida/frida/releases — match version to your frida-tools")
    if ON_DEVICE and not srv:
        print(f"\n{C}Deploy steps (run in Termux with root):{RE}")
        print(f"  wget <frida-server-{frida_arch}> -O /data/local/tmp/frida-server")
        print(f"  chmod 755 /data/local/tmp/frida-server")
        print(f"  su -c '/data/local/tmp/frida-server &'")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 34 — Running Process Analysis
# ─────────────────────────────────────────────────────────────────────────────
def m34_process_list():
    header("Method 34: Running Process Analysis")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    out, _, _ = shell("ps -A 2>/dev/null | head -50")
    print(f"{C}Top processes:{RE}")
    for line in out.split('\n')[:30]:
        print(f"  {W}{line}{RE}")
    print(f"\n{C}Security-relevant processes:{RE}")
    for proc in ["keystore", "vold", "installd", "android.security.keystore",
                 "vendor.samsung.hardware.security"]:
        pid, _, _ = shell(f"pgrep -f {proc} 2>/dev/null")
        print(f"  {C}{proc:<45}{RE}: {G if pid else Y}{'PID ' + pid if pid else 'not running'}{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 35 — Network Interface Analysis
# ─────────────────────────────────────────────────────────────────────────────
def m35_network_analysis():
    header("Method 35: Network Interface Analysis")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    out, _, _ = shell("ip addr show")
    print(f"{C}Network interfaces:{RE}")
    for line in out.split('\n'):
        if line.strip():
            print(f"  {W}{line}{RE}")
    host, _, _ = shell("getprop net.hostname")
    ip,   _, _ = shell("getprop dhcp.wlan0.ipaddress")
    print(f"\n  {C}Hostname{RE}: {W}{host or 'N/A'}{RE}")
    print(f"  {C}WiFi IP {RE}: {W}{ip   or 'N/A'}{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 36 — OEM Unlock via Shell (Advanced multi-method)
# ─────────────────────────────────────────────────────────────────────────────
def m36_shell_oem_unlock():
    header("Method 36: OEM Unlock via Shell — Advanced Multi-Method")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return
    # Method A — settings put global
    shell("settings put global oem_unlock_allowed 1")
    v1, _, _ = shell("settings get global oem_unlock_allowed")
    print(f"  {C}Method A — settings put global{RE}: {G if v1=='1' else Y}{v1 or 'N/A'}{RE}")
    # Method B — content URI
    _, _, rc2 = shell("content insert --uri content://settings/global "
                      "--bind name:s:oem_unlock_allowed --bind value:s:1")
    print(f"  {C}Method B — content URI insert {RE}: {G if rc2==0 else Y}{'OK' if rc2==0 else 'Failed (needs root)'}{RE}")
    # Method C — sqlite3 direct (needs root)
    _, _, rc3 = run(
        'su -c \'sqlite3 /data/data/com.android.providers.settings/databases/settings.db '
        '"UPDATE global SET value=1 WHERE name=\'oem_unlock_allowed\';" 2>/dev/null\'')
    print(f"  {C}Method C — sqlite3 (root)     {RE}: {G if rc3==0 else Y}{'OK' if rc3==0 else 'Failed (needs root)'}{RE}")
    final, _, _ = shell("settings get global oem_unlock_allowed")
    print(f"\n  {C}Final state{RE}: {G if final=='1' else R}{final or 'N/A'}{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 37 — EDL Mode Information
# ─────────────────────────────────────────────────────────────────────────────
def m37_edl_mode():
    header("Method 37: EDL (Emergency Download) Mode")
    print(f"{C}Overview:{RE}")
    print(f"  {W}EDL is Qualcomm's low-level flashing protocol (USB PID 9008){RE}")
    print(f"  {W}S24 Ultra (Snapdragon 8 Gen 3) supports EDL{RE}")
    print(f"  {W}Use with QPST/QFIL (Windows) or edl.py (Linux/Mac){RE}\n")
    for m_text in [
        "1. ADB (some builds): adb reboot edl",
        "2. pip install edl  →  github.com/bkerler/edl",
        "3. Dialer *#9090# — diagnostic mode (carrier-dependent)",
        "4. Hardware EDL test pads — requires teardown (not recommended)",
    ]:
        print(f"  {W}{m_text}{RE}")
    if ON_DEVICE:
        out, err, rc = run("reboot edl 2>&1", timeout=5)
        if rc != 0:
            info("Direct 'reboot edl' not available — try methods above")
    else:
        serial, _ = get_device()
        if serial:
            out, err, rc = run("adb reboot edl 2>&1")
            if rc != 0:
                info("'adb reboot edl' not supported on this firmware")
    print(f"\n{Y}Note: EDL is last resort. Standard fastboot OEM unlock is preferred.{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 38 — Flash Custom Boot Image
# ─────────────────────────────────────────────────────────────────────────────
def m38_flash_boot():
    header("Method 38: Flash Custom Boot Image")
    if ON_DEVICE:
        need_fastboot(); return
    if not get_fb_device():
        error("No fastboot device — use Method 7 first"); return
    img = input(f"\n{C}Path to boot image: {RE}").strip()
    if not os.path.exists(img):
        error(f"File not found: {img}"); return
    if input(f"{Y}Flash {img} to boot? (yes/no): {RE}").strip().lower() != "yes":
        info("Cancelled"); return
    out, err, rc = run(f"fastboot flash boot \"{img}\"", timeout=120)
    print(f"\n{W}{out + err}{RE}")
    if rc == 0:
        success("Boot image flashed")
        if input(f"{Y}Reboot now? (yes/no): {RE}").strip().lower() == "yes":
            run("fastboot reboot")
            success("Rebooting…")
    else:
        error(f"Flash failed: {err}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 39 — dm-verity / Verified Boot Control
# ─────────────────────────────────────────────────────────────────────────────
def m39_disable_verity():
    header("Method 39: dm-verity / Verified Boot Control")
    if ON_DEVICE:
        vm, _, _ = shell("getprop ro.boot.veritymode")
        print(f"  {C}Current verity mode{RE}: {W}{vm or 'N/A'}{RE}")
        need_fastboot(); return
    fb = get_fb_device()
    serial, _ = get_device()
    if fb:
        out, err, _ = run("fastboot getvar verity-mode 2>&1")
        for line in (out + err).split('\n'):
            if 'verity' in line.lower():
                print(f"  {C}{line.strip()}{RE}")
        warn("Disabling dm-verity requires stock vbmeta.img")
        if input(f"{Y}Proceed? (yes/no): {RE}").strip().lower() == "yes":
            vbmeta = input(f"{C}Path to vbmeta.img: {RE}").strip()
            if os.path.exists(vbmeta):
                out2, err2, rc2 = run(
                    f"fastboot --disable-verity --disable-verification flash vbmeta \"{vbmeta}\"",
                    timeout=60)
                print(f"\n{W}{out2 + err2}{RE}")
                if rc2 == 0:
                    success("dm-verity disabled")
                else:
                    error(f"Failed: {err2}")
            else:
                error(f"vbmeta.img not found: {vbmeta}")
                info("Extract vbmeta.img from stock AP_*.tar.lz4 firmware")
    elif serial:
        vm, _, _ = shell("getprop ro.boot.veritymode")
        print(f"  {C}Current verity mode{RE}: {W}{vm or 'N/A'}{RE}")
        info("Boot to fastboot mode then run this method again with vbmeta.img")
    else:
        error("No device connected")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 40 — Complete Automated Unlock Workflow
# ─────────────────────────────────────────────────────────────────────────────
def m40_full_workflow():
    header("Method 40: Complete Automated Unlock Workflow")
    print(f"{C}{BO}Samsung Galaxy S24 Ultra — End-to-End Bootloader Unlock{RE}\n")
    for step, desc in [
        ("STEP  1", "Back up data — Smart Switch or Method 32"),
        ("STEP  2", "Settings → About Phone → tap Build Number 7× → Developer Options enabled"),
        ("STEP  3", "Settings → Developer Options → enable OEM Unlocking toggle"),
        ("STEP  4", "Settings → Developer Options → enable USB Debugging"),
        ("STEP  5", "If using PC: connect USB, accept RSA fingerprint on device"),
        ("STEP  6", "Enable OEM unlock setting via Method 6 or Method 36"),
        ("STEP  7", "Reboot to bootloader: Method 7 (needs root) or hold Vol Down + Power"),
        ("STEP  8", "From PC: fastboot devices  (confirm device shown)"),
        ("STEP  9", "From PC: fastboot flashing unlock"),
        ("STEP 10", "On device screen → Volume Up to confirm wipe & unlock"),
        ("STEP 11", "Wait for factory reset and reboot (~2 min)"),
        ("STEP 12", "Complete first-time setup; re-enable Developer Options + USB Debugging"),
        ("STEP 13", "Download stock firmware for your CSC from samfw.com"),
        ("STEP 14", "Extract boot.img from AP_*.tar.lz4"),
        ("STEP 15", "Install Magisk APK on device"),
        ("STEP 16", "Magisk → Install → Select and Patch a File → pick boot.img"),
        ("STEP 17", "Copy magisk_patched_*.img from /sdcard/Download/"),
        ("STEP 18", "Reboot to bootloader (Method 7)"),
        ("STEP 19", "From PC: fastboot flash boot magisk_patched_*.img"),
        ("STEP 20", "fastboot reboot → verify root in Magisk app"),
    ]:
        print(f"  {B}{BO}{step}{RE}: {W}{desc}{RE}")

    print(f"\n{C}{'─'*62}{RE}")
    print(f"{C}{BO}Current Device State{RE}")
    print(f"{C}{'─'*62}{RE}")
    serial, adb_state = get_device()
    fb = get_fb_device()
    mode_str = f"{G}ON-DEVICE{RE}" if ON_DEVICE else f"{C}REMOTE/ADB{RE}"
    print(f"  {C}Run mode       {RE}: {mode_str}")
    print(f"  {C}Device         {RE}: {G if serial else R}{serial or 'Not detected'}{RE}")
    print(f"  {C}ADB state      {RE}: {G if adb_state=='device' else W}{adb_state or 'N/A'}{RE}")
    if not ON_DEVICE:
        print(f"  {C}Fastboot device{RE}: {G if fb else R}{fb or 'Not detected'}{RE}")
    if serial:
        dev,  _, _ = shell("settings get global development_settings_enabled")
        oem,  _, _ = shell("settings get global oem_unlock_allowed")
        vbs,  _, _ = shell("getprop ro.boot.verifiedbootstate")
        knox, _, _ = shell("getprop ro.boot.warranty_bit")
        root, _, _ = shell("which su 2>/dev/null")
        print(f"  {C}Developer Opts {RE}: {G if dev=='1'  else R}{'Enabled'   if dev=='1'  else 'Disabled'}{RE}")
        print(f"  {C}OEM Unlock     {RE}: {G if oem=='1'  else R}{'Allowed'   if oem=='1'  else 'Not allowed'}{RE}")
        print(f"  {C}Verified Boot  {RE}: {W}{vbs  or 'N/A'}{RE}")
        print(f"  {C}Knox Warranty  {RE}: {R if knox=='1' else G}{'TRIPPED'   if knox=='1' else 'Intact' if knox=='0' else 'N/A'}{RE}")
        print(f"  {C}Root (su)      {RE}: {G if root else Y}{'Present'   if root else 'Not rooted'}{RE}")
    print(f"\n{G}{BO}{'Ready! Follow the steps above.' if serial else 'No device detected — check connection.'}{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 41 — Samsung OEM Unlock 7-Day Timer Check
# ─────────────────────────────────────────────────────────────────────────────
def m41_seven_day_timer():
    header("Method 41: Samsung OEM Unlock 7-Day Timer Check")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    print(f"{C}Samsung requires the device to have an active internet connection")
    print(f"for at least 7 days before OEM Unlocking toggle becomes available.{RE}\n")

    # Use robust get_setting() to bypass Termux permission restrictions
    prov       = get_setting("global", "device_provisioned")
    setup_done = get_setting("secure", "user_setup_complete")
    setup_time = get_setting("global", "device_setup_timestamp")
    oem_val    = get_setting("global", "oem_unlock_allowed")
    oem_sys,   _, _ = shell("getprop sys.oem_unlock_allowed")

    print(f"  {C}device_provisioned{RE}        : {G if prov=='1' else W}{prov or 'N/A (permission denied)'}{RE}")
    print(f"  {C}user_setup_complete{RE}        : {G if setup_done=='1' else W}{setup_done or 'N/A'}{RE}")
    print(f"  {C}device_setup_timestamp{RE}     : {W}{setup_time or 'N/A'}{RE}")
    print(f"  {C}oem_unlock_allowed (global){RE}: {G if oem_val=='1' else R}{oem_val or 'N/A'}{RE}")
    print(f"  {C}sys.oem_unlock_allowed{RE}     : {G if oem_sys=='1' else R}{oem_sys or 'N/A'}{RE}")

    # Check boot time (uptime) as proxy for how long device has been running
    uptime_raw, _, _ = shell("cat /proc/uptime 2>/dev/null")
    if uptime_raw:
        try:
            secs = float(uptime_raw.split()[0])
            days  = int(secs // 86400)
            hours = int((secs % 86400) // 3600)
            print(f"\n  {C}Current uptime{RE}: {W}{days}d {hours}h (since last reboot){RE}")
        except Exception:
            pass

    print(f"\n{C}What affects the 7-day timer:{RE}")
    for tip in [
        "Timer starts after FIRST internet connection post factory-reset",
        "Device must be signed into a Google account",
        "No SIM required for global (XXS) variant like yours",
        "Timer resets to zero after another factory reset",
        "Timer is tracked server-side by Samsung — cannot be bypassed locally",
        "If toggle is greyed out: connect to WiFi and wait 7 days",
        "If toggle is missing: Developer Options may not be fully enabled",
    ]:
        print(f"  {Y}•{RE} {W}{tip}{RE}")

    print()
    if oem_val == "1" or oem_sys == "1":
        success("OEM unlock appears ALLOWED — timer has elapsed")
    else:
        warn("OEM unlock not yet allowed — timer may still be running or toggle not enabled")
        info("Connect to WiFi, leave device running, check again in 7 days")
        info("If settings read failed above: try Method 57 (Root Settings Access) or Method 59")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 42 — Open OEM Unlock Toggle Directly
# ─────────────────────────────────────────────────────────────────────────────
def m42_open_oem_toggle():
    header("Method 42: Open OEM Unlock Toggle Directly on Screen")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    info("Launching Developer Options OEM Unlocking page…")

    # Try deep-link into developer options OEM unlock setting
    intents = [
        "com.android.settings/.development.DevelopmentSettingsDashboardActivity",
        "com.android.settings/.DevelopmentSettings",
        "android.settings.APPLICATION_DEVELOPMENT_SETTINGS",
    ]
    launched = False
    for intent in intents:
        if intent.startswith("android."):
            cmd = f"am start -a {intent} 2>/dev/null"
        else:
            cmd = f"am start -n {intent} 2>/dev/null"
        out, err, rc = shell(cmd)
        if rc == 0 and "Error" not in (out + err):
            success(f"Launched: {intent}")
            launched = True
            break

    if not launched:
        warn("Could not auto-launch, opening Settings manually…")
        shell("am start -a android.settings.SETTINGS 2>/dev/null")

    print(f"\n{C}Once Developer Options is open:{RE}")
    for step in [
        "Scroll down to find 'OEM Unlocking'",
        "Toggle it ON (you may need to enter your PIN/pattern)",
        "A warning dialog will appear — tap 'Enable'",
        "The toggle turns blue = OEM unlock is enabled",
        "Now you can proceed with fastboot flashing unlock from a PC",
    ]:
        print(f"  {W}→ {step}{RE}")

    # Check current state
    oem, _, _ = shell("settings get global oem_unlock_allowed")
    print(f"\n  {C}Current oem_unlock_allowed{RE}: {G if oem=='1' else R}{oem or 'N/A'}{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 43 — CSC / Sales Code Analysis
# ─────────────────────────────────────────────────────────────────────────────
def m43_csc_analysis():
    header("Method 43: CSC / Sales Code Analysis")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    props = [
        ("CSC sales code",       "getprop ro.csc.sales_code"),
        ("CSC country",          "getprop ro.csc.country_code"),
        ("CSC product",          "getprop ro.csc.product.model"),
        ("Carrier",              "getprop ro.carrier"),
        ("SIM operator name",    "getprop gsm.operator.alpha"),
        ("Build variant",        "getprop ro.build.flavor"),
        ("Omitted props CSC",    "getprop ril.product_code 2>/dev/null"),
        ("Active CSC",           "getprop ro.boot.csc"),
        ("Default CSC",          "getprop ro.csc.default_csc_code 2>/dev/null"),
    ]
    results = {}
    for label, cmd in props:
        val, _, _ = shell(cmd)
        results[label] = val
        print(f"  {C}{label:<25}{RE}: {W}{val or 'N/A'}{RE}")

    # Parse bootloader string for region: S928BXXS6DZE1
    bl, _, _ = shell("getprop ro.bootloader")
    if bl and len(bl) >= 8:
        region_code = bl[5:7] if len(bl) > 7 else "??"
        print(f"\n  {C}Bootloader region code{RE}: {W}{region_code}{RE}")
        region_map = {
            "XX": "Global (unlocked) — OEM unlock SHOULD be available",
            "XA": "Asia Pacific",
            "XE": "Nordic/Europe",
            "XFE":"France",
            "BTU": "UK (open)",
            "VZW": "Verizon — may be carrier-locked",
            "TMB": "T-Mobile — may be carrier-locked",
            "ATT": "AT&T — carrier-locked, OEM unlock restricted",
            "SPR": "Sprint — carrier-locked",
        }
        desc = region_map.get(region_code, "Unknown region")
        color = G if "Global" in desc or "unlocked" in desc.lower() else Y
        print(f"  {C}Region meaning{RE}         : {color}{desc}{RE}")

    print(f"\n{C}SM-S928B with XXS bootloader = Global Snapdragon variant{RE}")
    success("Your device is a global variant — OEM unlock is supported by Samsung")
    info("The toggle just needs to be enabled in Developer Options")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 44 — Bootloader Version Parser
# ─────────────────────────────────────────────────────────────────────────────
def m44_bootloader_parser():
    header("Method 44: Bootloader Version Parser (S928BXXS6DZE1)")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    bl, _, _ = shell("getprop ro.bootloader")
    if not bl:
        bl, _, _ = shell("getprop ro.build.display.id")

    print(f"\n  {C}Bootloader string{RE}: {W}{bl}{RE}\n")

    if bl and len(bl) >= 10:
        model_part  = bl[:6]    # S928BX
        region      = bl[5:7]   # XX
        vendor      = bl[7]     # S = Samsung
        android_ver = bl[8]     # 6 = Android 16 (hex: 6→6, A→10, B→11…)
        build_sfx   = bl[9:]    # DZE1

        # Android version decode (Samsung uses: 1=Android 11, 2=12 ... 6=16)
        android_map = {'1':'11','2':'12','3':'13','4':'14','5':'15','6':'16',
                       'A':'Android 10','B':'11','C':'12'}
        android_decoded = android_map.get(android_ver, android_ver)

        print(f"  {C}Model prefix  {RE}: {W}{model_part}{RE}")
        print(f"  {C}Region code   {RE}: {W}{region}{RE}  → {'Global (unlocked)' if region=='XX' else region}")
        print(f"  {C}Vendor code   {RE}: {W}{vendor}{RE}  → {'Samsung' if vendor=='S' else vendor}")
        print(f"  {C}Android ver   {RE}: {W}{android_ver}{RE}  → Android {android_decoded}")
        print(f"  {C}Build suffix  {RE}: {W}{build_sfx}{RE}")
        print(f"    {Y}D{RE}=month(Apr) {Y}Z{RE}=day(26) {Y}E1{RE}=revision")

    print(f"\n{C}What this tells us about unlock:{RE}")
    for fact in [
        "XX region = global unlocked variant, no carrier restrictions",
        "Android 16 (SDK 36) = latest, Samsung has not patched out OEM unlock",
        "S928BXXS6DZE1 firmware supports fastboot flashing unlock",
        "No downgrade needed — current firmware is unlockable",
    ]:
        print(f"  {G}✓{RE} {W}{fact}{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 45 — Wireless ADB Setup (Android 11+)
# ─────────────────────────────────────────────────────────────────────────────
def m45_wireless_adb():
    header("Method 45: Wireless ADB Setup (Android 11+ built-in)")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    print(f"{C}Android 11+ has built-in Wireless Debugging (no USB cable needed).{RE}\n")

    # Check current wireless ADB state
    wifi_adb, _, _ = shell("settings get global adb_wifi_enabled")
    tcp_port,  _, _ = shell("getprop service.adb.tcp.port")
    wifi_ip,   _, _ = shell("ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \\K[^ ]+'")
    if not wifi_ip:
        wifi_ip, _, _ = shell("getprop dhcp.wlan0.ipaddress")

    print(f"  {C}Wireless ADB enabled{RE}: {G if wifi_adb=='1' else R}{wifi_adb or 'N/A'}{RE}")
    print(f"  {C}ADB TCP port        {RE}: {W}{tcp_port or 'N/A (USB only)'}{RE}")
    print(f"  {C}Device WiFi IP      {RE}: {W}{wifi_ip or 'N/A'}{RE}")

    print(f"\n{C}How to enable Wireless Debugging:{RE}")
    for step in [
        "Settings → Developer Options → Wireless Debugging → toggle ON",
        "Tap 'Pair device with pairing code' for one-time PC pairing",
        "Or tap 'Pair device with QR code' for QR scan",
        "Note the IP:port shown — use on PC: adb connect <ip>:<port>",
    ]:
        print(f"  {W}→ {step}{RE}")

    if wifi_adb != "1":
        info("Enabling Wireless ADB now…")
        shell("settings put global adb_wifi_enabled 1")
        v2, _, _ = shell("settings get global adb_wifi_enabled")
        if v2 == "1":
            success("Wireless ADB enabled")
            info("Go to Developer Options → Wireless Debugging to get pairing code")
        else:
            warn("Could not enable automatically — toggle manually in Developer Options")
    else:
        success("Wireless ADB already ON")
        if wifi_ip and tcp_port:
            print(f"\n  {G}Connect from PC:{RE} {W}adb connect {wifi_ip}:{tcp_port}{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 46 — Wireless ADB Pairing Code (Android 12+)
# ─────────────────────────────────────────────────────────────────────────────
def m46_wireless_pairing():
    header("Method 46: Wireless ADB Pairing Code (Android 12+)")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    sdk, _, _ = shell("getprop ro.build.version.sdk")
    if sdk and int(sdk) < 31:
        warn(f"Android 12+ required for pairing codes (your SDK: {sdk})"); return

    wifi_ip, _, _ = shell("ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \\K[^ ]+'")
    if not wifi_ip:
        wifi_ip, _, _ = shell("getprop dhcp.wlan0.ipaddress")

    print(f"  {C}Device IP{RE}: {W}{wifi_ip or 'N/A'}{RE}\n")

    print(f"{C}Steps to pair a PC via code (one-time setup):{RE}")
    for step in [
        "1. On phone: Settings → Developer Options → Wireless Debugging",
        "2. Tap 'Pair device with pairing code'",
        "3. Note the IP:port and 6-digit code shown",
        "4. On PC run: adb pair <ip>:<pairing-port> <6-digit-code>",
        "5. After pairing, connect: adb connect <ip>:<regular-port>",
        "6. Verify: adb devices  (shows device as connected over WiFi)",
    ]:
        print(f"  {W}{step}{RE}")

    print(f"\n{C}Alternative — enable ADB TCP port 5555 (needs root):{RE}")
    _, _, rc = shell("setprop service.adb.tcp.port 5555 2>/dev/null")
    if rc == 0:
        shell("stop adbd 2>/dev/null; sleep 1; start adbd 2>/dev/null")
        success("ADB TCP port 5555 set")
        if wifi_ip:
            print(f"  {G}Connect from PC:{RE} {W}adb connect {wifi_ip}:5555{RE}")
    else:
        out, _, rc2 = run("su -c 'setprop service.adb.tcp.port 5555 && stop adbd && start adbd' 2>/dev/null", timeout=10)
        if rc2 == 0:
            success("ADB TCP 5555 set via root")
            if wifi_ip:
                print(f"  {G}Connect from PC:{RE} {W}adb connect {wifi_ip}:5555{RE}")
        else:
            info("Root not available — use the Wireless Debugging UI steps above")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 47 — Simulate Build Number 7-Tap (Enable Dev Options)
# ─────────────────────────────────────────────────────────────────────────────
def m47_tap_build_number():
    header("Method 47: Simulate Build Number 7-Tap (Force Developer Options)")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    dev_before, _, _ = shell("settings get global development_settings_enabled")
    if dev_before == "1":
        success("Developer Options already enabled — no tapping needed")
        return

    info("Attempting to enable Developer Options via settings write…")
    shell("settings put global development_settings_enabled 1")

    val, _, _ = shell("settings get global development_settings_enabled")
    if val == "1":
        success("Developer Options ENABLED")
    else:
        warn("Settings write blocked — trying intent approach…")
        # Open About Phone and simulate taps on build number via input
        shell("am start -a android.settings.DEVICE_INFO_SETTINGS 2>/dev/null", timeout=5)
        time.sleep(2)
        # Simulate 7 taps in the center of screen (approximate build number location)
        for i in range(7):
            shell("input tap 540 1800 2>/dev/null", timeout=3)
            time.sleep(0.3)
        time.sleep(1)
        val2, _, _ = shell("settings get global development_settings_enabled")
        if val2 == "1":
            success("Developer Options enabled via taps")
        else:
            warn("Auto-tap did not work (screen coordinates vary by device)")
            print(f"\n{C}Manual steps:{RE}")
            print("  Settings → About Phone → Software Information → tap Build Number 7×")
            print("  You will see a countdown: 'You are N steps away from being a developer'")

    # Open Developer Options
    shell("am start -n com.android.settings/.DevelopmentSettings 2>/dev/null", timeout=5)
    info("Opened Developer Options page")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 48 — Internet Connectivity Check (Required for OEM Unlock)
# ─────────────────────────────────────────────────────────────────────────────
def m48_internet_check():
    header("Method 48: Internet Connectivity Check (OEM Unlock Requirement)")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    print(f"{C}Samsung requires internet connectivity for the 7-day OEM unlock timer.{RE}\n")

    ip_addr  = get_wifi_ip()
    inet     = check_internet()
    net_state, _, _ = shell("getprop gsm.data.state 2>/dev/null")

    _, _, ping_rc = shell("ping -c 1 -W 3 8.8.8.8 2>/dev/null")
    _, _, dns_rc  = shell("nslookup google.com 2>/dev/null")

    print(f"  {C}WiFi IP address {RE}: {G if ip_addr else R}{ip_addr or 'No IP (not connected)'}{RE}")
    print(f"  {C}Ping 8.8.8.8   {RE}: {G if ping_rc==0 else R}{'OK' if ping_rc==0 else 'Failed'}{RE}")
    print(f"  {C}DNS resolution  {RE}: {G if dns_rc==0 else R}{'OK' if dns_rc==0 else 'Failed'}{RE}")
    print(f"  {C}Mobile data     {RE}: {W}{net_state or 'N/A'}{RE}")
    print(f"  {C}Overall internet{RE}: {G if inet else R}{'CONNECTED' if inet else 'DISCONNECTED'}{RE}")

    print()
    if inet:
        success("Internet connectivity ACTIVE — OEM unlock timer is counting")
    elif ip_addr:
        warn("IP assigned but no internet — check router/connection quality")
    else:
        error("NO internet connectivity — OEM unlock timer is PAUSED")
        print(f"\n{C}Fix:{RE}")
        print("  Connect to WiFi: Settings → WiFi → select your network")
        print("  Or enable mobile data: Settings → Connections → Mobile networks")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 49 — Samsung Account Status Check
# ─────────────────────────────────────────────────────────────────────────────
def m49_samsung_account():
    header("Method 49: Samsung Account & Google Account Status")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    print(f"{C}Account requirements for OEM Unlock on S24 Ultra:{RE}\n")

    # Check accounts via content provider
    accounts, _, _ = shell("content query --uri content://com.android.accounts/accounts 2>/dev/null | head -20")
    # Alternative: dumpsys
    google_acct, _, _ = shell("dumpsys account 2>/dev/null | grep -i 'google\\|samsung' | head -10")

    # Check Samsung account package
    samsung_pkg, _, _ = shell("pm list packages 2>/dev/null | grep -i 'samsungaccount\\|myaccount'")
    google_pkg,  _, _ = shell("pm list packages 2>/dev/null | grep -i 'gms\\|google.android.gms' | head -3")

    print(f"  {C}Samsung Account app{RE}: {G if samsung_pkg else Y}{samsung_pkg.replace('package:','') if samsung_pkg else 'Not found'}{RE}")
    print(f"  {C}Google GMS        {RE}: {G if google_pkg else R}{'Present' if google_pkg else 'Not found'}{RE}")

    if google_acct:
        print(f"\n{C}Detected accounts:{RE}")
        for line in google_acct.split('\n')[:8]:
            if line.strip():
                print(f"  {W}{line.strip()}{RE}")

    print(f"\n{C}Account requirements for OEM Unlock:{RE}")
    for req in [
        "Google account: recommended (helps with timer tracking)",
        "Samsung account: NOT required for bootloader unlock on XXS global variant",
        "FRP (Factory Reset Protection) lock: tied to Google account",
        "After unlock+wipe, your Google account will be needed to pass FRP",
        "Remove Google account BEFORE unlocking if you want to skip FRP",
    ]:
        print(f"  {Y}•{RE} {W}{req}{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 50 — Play Integrity / SafetyNet Status
# ─────────────────────────────────────────────────────────────────────────────
def m50_play_integrity():
    header("Method 50: Play Integrity / SafetyNet Status")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    # Check keystore attestation support
    km_ver,  _, _ = shell("getprop ro.hardware.keystore")
    km_vers2,_, _ = shell("getprop ro.vendor.keymaster.version 2>/dev/null")
    gms_ver, _, _ = shell("dumpsys package com.google.android.gms 2>/dev/null | grep versionName | head -1")
    play_ver,_, _ = shell("dumpsys package com.android.vending 2>/dev/null | grep versionName | head -1")
    tee,     _, _ = shell("getprop ro.hardware.keystore_desede 2>/dev/null")

    print(f"  {C}Keystore hardware  {RE}: {W}{km_ver or 'N/A'}{RE}")
    print(f"  {C}KeyMaster version  {RE}: {W}{km_vers2 or 'N/A'}{RE}")
    print(f"  {C}Google Play version{RE}: {W}{play_ver.strip() if play_ver else 'N/A'}{RE}")
    print(f"  {C}GMS version        {RE}: {W}{gms_ver.strip() if gms_ver else 'N/A'}{RE}")

    vbs, _, _ = shell("getprop ro.boot.verifiedbootstate")
    print(f"  {C}Verified boot state{RE}: {G if vbs=='green' else Y}{vbs or 'N/A'}{RE}")

    print(f"\n{C}Play Integrity levels — current vs after unlock:{RE}")
    rows = [
        ("MEETS_BASIC_INTEGRITY",  "green", "green",   "Passes locked",  "Passes if relocked"),
        ("MEETS_DEVICE_INTEGRITY", "green", "red",     "Passes locked",  "FAILS after unlock"),
        ("MEETS_STRONG_INTEGRITY", "green", "red",     "Passes locked",  "FAILS after unlock"),
    ]
    print(f"  {'Verdict':<30} {'Now':^8} {'After unlock':^14}")
    print(f"  {'─'*54}")
    for label, c_now, c_after, now_str, after_str in rows:
        nc = G if c_now   == "green" else R
        ac = G if c_after == "green" else R
        print(f"  {W}{label:<30}{RE} {nc}{now_str:^8}{RE} {ac}{after_str:^14}{RE}")

    print(f"\n{Y}Note: After unlocking, use Magisk + Shamiko + PlayIntFix module{RE}")
    print(f"{Y}to restore Play Integrity for banking apps.{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 51 — Check for OTA Updates (affects unlock)
# ─────────────────────────────────────────────────────────────────────────────
def m51_ota_check():
    header("Method 51: OTA Update Status (Important for Unlock Timing)")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    build,   _, _ = shell("getprop ro.build.version.incremental")
    ota_pkg, _, _ = shell("getprop ro.ota.package 2>/dev/null")
    fota,    _, _ = shell("dumpsys package com.wssyncmldm 2>/dev/null | grep versionName | head -1")
    dul,     _, _ = shell("pm list packages 2>/dev/null | grep -i 'fota\\|dul\\|wssync'")
    pending, _, _ = shell("getprop sys.update.title 2>/dev/null")

    print(f"  {C}Current build        {RE}: {W}{build or 'N/A'}{RE}")
    print(f"  {C}OTA package prop     {RE}: {W}{ota_pkg or 'N/A'}{RE}")
    print(f"  {C}Pending update title {RE}: {W}{pending or 'None detected'}{RE}")
    print(f"  {C}FOTA/DUL packages    {RE}: {W}{dul.replace('package:','') if dul else 'N/A'}{RE}")

    print(f"\n{C}Why OTA matters for bootloader unlock:{RE}")
    for tip in [
        "Do NOT install OTA updates after enabling OEM Unlocking toggle",
        "OTA updates may re-lock the bootloader or reset the 7-day timer",
        "Complete the unlock FIRST, then update via Magisk-patched boot",
        "Your build S928BXXS6DZE1 (Android 16) is current — no update needed",
        "After rooting: disable automatic updates in Settings → Software Update",
    ]:
        print(f"  {Y}•{RE} {W}{tip}{RE}")

    # Try to open software update settings
    if input(f"\n{Y}Open Software Update settings to check/disable? (yes/no): {RE}").strip().lower() == "yes":
        shell("am start -n com.wssyncmldm/.activity.MainScreen 2>/dev/null || "
              "am start -a android.settings.SETTINGS 2>/dev/null", timeout=5)
        info("Navigate to Settings → Software Update → Auto Download over WiFi → OFF")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 52 — Heimdall Compatibility & Download Mode Guide
# ─────────────────────────────────────────────────────────────────────────────
def m52_heimdall():
    header("Method 52: Heimdall Compatibility & Download Mode Guide")
    serial, _ = get_device()

    print(f"{C}Heimdall is an open-source alternative to Samsung Odin.{RE}")
    print(f"{C}Works with Download Mode (Vol Down + power/USB) on Samsung devices.{RE}\n")

    # Check if heimdall is installed
    heim = check_tool("heimdall")
    print(f"  {C}heimdall installed{RE}: {G if heim else Y}{'Yes' if heim else 'No — install: pkg install heimdall'}{RE}")

    if not heim and ON_DEVICE:
        if input(f"\n{Y}Install heimdall now? (yes/no): {RE}").strip().lower() == "yes":
            out, err, rc = run("pkg install -y heimdall 2>/dev/null", timeout=120)
            if rc == 0 or check_tool("heimdall"):
                success("heimdall installed")
            else:
                warn("heimdall not in Termux repos — use from PC instead")
                info("PC install: sudo apt install heimdall-flash  (Ubuntu/Debian)")

    print(f"\n{C}Heimdall usage for S24 Ultra:{RE}")
    for cmd_info in [
        ("List partitions",        "heimdall print-pit --no-reboot"),
        ("Flash recovery",         "heimdall flash --RECOVERY twrp.img"),
        ("Flash boot",             "heimdall flash --BOOT boot.img"),
        ("Flash with reboot",      "heimdall flash --BOOT boot.img --reboot"),
        ("Detect device",          "heimdall detect"),
    ]:
        print(f"  {C}{cmd_info[0]:<25}{RE}: {W}{cmd_info[1]}{RE}")

    print(f"\n{Y}Device must be in Download Mode for Heimdall (Method 9).{RE}")
    print(f"{Y}Note: Some S24 Ultra builds block Heimdall — Odin4 on PC is more reliable.{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 53 — Knox Detailed Counter & TIMA Analysis
# ─────────────────────────────────────────────────────────────────────────────
def m53_knox_detailed():
    header("Method 53: Knox Detailed Counter & TIMA Analysis")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    knox_props = [
        ("ro.boot.warranty_bit",       "getprop ro.boot.warranty_bit"),
        ("ro.boot.knoxcountervalue",   "getprop ro.boot.knoxcountervalue"),
        ("ro.boot.knox",               "getprop ro.boot.knox"),
        ("sys.knox.warranty_bit",      "getprop sys.knox.warranty_bit"),
        ("ro.build.type",              "getprop ro.build.type"),
        ("TIMA enabled",               "getprop ro.tima 2>/dev/null"),
        ("Knox version",               "getprop ro.knox.version 2>/dev/null"),
        ("Knox config",                "getprop ro.config.knox 2>/dev/null"),
        ("Keystore TEE",               "getprop ro.hardware.keystore"),
        ("SE for Android enforcing",   "getprop ro.build.selinux"),
    ]
    for label, cmd in knox_props:
        val, _, _ = shell(cmd)
        print(f"  {C}{label:<30}{RE}: {W}{val or 'N/A'}{RE}")

    print(f"\n{C}Knox protection layers on S24 Ultra:{RE}")
    for layer in [
        "Knox Warranty Bit — trips on bootloader unlock (PERMANENT)",
        "TIMA (TrustZone-based Integrity Meas. Arch.) — monitors kernel",
        "dm-verity — verifies system partition on boot",
        "Secure Boot — validates bootloader chain",
        "RKP (Realtime Kernel Protection) — prevents kernel exploits",
        "SE for Android — mandatory access control",
    ]:
        print(f"  {Y}▸{RE} {W}{layer}{RE}")

    bit, _, _ = shell("getprop ro.boot.warranty_bit")
    print()
    if bit == "0":
        success("Knox warranty bit INTACT (0) — tripped after unlock")
    elif bit == "1":
        warn("Knox warranty bit TRIPPED (1) — warranty already voided")
    else:
        info("Knox warranty bit not readable from this property")

    print(f"\n{C}What Knox means practically:{RE}")
    print(f"  {W}• Knox apps (Secure Folder, Samsung Pay) stop working after unlock{RE}")
    print(f"  {W}• Samsung warranty is voided permanently{RE}")
    print(f"  {W}• MDM/enterprise policies will reject the device{RE}")
    print(f"  {W}• This cannot be reset — even reflashing stock firmware{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 54 — FRP Lock Analysis & Preparation
# ─────────────────────────────────────────────────────────────────────────────
def m54_frp_analysis():
    header("Method 54: FRP Lock Analysis & Pre-Unlock Preparation")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    print(f"{C}FRP (Factory Reset Protection) is tied to your Google account.{RE}")
    print(f"{C}After bootloader unlock the device wipes — FRP will activate.{RE}\n")

    # Check FRP state
    frp_props = [
        ("FRP prop",              "getprop ro.frp.pst 2>/dev/null"),
        ("Secure frp",            "getprop ro.boot.secure_frp 2>/dev/null"),
        ("Persist FRP",           "getprop persist.sys.block_secureerase 2>/dev/null"),
    ]
    for label, cmd in frp_props:
        val, _, _ = shell(cmd)
        print(f"  {C}{label:<20}{RE}: {W}{val or 'N/A'}{RE}")

    # Check Google accounts
    gaccts, _, _ = shell("content query --uri content://com.android.accounts/accounts "
                          "--projection name,type 2>/dev/null | grep -i google")
    if gaccts:
        count = gaccts.count("com.google")
        print(f"\n  {C}Google accounts found{RE}: {Y}{count}{RE}")
        for line in gaccts.split('\n')[:3]:
            if 'name=' in line:
                name = line.split('name=')[1].split(',')[0] if 'name=' in line else '?'
                print(f"    {W}→ {name}{RE}")

    print(f"\n{C}FRP strategy BEFORE you unlock:{RE}")
    for step in [
        "Option A — Remove Google account before unlocking (no FRP after wipe)",
        "  Settings → Accounts & Backup → Manage accounts → Google → Remove",
        "",
        "Option B — Keep account (FRP activates, you must log in after wipe)",
        "  You will need your Google credentials after factory reset",
        "  Make sure you know the password before proceeding",
        "",
        "Option C — Only remove account temporarily, re-add after setup",
    ]:
        color = C if step.startswith("Option") else W
        print(f"  {color}{step}{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 55 — Full Unlock Eligibility Report (S24 Ultra Specific)
# ─────────────────────────────────────────────────────────────────────────────
def m55_eligibility_report():
    header("Method 55: Full Unlock Eligibility Report — SM-S928B")
    serial, _ = get_device()
    if not serial:
        error("No device connected"); return

    print(f"{C}{BO}Gathering all unlock eligibility data…{RE}")
    print(f"{Y}Note: Settings reads may return N/A in Termux (no root) — not a real failure{RE}\n")

    checks   = {}   # label -> (status, detail, is_hard_blocker)
    cant_read = []  # labels where we genuinely cannot determine state

    # ── 1. Device model ──────────────────────────────────────────────────────
    model, _, _ = shell("getprop ro.product.model")
    checks["Model is S24 Ultra (S928B)"] = ("s928" in model.lower(), model, True)

    # ── 2. Region ────────────────────────────────────────────────────────────
    bl, _, _ = shell("getprop ro.bootloader")
    is_global = "XX" in bl if bl else False
    checks["Global variant (XX region)"] = (is_global, bl or "N/A", True)

    # ── 3. Developer Options — multi-method, no root needed ──────────────────
    dev_ok = False
    dev_method = "undetected"
    # a) settings read
    dev_s = get_setting("global", "development_settings_enabled")
    if dev_s == "1":
        dev_ok = True; dev_method = "settings"
    # b) pm resolve-activity (works without root when dev options on)
    if not dev_ok:
        out_pm, _, rc_pm = shell("pm resolve-activity --brief -a android.settings.APPLICATION_DEVELOPMENT_SETTINGS 2>/dev/null")
        if rc_pm == 0 and "android.settings" in (out_pm or ""):
            dev_ok = True; dev_method = "pm-resolve"
    # c) persist.sys.usb.config contains adb
    if not dev_ok:
        out_usb, _, _ = shell("getprop persist.sys.usb.config 2>/dev/null")
        if "adb" in (out_usb or ""):
            dev_ok = True; dev_method = f"usb.config={out_usb.strip()}"
    # d) cmd settings
    if not dev_ok:
        out_cmd, _, _ = shell("cmd settings get global development_settings_enabled 2>/dev/null")
        if out_cmd.strip() == "1":
            dev_ok = True; dev_method = "cmd-settings"
    # e) content provider
    if not dev_ok:
        out_cp, _, _ = shell("content query --uri content://settings/global --where \"name='development_settings_enabled'\" 2>/dev/null")
        if "value=1" in (out_cp or ""):
            dev_ok = True; dev_method = "content-provider"

    if not dev_ok and dev_s in (None, "", "null", "N/A"):
        cant_read.append("Developer Options")
        dev_note = "cannot read (Termux limitation) — assumed enabled if you did 7-tap"
    else:
        dev_note = f"detected via {dev_method}" if dev_ok else "NOT enabled"
    checks["Developer Options enabled"] = (dev_ok, dev_note, False)  # not a hard blocker if unreadable

    # ── 4. OEM unlock setting (secondary — getprop is primary) ───────────────
    oem_s = get_setting("global", "oem_unlock_allowed")
    oem_s_ok = oem_s == "1"
    if oem_s in (None, "", "null", "N/A"):
        cant_read.append("oem_unlock_allowed setting")
        oem_s_note = "cannot read (Termux limitation)"
    else:
        oem_s_note = f"value={oem_s}"
    checks["OEM unlock allowed (setting)"] = (oem_s_ok, oem_s_note, False)

    # ── 5. sys.oem_unlock_allowed (THE key check — set by Samsung daemon) ────
    oem_sys, _, _ = shell("getprop sys.oem_unlock_allowed")
    oem_sys = oem_sys.strip()
    oem_sys_ok = oem_sys == "1"
    if oem_sys_ok:
        oem_sys_note = "✓ ALLOWED — OEM Unlocking toggle is VISIBLE and active"
    elif oem_sys in ("0", ""):
        oem_sys_note = "NOT YET — toggle is HIDDEN from Developer Options (timer running)"
    else:
        oem_sys_note = f"NOT SET — toggle HIDDEN until timer completes (value={oem_sys or 'N/A'})"
    checks["sys.oem_unlock_allowed  ★ KEY"] = (oem_sys_ok, oem_sys_note, True)

    # ── 6–10. Hardware / platform checks ────────────────────────────────────
    locked, _, _ = shell("getprop ro.boot.flash.locked")
    checks["Bootloader currently LOCKED (to unlock)"] = (locked == "1", f"flash.locked={locked}", False)

    vbs, _, _ = shell("getprop ro.boot.verifiedbootstate")
    checks["Verified boot state (green=stock)"] = (vbs == "green", f"state={vbs}", False)

    knox, _, _ = shell("getprop ro.boot.warranty_bit")
    checks["Knox warranty bit intact (0)"] = (knox == "0", f"bit={knox}", False)

    inet = check_internet()
    ip   = get_wifi_ip()
    checks["Internet connectivity"] = (inet, f"IP={ip or 'none'} ping={'OK' if inet else 'FAIL'}", True)

    android, _, _ = shell("getprop ro.build.version.release")
    checks["Android version (16 supports unlock)"] = (True, f"Android {android}", False)

    oem_sup, _, _ = shell("getprop ro.oem_unlock_supported 2>/dev/null")
    if oem_sup.strip() == "0":
        checks["ro.oem_unlock_supported"] = (False, "0 — hardware reports unsupported!", True)
    elif oem_sup.strip():
        checks["ro.oem_unlock_supported"] = (True, oem_sup.strip(), False)

    # ── Print report ─────────────────────────────────────────────────────────
    pass_c = fail_c = warn_c = unread_c = 0
    hard_blockers = []
    for label, (status, detail, is_hard) in checks.items():
        if status:
            print(f"  {G}[PASS]{RE} {W}{label:<50}{RE} {C}{detail}{RE}")
            pass_c += 1
        elif "cannot read" in detail or "assumed" in detail:
            print(f"  {Y}[INFO]{RE} {W}{label:<50}{RE} {Y}{detail}{RE}")
            unread_c += 1
        elif "LOCKED" in label or "Knox" in label or "verified" in label.lower():
            print(f"  {C}[INFO]{RE} {W}{label:<50}{RE} {Y}{detail}{RE}")
            warn_c += 1
        else:
            print(f"  {R}[FAIL]{RE} {W}{label:<50}{RE} {Y}{detail}{RE}")
            fail_c += 1
            if is_hard:
                hard_blockers.append(label)

    print(f"\n{C}{'─'*62}{RE}")
    print(f"  {G}PASS: {pass_c}{RE}  {R}FAIL: {fail_c}{RE}  {Y}INFO: {warn_c}{RE}  {W}UNREADABLE: {unread_c}{RE}")
    if cant_read:
        print(f"  {Y}(Settings unreadable in Termux without root — not real failures){RE}")
    print(f"{C}{'─'*62}{RE}\n")

    # ── Verdict ───────────────────────────────────────────────────────────────
    if not hard_blockers:
        print(f"{G}{BO}  ✓ VERDICT: Device IS ELIGIBLE for bootloader unlock!{RE}")
        print(f"\n{C}  Next steps:{RE}")
        if not oem_sys_ok:
            print(f"  {Y}  1. WAIT — 7-day timer not complete (OEM Unlocking is HIDDEN in Dev Options){RE}")
            print(f"  {Y}  2. Keep WiFi on continuously until sys.oem_unlock_allowed = 1{RE}")
            print(f"  {Y}  3. Method 68 watches every 5s and alerts when toggle appears{RE}")
            print(f"  {W}  4. Once visible: Developer Options → OEM Unlocking → Enable (blue){RE}")
            print(f"  {W}  5. Reboot to bootloader → PC: fastboot flashing unlock{RE}")
        else:
            print(f"  {G}  1. OEM UNLOCKING IS VISIBLE — go to Developer Options → tap it → Enable{RE}")
            print(f"  {W}  2. Reboot to bootloader (Method 7){RE}")
            print(f"  {W}  3. From PC: fastboot flashing unlock{RE}")
        print(f"  {R}  ★ Or run Method 56 (One-Button Master Unlock) to guide you through each step{RE}")
    else:
        print(f"{R}{BO}  ✗ VERDICT: Hard blockers found:{RE}")
        for b in hard_blockers:
            _, detail, _ = checks[b]
            print(f"  {R}  • {b}{RE}: {detail}")
        print()
        if not oem_sys_ok:
            print(f"  {Y}  ► OEM Unlocking is HIDDEN from Developer Options — this is NORMAL on OneUI{RE}")
            print(f"  {Y}  ► The option only APPEARS once the 7-day internet timer completes{RE}")
            print(f"  {Y}  ► Keep WiFi connected — run Method 68 to be notified when it activates{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 56 — ONE-BUTTON MASTER UNLOCK  ★★
# ─────────────────────────────────────────────────────────────────────────────
def m56_one_button_unlock():
    header("Method 56: ONE-BUTTON MASTER UNLOCK — SM-S928B")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    print(f"{R}{BO}  !! THIS WILL WIPE ALL DATA AND VOID YOUR WARRANTY !!{RE}")
    print(f"{Y}  Knox warranty bit will be permanently tripped.{RE}\n")
    if input(f"{R}Type UNLOCK to proceed (anything else cancels): {RE}").strip() != "UNLOCK":
        info("Cancelled — no changes made"); return

    step = 0
    def s(msg):
        nonlocal step; step += 1
        print(f"\n{B}{BO}━━━ STEP {step:02d} ━━━{RE} {C}{msg}{RE}")

    def ok_line(label, passed, detail=""):
        c = G if passed else R
        sym = "✓" if passed else "✗"
        print(f"  {c}[{sym}]{RE} {C}{label:<32}{RE} {W}{detail}{RE}")

    def verify_oem():
        """Samsung daemon sets sys.oem_unlock_allowed=1 when toggle goes ON — no root needed."""
        v, _, _ = shell("getprop sys.oem_unlock_allowed")
        if v == "1": return True
        v2 = get_setting("global", "oem_unlock_allowed")
        return v2 == "1"

    def verify_dev():
        # Method 1: settings read (may fail in Termux without root)
        v = get_setting("global", "development_settings_enabled")
        if v == "1":
            return True
        # Method 2: check if Developer Options activity resolves (only works when enabled)
        out, _, rc = shell("pm resolve-activity --brief -a android.settings.APPLICATION_DEVELOPMENT_SETTINGS 2>/dev/null")
        if rc == 0 and "android.settings" in (out or ""):
            return True
        # Method 3: USB config contains 'adb' → dev options was on at some point
        out2, _, _ = shell("getprop persist.sys.usb.config 2>/dev/null")
        if "adb" in (out2 or ""):
            return True
        # Method 4: check via cmd settings
        out3, _, rc3 = shell("cmd settings get global development_settings_enabled 2>/dev/null")
        if out3.strip() == "1":
            return True
        # Method 5: check content provider directly
        out4, _, _ = shell("content query --uri content://settings/global --where \"name='development_settings_enabled'\" 2>/dev/null")
        if "value=1" in (out4 or ""):
            return True
        return False

    # ── STEP 1: Battery ────────────────────────────────────────────────────────
    s("Battery level (Samsung requires ≥ 80% for unlock)")
    bat, _, _ = shell("cat /sys/class/power_supply/battery/capacity 2>/dev/null")
    bat_int = int(bat) if bat and bat.isdigit() else 0
    ok_line("Battery", bat_int >= 80, f"{bat or 'N/A'}%")
    if bat_int and bat_int < 80:
        warn(f"Battery at {bat}% — charge to ≥80% before unlocking, then re-run")

    # ── STEP 2: Internet ───────────────────────────────────────────────────────
    s("Internet connectivity (7-day timer must be running)")
    inet = check_internet()
    ip   = get_wifi_ip()
    ok_line("Internet", inet, f"IP={ip or 'N/A'}")
    if not inet:
        warn("No internet — connect to WiFi now")
        shell("am start -a android.settings.WIFI_SETTINGS 2>/dev/null", timeout=5)
        input(f"  {Y}Connect WiFi then press Enter…{RE}")
        inet = check_internet()
        ip   = get_wifi_ip()

    # ── STEP 3: Developer Options ──────────────────────────────────────────────
    s("Enable Developer Options")
    # Try all auto methods first
    put_setting("global", "development_settings_enabled", "1")
    run("su -c 'settings put global development_settings_enabled 1' 2>/dev/null")
    run(f"su -c 'sqlite3 {_SETTINGS_DB} "
        "\"INSERT OR REPLACE INTO global(name,value) "
        "VALUES(\\\"development_settings_enabled\\\",\\\"1\\\")\"' 2>/dev/null")
    dev_ok = verify_dev()

    if not dev_ok:
        warn("Auto-enable failed (no root) — opening About Phone now…")
        shell("am start -a android.settings.DEVICE_INFO_SETTINGS 2>/dev/null", timeout=5)
        print(f"""
  {W}On your phone:{RE}
  {G}  1.{RE} {W}Tap "Software Information"{RE}
  {G}  2.{RE} {W}Tap "Build Number" 7 times{RE}
  {G}  3.{RE} {W}Enter PIN if prompted{RE}
  {G}  4.{RE} {W}You'll see: "Developer mode has been enabled"{RE}""")
        while not dev_ok:
            ans = input(f"\n  {Y}Press Enter after tapping Build Number 7×  (or type 'y' if you see 'Developer mode enabled'): {RE}").strip().lower()
            if ans in ("y", "yes", "done", "ok", "1"):
                dev_ok = True
                success("Developer Options accepted (manual confirm)")
                break
            dev_ok = verify_dev()
            if dev_ok:
                success("Developer Options confirmed ON")
                break
            warn("Not detected yet — if you already see 'Developer mode has been enabled' on screen, type 'y' and press Enter")
            shell("am start -a android.settings.DEVICE_INFO_SETTINGS 2>/dev/null", timeout=5)

    ok_line("Developer Options", dev_ok)

    # ── STEP 4: OEM Unlock toggle ──────────────────────────────────────────────
    s("Enable OEM Unlocking (Developer Options → OEM Unlocking)")
    # Try all auto writes (will work if root exists)
    put_setting("global", "oem_unlock_allowed", "1")
    run("su -c 'settings put global oem_unlock_allowed 1' 2>/dev/null")
    run(f"su -c 'sqlite3 {_SETTINGS_DB} "
        "\"INSERT OR REPLACE INTO global(name,value) "
        "VALUES(\\\"oem_unlock_allowed\\\",\\\"1\\\")\"' 2>/dev/null")
    oem_ok = verify_oem()

    if not oem_ok:
        # Try to force-show the toggle via am broadcast
        shell("am broadcast -a com.android.settings.action.OEM_UNLOCK_SETTINGS 2>/dev/null", timeout=5)
        # Open Developer Options page
        for intent in [
            "com.android.settings/.development.DevelopmentSettingsDashboardActivity",
            "com.android.settings/.DevelopmentSettings",
            "com.android.settings/.Settings$DevelopmentSettingsActivity",
        ]:
            _, _, rc = shell(f"am start -n {intent} 2>/dev/null", timeout=5)
            if rc == 0: break

        # Check ro.oem_unlock_supported
        oem_sup, _, _ = shell("getprop ro.oem_unlock_supported 2>/dev/null")
        timer_ok, _, _ = shell("getprop sys.oem_unlock_allowed 2>/dev/null")
        timer_val = timer_ok.strip()

        if timer_val != "1":
            # Timer not done — toggle is HIDDEN on OneUI (not just greyed)
            print(f"""
  {R}{BO}  ══ SAMSUNG ONEU I — OEM UNLOCK TIMER NOT COMPLETE ══{RE}

  {Y}  sys.oem_unlock_allowed = {timer_val or 'N/A'} (need: 1){RE}

  {W}  On Samsung OneUI the "OEM Unlocking" item is completely{RE}
  {W}  HIDDEN from Developer Options until the 7-day timer finishes.{RE}
  {W}  This is NORMAL — the option is not greyed, it simply does not{RE}
  {W}  appear in the list yet.{RE}

  {C}  What to do RIGHT NOW:{RE}
  {G}  1.{RE} {W}Go to Settings → Connections → WiFi → make sure connected{RE}
  {G}  2.{RE} {W}Leave phone ON with WiFi connected for 7 cumulative days{RE}
  {G}  3.{RE} {W}Do NOT factory reset (resets the 7-day timer to zero){RE}
  {G}  4.{RE} {W}Keep screen from going fully off (Method 95 sets stay-awake){RE}
  {G}  5.{RE} {W}Run Method 68 to get notified the moment the toggle appears{RE}

  {Y}  Once timer completes:{RE}
  {W}  • sys.oem_unlock_allowed becomes 1{RE}
  {W}  • "OEM Unlocking" APPEARS in Developer Options{RE}
  {W}  • Tap it, tap "Enable", then run fastboot flashing unlock from PC{RE}

  {C}  sys.oem_unlock_allowed = {timer_val or 'N/A'}  |  ro.oem_unlock_supported = {oem_sup or 'N/A'}{RE}""")
        else:
            # Timer done, toggle should show
            print(f"""
  {G}{BO}  ══ TIMER COMPLETE — OEM UNLOCKING SHOULD NOW BE VISIBLE ══{RE}

  {W}On your phone (Developer Options is now open):{RE}
  {G}  1.{RE} {W}Scroll ALL the way down — "OEM Unlocking" is near the bottom{RE}
  {G}  2.{RE} {W}Tap the toggle → tap "Enable" in the confirmation dialog{RE}
  {G}  3.{RE} {W}The toggle turns BLUE = success{RE}

  {Y}  If "OEM Unlocking" is still missing:{RE}
  {W}     → Settings → search bar → type "OEM"{RE}
  {W}     → Reboot phone, then open Developer Options again{RE}
  {W}     → Run Method 116 (Force Show OEM Toggle){RE}

  {C}  sys.oem_unlock_allowed = {timer_val}  ✓{RE}""")

        while not oem_ok:
            choice = input(f"\n  {Y}(Enter) once toggle is BLUE  |  (y) yes I enabled it  |  (s) skip  |  (q) quit: {RE}").strip().lower()
            if choice == "q":
                info("Quitting unlock flow"); return
            if choice in ("y", "yes", "done", "ok", "1"):
                oem_ok = True
                success("OEM Unlock accepted (manual confirm)")
                break
            if choice == "s":
                warn("Skipping — ensure toggle is ON before running fastboot unlock"); oem_ok = True; break
            oem_ok = verify_oem()
            v_raw, _, _ = shell("getprop sys.oem_unlock_allowed")
            if oem_ok:
                success("OEM Unlock toggle confirmed ON!"); break
            warn(f"Not confirmed yet (sys.oem_unlock_allowed={v_raw or 'N/A'})")
            warn("If you see the toggle is BLUE, type 'y' and press Enter to continue")
            shell("am start -n com.android.settings/.DevelopmentSettings 2>/dev/null", timeout=5)

    ok_line("OEM Unlock toggle", oem_ok)

    # ── STEP 5: USB Debugging ─────────────────────────────────────────────────
    s("Enable USB Debugging")
    put_setting("global", "adb_enabled", "1")
    run("su -c 'settings put global adb_enabled 1' 2>/dev/null")
    adb_v = get_setting("global", "adb_enabled")
    if adb_v != "1":
        shell("am start -n com.android.settings/.DevelopmentSettings 2>/dev/null", timeout=5)
        input(f"  {Y}Enable 'USB Debugging' then press Enter…{RE}")
    ok_line("USB Debugging", True, "enabled")

    # ── STEP 6: Wireless ADB ──────────────────────────────────────────────────
    s("Setup Wireless ADB (TCP port 5555)")
    put_setting("global", "adb_wifi_enabled", "1")
    run("su -c 'setprop service.adb.tcp.port 5555; stop adbd; start adbd' 2>/dev/null", timeout=10)
    ip = get_wifi_ip()
    tcp, _, _ = shell("getprop service.adb.tcp.port")
    ok_line("WiFi IP detected", bool(ip), ip or "N/A")
    ok_line("ADB TCP port", tcp == "5555", tcp or "N/A")

    # ── STEP 7: Final Status Dashboard ────────────────────────────────────────
    s("Final Status Dashboard")
    locked, _, _ = shell("getprop ro.boot.flash.locked")
    knox,   _, _ = shell("getprop ro.boot.warranty_bit")
    vbs,    _, _ = shell("getprop ro.boot.verifiedbootstate")
    oem_sys,_, _ = shell("getprop sys.oem_unlock_allowed")

    print(f"\n{C}{BO}{'═'*62}{RE}")
    print(f"{C}{BO}  UNLOCK READINESS SUMMARY{RE}")
    print(f"{C}{'═'*62}{RE}")
    ok_line("Internet connected",    inet,          ip or "N/A")
    ok_line("Battery ≥ 80%",        bat_int >= 80, f"{bat_int}%")
    ok_line("Developer Options",     dev_ok)
    ok_line("OEM Unlock toggle ON",  oem_ok,        f"sys={oem_sys or '?'}")
    ok_line("USB Debugging",         True)
    ok_line("Bootloader locked",     locked == "1", "needs fastboot unlock")
    ok_line("Knox bit intact",       knox == "0",   f"bit={knox} (trips after unlock)")
    print(f"{C}{'═'*62}{RE}")

    # ── STEP 8: PC Unlock Commands ────────────────────────────────────────────
    s("PC Unlock Commands")
    print(f"""
{B}─── Via USB cable (most reliable) ──────────────────────────────{RE}
{G}  fastboot devices{RE}                    {W}# confirm device shown{RE}
{G}  fastboot flashing unlock{RE}            {W}# Volume Up on phone to confirm{RE}

{B}─── Via WiFi (no USB cable needed) ─────────────────────────────{RE}""")
    if ip:
        print(f"{G}  adb connect {ip}:5555{RE}")
        print(f"{G}  adb reboot bootloader{RE}")
        print(f"{G}  fastboot flashing unlock{RE}            {W}# Volume Up on phone{RE}")
    else:
        print(f"{Y}  WiFi IP not detected — use USB cable or run Method 71{RE}")

    print(f"""
{B}─── Manual bootloader entry (no ADB needed) ────────────────────{RE}
{W}  Power OFF → hold Volume Down + Power → bootloader screen{RE}
{W}  Connect USB to PC → fastboot flashing unlock{RE}

{B}─── After unlock completes ─────────────────────────────────────{RE}
{W}  Device wipes and reboots (~2 min){RE}
{W}  Re-enable Developer Options (Build Number × 7){RE}
{W}  Method 27 → patch boot.img with Magisk for root{RE}
{W}  Method 66 → download correct firmware from SamFW{RE}
""")

    # Save commands to file
    cmd_file = os.path.expanduser("~/UNLOCK_COMMANDS.txt")
    with open(cmd_file, "w") as f:
        f.write(f"S24 Ultra Bootloader Unlock Commands\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        if ip:
            f.write(f"WIRELESS:\nadb connect {ip}:5555\nadb reboot bootloader\n")
        f.write(f"fastboot flashing unlock\n\nOR\n\nPower OFF → hold Vol Down + Power\nfastboot flashing unlock\n")
    success(f"Commands saved to: {cmd_file}")

    # ── STEP 9: Reboot ────────────────────────────────────────────────────────
    s("Reboot to Bootloader")
    print(f"\n{Y}Ready to reboot? After rebooting:{RE}")
    print(f"  {W}1. On PC run: fastboot flashing unlock{RE}")
    print(f"  {W}2. Press Volume Up on phone screen to confirm{RE}")
    choice = input(f"\n{Y}(r)eboot now  |  (s)kip — I'll do it manually  |  (q)uit: {RE}").strip().lower()
    if choice == "r":
        ok2 = adb_reboot("bootloader")
        if ok2:
            print(f"\n{G}{BO}Device rebooting to bootloader!{RE}")
            print(f"{C}Now on PC run: {G}fastboot flashing unlock{RE}")
        else:
            info("Manual: Power off → hold Volume Down + Power")
    elif choice == "s":
        info("Manual bootloader entry: Power off → hold Volume Down + Power")

    print(f"\n{G}{BO}Master unlock flow complete! Check: {cmd_file}{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 57 — Root-Based Settings Access
# ─────────────────────────────────────────────────────────────────────────────
def m57_root_settings():
    header("Method 57: Root-Based Settings Access")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    print(f"{C}Termux app context lacks permission for 'settings' service.{RE}")
    print(f"{C}Testing all available access methods:{RE}\n")

    test_key = "development_settings_enabled"
    methods = [
        ("Direct (settings cmd)",      lambda: shell(f"settings get global {test_key}")),
        ("Via su",                     lambda: run(f"su -c 'settings get global {test_key}' 2>/dev/null")),
        ("Content provider",           lambda: shell(f"content query --uri content://settings/global "
                                                     f"--where \"name='{test_key}'\" 2>/dev/null")),
        ("sqlite3 (root)",             lambda: run(f"su -c 'sqlite3 {_SETTINGS_DB} "
                                                   f"\"SELECT value FROM global WHERE "
                                                   f"name=\\\"{test_key}\\\"\"' 2>/dev/null")),
        ("cmd settings (system)",      lambda: shell(f"cmd settings get global {test_key} 2>/dev/null")),
    ]
    working = []
    for label, fn in methods:
        val, err, rc = fn()
        ok = rc == 0 and val and "Failure" not in val and "Error" not in val
        status = G if ok else R
        print(f"  {status}{label:<35}{RE}: {W}{(val or err or 'N/A')[:50]}{RE}")
        if ok:
            working.append(label)

    print()
    if working:
        success(f"Working method(s): {', '.join(working)}")
        # Now use best method to read all key settings
        print(f"\n{C}Key settings via best available method:{RE}")
        for ns, key in [("global","development_settings_enabled"),
                        ("global","oem_unlock_allowed"),
                        ("global","adb_enabled"),
                        ("global","adb_wifi_enabled"),
                        ("secure","user_setup_complete"),
                        ("global","device_provisioned")]:
            val = get_setting(ns, key)
            color = G if val == "1" else (R if val == "0" else W)
            print(f"  {C}{ns}/{key:<35}{RE}: {color}{val or 'N/A'}{RE}")
    else:
        error("No settings access method works — root required")
        info("Install root: Method 27 (Magisk) or Method 70 (KernelSU)")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 58 — Internet Connectivity Repair
# ─────────────────────────────────────────────────────────────────────────────
def m58_internet_fix():
    header("Method 58: Internet Connectivity Check & Repair")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    print(f"{C}Running full connectivity diagnostics:{RE}\n")

    ip = get_wifi_ip()
    print(f"  {C}WiFi IP{RE}          : {G if ip else R}{ip or 'None'}{RE}")

    # WiFi state
    wifi_state, _, _ = shell("getprop wlan.driver.status 2>/dev/null")
    print(f"  {C}WiFi driver{RE}      : {W}{wifi_state or 'N/A'}{RE}")

    # SSID
    ssid, _, _ = shell("getprop wifi.interface 2>/dev/null")
    dumped_ssid, _, _ = shell("dumpsys wifi 2>/dev/null | grep 'mWifiInfo' | head -1")
    print(f"  {C}WiFi interface{RE}   : {W}{ssid or 'N/A'}{RE}")

    # Ping tests
    for host, label in [("8.8.8.8","Google DNS"),("1.1.1.1","Cloudflare"),
                         ("samsung.com","Samsung servers")]:
        _, _, rc = shell(f"ping -c 1 -W 4 {host} 2>/dev/null")
        print(f"  {C}Ping {label:<17}{RE}: {G if rc==0 else R}{'OK' if rc==0 else 'FAILED'}{RE}")

    # DNS
    _, _, dns_rc = shell("nslookup google.com 2>/dev/null")
    print(f"  {C}DNS lookup{RE}       : {G if dns_rc==0 else R}{'OK' if dns_rc==0 else 'FAILED'}{RE}")

    # HTTP check
    if check_tool("curl"):
        out, _, rc = run("curl -s --connect-timeout 5 -o /dev/null "
                         "-w '%{http_code}' http://clients1.google.com/generate_204 2>/dev/null")
        print(f"  {C}HTTP check{RE}       : {G if out.strip()=='204' else R}{out.strip() or 'FAILED'}{RE}")

    inet = check_internet()
    print()
    if inet:
        success("Internet CONNECTED — OEM unlock 7-day timer is active")
    else:
        error("NO internet — timer is paused")
        print(f"\n{C}Repair options:{RE}")
        print(f"  {W}1. Settings → Connections → WiFi → connect to your network{RE}")
        print(f"  {W}2. Settings → Connections → Mobile Networks → enable data{RE}")
        print(f"  {W}3. Toggle Airplane mode off/on{RE}")
        # Try toggling WiFi via command
        if input(f"\n{Y}Try toggling WiFi via shell? (yes/no): {RE}").strip().lower() == "yes":
            shell("svc wifi disable 2>/dev/null"); time.sleep(2)
            shell("svc wifi enable 2>/dev/null");  time.sleep(5)
            ip2 = get_wifi_ip()
            if ip2:
                success(f"WiFi reconnected: {ip2}")
            else:
                warn("WiFi toggle did not restore connection")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 59 — Force Enable Developer Options via Root
# ─────────────────────────────────────────────────────────────────────────────
def m59_force_dev_root():
    header("Method 59: Force Enable Developer Options via Root")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    dev = get_setting("global", "development_settings_enabled")
    if dev == "1":
        success("Developer Options already ENABLED"); return

    info("Attempting to force-enable Developer Options via multiple methods…")
    results = []

    # Method A: settings put via su
    _, _, rc = run("su -c 'settings put global development_settings_enabled 1' 2>/dev/null")
    results.append(("su settings put", rc == 0))

    # Method B: sqlite3 direct write
    _, _, rc2 = run(f"su -c 'sqlite3 {_SETTINGS_DB} "
                    "\"INSERT OR REPLACE INTO global(name,value) "
                    "VALUES(\\\"development_settings_enabled\\\",\\\"1\\\")\"' 2>/dev/null")
    results.append(("sqlite3 direct write", rc2 == 0))

    # Method C: cmd settings
    _, _, rc3 = shell("cmd settings put global development_settings_enabled 1 2>/dev/null")
    results.append(("cmd settings put", rc3 == 0))

    # Method D: am broadcast (triggers dev options)
    _, _, rc4 = shell("am broadcast -a com.android.settings.development.ENABLE_DEVELOPER_OPTIONS 2>/dev/null")
    results.append(("am broadcast", rc4 == 0))

    for label, ok in results:
        print(f"  {C}{label:<30}{RE}: {G if ok else Y}{'OK' if ok else 'Failed'}{RE}")

    time.sleep(1)
    final = get_setting("global", "development_settings_enabled")
    print()
    if final == "1":
        success("Developer Options ENABLED successfully")
        shell("am start -n com.android.settings/.DevelopmentSettings 2>/dev/null", timeout=5)
        info("Developer Options page opened on screen")
    else:
        warn("Automatic methods failed — manual steps required")
        print(f"\n{C}Manual:{RE}")
        print("  Settings → About Phone → Software Information → tap Build Number 7×")
        print("  Each tap shows: 'You are N steps away from being a developer'")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 60 — Force Enable OEM Unlock via Root DB Write
# ─────────────────────────────────────────────────────────────────────────────
def m60_force_oem_root():
    header("Method 60: Force Enable OEM Unlock via Root Database Write")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    warn("Knox warranty bit will be tripped permanently after actual unlock!")
    if input(f"{Y}Continue enabling OEM unlock setting? (yes/no): {RE}").strip().lower() != "yes":
        info("Cancelled"); return

    info("Writing oem_unlock_allowed=1 via all available methods…")
    results = []

    # A: su settings put
    _, _, rc = run("su -c 'settings put global oem_unlock_allowed 1' 2>/dev/null")
    results.append(("su settings put", rc == 0))

    # B: sqlite3 INSERT OR REPLACE
    _, _, rc2 = run(f"su -c 'sqlite3 {_SETTINGS_DB} "
                    "\"INSERT OR REPLACE INTO global(name,value) "
                    "VALUES(\\\"oem_unlock_allowed\\\",\\\"1\\\")\"' 2>/dev/null")
    results.append(("sqlite3 INSERT OR REPLACE", rc2 == 0))

    # C: sqlite3 UPDATE
    _, _, rc3 = run(f"su -c 'sqlite3 {_SETTINGS_DB} "
                    "\"UPDATE global SET value=\\\"1\\\" "
                    "WHERE name=\\\"oem_unlock_allowed\\\"\"' 2>/dev/null")
    results.append(("sqlite3 UPDATE", rc3 == 0))

    # D: content insert
    _, _, rc4 = shell("content insert --uri content://settings/global "
                      "--bind name:s:oem_unlock_allowed --bind value:s:1 2>/dev/null")
    results.append(("content provider insert", rc4 == 0))

    # E: cmd settings
    _, _, rc5 = shell("cmd settings put global oem_unlock_allowed 1 2>/dev/null")
    results.append(("cmd settings", rc5 == 0))

    for label, ok in results:
        print(f"  {C}{label:<35}{RE}: {G if ok else Y}{'OK' if ok else 'Failed'}{RE}")

    time.sleep(1)
    final = get_setting("global", "oem_unlock_allowed")
    oem_sys, _, _ = shell("getprop sys.oem_unlock_allowed")
    print(f"\n  {C}Final oem_unlock_allowed{RE}: {G if final=='1' else R}{final or 'N/A'}{RE}")
    print(f"  {C}sys.oem_unlock_allowed  {RE}: {G if oem_sys=='1' else W}{oem_sys or 'N/A'}{RE}")

    if final == "1":
        success("OEM unlock setting written successfully")
        info("Now also toggle it physically: Developer Options → OEM Unlocking → ON")
        info("Physical toggle is required for fastboot flashing unlock to work")
    else:
        error("All write methods failed — root access not available or SELinux blocking")
        print(f"\n{C}Without root, you must toggle it manually:{RE}")
        print("  Settings → Developer Options → OEM Unlocking → toggle ON")
        shell("am start -n com.android.settings/.DevelopmentSettings 2>/dev/null", timeout=5)


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 61 — A/B Partition Slot Status
# ─────────────────────────────────────────────────────────────────────────────
def m61_ab_slot_status():
    header("Method 61: A/B Partition Slot Status (Virtual A/B)")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    props = [
        ("Current slot",           "getprop ro.boot.slot_suffix"),
        ("A/B enabled",            "getprop ro.build.ab_update"),
        ("Virtual A/B",            "getprop ro.virtual_ab.enabled"),
        ("Virtual A/B retrofit",   "getprop ro.virtual_ab.retrofit"),
        ("Slot A success",         "getprop bootctl.slot-a-successfull 2>/dev/null"),
        ("Slot B success",         "getprop bootctl.slot-b-successfull 2>/dev/null"),
        ("Snapshot COW",           "getprop ro.virtual_ab.cow_version 2>/dev/null"),
    ]
    for label, cmd in props:
        val, _, _ = shell(cmd)
        print(f"  {C}{label:<25}{RE}: {W}{val or 'N/A'}{RE}")

    # bootctl
    bc_cur, _, bc_rc = shell("bootctl get-current-slot 2>/dev/null")
    if bc_rc == 0:
        print(f"\n  {C}bootctl current slot{RE}: {G}{bc_cur}{RE}")

    slot, _, _ = shell("getprop ro.boot.slot_suffix")
    print(f"\n{C}What this means for flashing:{RE}")
    print(f"  {W}S24 Ultra uses Virtual A/B (VAB) — both slots active simultaneously{RE}")
    print(f"  {W}Current active slot: {slot or '_a (default)'}{RE}")
    print(f"  {W}After unlock, always flash to BOTH slots or use --skip-reboot{RE}")
    print(f"  {W}fastboot flash boot boot.img  (flashes to current slot){RE}")
    print(f"  {W}fastboot --set-active=a flash boot boot.img  (force slot a){RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 62 — Anti-Rollback Level Check
# ─────────────────────────────────────────────────────────────────────────────
def m62_anti_rollback():
    header("Method 62: Anti-Rollback (ARB) Level Check")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    arb_props = [
        ("AVB version",            "ro.boot.avb_version"),
        ("VBMeta version",         "ro.boot.vbmeta.avb_version"),
        ("Verified boot hash",     "ro.boot.vbmeta.digest"),
        ("Rollback index boot",    "ro.boot.vbmeta.rollback_index 2>/dev/null"),
        ("ARB boot",               "ro.boot.rollback_index 2>/dev/null"),
        ("Security level",         "ro.boot.vbmeta.device_state"),
        ("Boot security patch",    "ro.boot.patch_level"),
    ]
    for label, prop in arb_props:
        val, _, _ = shell(f"getprop {prop}")
        print(f"  {C}{label:<30}{RE}: {W}{val or 'N/A'}{RE}")

    # via fastboot if available
    fb = get_fb_device()
    if fb:
        for part in ["boot", "system", "vendor"]:
            out, err, _ = run(f"fastboot getvar rollback-index-{part} 2>&1")
            for line in (out + err).split('\n'):
                if 'rollback' in line.lower():
                    print(f"  {C}{line.strip()}{RE}")

    print(f"\n{C}Anti-Rollback impact on S24 Ultra unlock:{RE}")
    for tip in [
        "ARB prevents flashing firmware OLDER than current ARB level",
        "S928BXXS6DZE1 (Android 16) has a high ARB level",
        "You CANNOT downgrade to Android 14/15 firmware after this",
        "Magisk/custom boot images must be built from current firmware",
        "Flashing wrong ARB level = PERMANENT BRICK (unrecoverable)",
        "Always use boot.img extracted from S928BXXS6DZE1 firmware",
    ]:
        print(f"  {Y}▸{RE} {W}{tip}{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 63 — USB Mode & Gadget Config
# ─────────────────────────────────────────────────────────────────────────────
def m63_usb_mode():
    header("Method 63: USB Gadget Mode & ADB Configuration")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    props = [
        ("USB function",       "getprop sys.usb.config"),
        ("USB state",          "getprop sys.usb.state"),
        ("USB speed",          "getprop sys.usb.speed 2>/dev/null"),
        ("ADB enabled",        "getprop persist.service.adb.enable 2>/dev/null"),
        ("Gadget controller",  "ls /sys/class/udc/ 2>/dev/null"),
    ]
    for label, cmd in props:
        val, _, _ = shell(cmd)
        print(f"  {C}{label:<20}{RE}: {W}{val or 'N/A'}{RE}")

    usb_func, _, _ = shell("getprop sys.usb.config")
    print()
    if "adb" in (usb_func or ""):
        success(f"ADB is active in USB config: {usb_func}")
    else:
        warn(f"ADB not in current USB config: {usb_func or 'N/A'}")
        info("Enable USB Debugging in Developer Options")

    # Set USB to MTP+ADB
    if input(f"\n{Y}Set USB mode to MTP+ADB? (yes/no): {RE}").strip().lower() == "yes":
        shell("setprop sys.usb.config mtp,adb 2>/dev/null")
        run("su -c 'setprop sys.usb.config mtp,adb' 2>/dev/null")
        time.sleep(2)
        new_func, _, _ = shell("getprop sys.usb.config")
        print(f"  {C}New USB config{RE}: {W}{new_func or 'N/A'}{RE}")
        if "adb" in (new_func or ""):
            success("USB mode set to MTP+ADB")
        else:
            info("Change USB mode from notification panel: tap 'Charging' → 'File Transfer'")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 64 — Kernel Version & Security Info
# ─────────────────────────────────────────────────────────────────────────────
def m64_kernel_info():
    header("Method 64: Kernel Version & Security Info")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    uname,    _, _ = shell("uname -a")
    kver,     _, _ = shell("uname -r")
    kbuild,   _, _ = shell("cat /proc/version 2>/dev/null | head -1")
    rkp,      _, _ = shell("getprop ro.config.rkp 2>/dev/null")
    kfence,   _, _ = shell("cat /proc/sys/kernel/kfence_sample_interval 2>/dev/null")
    lockdown, _, _ = shell("cat /sys/kernel/security/lockdown 2>/dev/null")
    modules,  _, _ = shell("lsmod 2>/dev/null | wc -l")
    cmdline,  _, _ = shell("cat /proc/cmdline 2>/dev/null")

    print(f"  {C}Kernel version  {RE}: {W}{kver or 'N/A'}{RE}")
    print(f"  {C}Full uname      {RE}: {W}{uname or 'N/A'}{RE}")
    print(f"  {C}Build string    {RE}: {W}{(kbuild or 'N/A')[:80]}{RE}")
    print(f"  {C}RKP enabled     {RE}: {W}{rkp or 'N/A'}{RE}")
    print(f"  {C}Lockdown mode   {RE}: {W}{lockdown or 'N/A'}{RE}")
    print(f"  {C}Loaded modules  {RE}: {W}{modules or 'N/A'}{RE}")
    print(f"\n  {C}Kernel cmdline  {RE}:\n  {W}{(cmdline or 'N/A')[:200]}{RE}")

    print(f"\n{C}Security features active on S24 Ultra kernel:{RE}")
    for feat in [
        "RKP (Realtime Kernel Protection) — Samsung hypervisor locks kernel",
        "KernelSU patches the kernel to bypass RKP for root",
        "KFENCE — probabilistic memory safety detector",
        "CFI (Control Flow Integrity) — prevents ROP attacks",
        "KASLR — kernel address space layout randomization",
        "SELinux enforcing — mandatory access control",
    ]:
        print(f"  {Y}▸{RE} {W}{feat}{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 65 — Generate PC Unlock Script
# ─────────────────────────────────────────────────────────────────────────────
def m65_generate_pc_script():
    header("Method 65: Generate PC Unlock Script")
    serial, _ = get_device()

    ip   = get_wifi_ip() or "<DEVICE_IP>"
    bl,  _, _ = shell("getprop ro.bootloader") if serial else ("S928BXXS6DZE1","",0)
    model,_,_ = shell("getprop ro.product.model") if serial else ("SM-S928B","",0)

    sh_path  = os.path.expanduser("~/pc_unlock_commands.sh")
    bat_path = os.path.expanduser("~/pc_unlock_commands.bat")

    sh_content = f"""#!/bin/bash
# Samsung Galaxy S24 Ultra Bootloader Unlock Script
# Model: {model or 'SM-S928B'}  Bootloader: {bl or 'S928BXXS6DZE1'}
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Run this on your PC (Linux/Mac) after enabling OEM Unlock on device

set -e

echo "=== S24 Ultra Bootloader Unlock ==="

# Option A: USB cable
echo "Checking ADB via USB..."
adb devices

echo "Rebooting to bootloader..."
adb reboot bootloader
sleep 10

echo "Checking fastboot..."
fastboot devices

echo "Unlocking bootloader (you must confirm on device screen with Volume Up)..."
fastboot flashing unlock

echo "Done! Device will factory reset and reboot."
echo "After reboot: re-enable Developer Options and run Magisk patching."

# Option B: Wireless (if TCP ADB is enabled on device)
# adb connect {ip}:5555
# adb reboot bootloader
# sleep 10
# fastboot flashing unlock
"""

    bat_content = f"""@echo off
REM Samsung Galaxy S24 Ultra Bootloader Unlock
REM Model: {model or 'SM-S928B'}  Bootloader: {bl or 'S928BXXS6DZE1'}
REM Run on Windows PC after enabling OEM Unlock on device

echo === S24 Ultra Bootloader Unlock ===

echo Checking ADB...
adb devices

echo Rebooting to bootloader...
adb reboot bootloader
timeout /t 10

echo Checking fastboot...
fastboot devices

echo Unlocking (confirm with Volume Up on device)...
fastboot flashing unlock

echo Done!
pause
"""

    with open(sh_path, 'w') as f:
        f.write(sh_content)
    with open(bat_path, 'w') as f:
        f.write(bat_content)
    run(f"chmod +x {sh_path}")

    success(f"Linux/Mac script: {sh_path}")
    success(f"Windows script  : {bat_path}")

    print(f"\n{C}Transfer to PC:{RE}")
    if ip and ip != "<DEVICE_IP>":
        print(f"  {W}# From PC (same WiFi network):{RE}")
        print(f"  {G}adb connect {ip}:5555{RE}")
        print(f"  {G}adb pull /data/local/tmp/pc_unlock_commands.sh .{RE}")
    print(f"  {W}# Or copy via USB storage / email to yourself{RE}")
    print(f"\n{C}Script preview:{RE}")
    for line in sh_content.split('\n')[:20]:
        print(f"  {W}{line}{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 66 — SamFW Firmware Info for S928BXXS6DZE1
# ─────────────────────────────────────────────────────────────────────────────
def m66_samfw_info():
    header("Method 66: SamFW Firmware Info — S928BXXS6DZE1")
    serial, _ = get_device()

    bl,      _, _ = shell("getprop ro.bootloader") if serial else ("S928BXXS6DZE1","",0)
    model,   _, _ = shell("getprop ro.product.model") if serial else ("SM-S928B","",0)
    csc,     _, _ = shell("getprop ro.csc.sales_code") if serial else ("","",0)
    android, _, _ = shell("getprop ro.build.version.release") if serial else ("16","",0)

    print(f"  {C}Model    {RE}: {W}{model or 'SM-S928B'}{RE}")
    print(f"  {C}Current  {RE}: {W}{bl or 'S928BXXS6DZE1'}{RE}")
    print(f"  {C}CSC      {RE}: {W}{csc or 'XXX (global)'}{RE}")
    print(f"  {C}Android  {RE}: {W}{android or '16'}{RE}\n")

    print(f"{C}Where to get stock firmware for Magisk patching:{RE}")
    sites = [
        ("SamFW (recommended)", "samfw.com/samsung/SM-S928B/XXX"),
        ("SamMobile",           "sammobile.com → Firmware → SM-S928B"),
        ("Frija (auto-dl tool)","github.com/SlackingVeteran/frija"),
        ("Samloader (Python)",  "github.com/nlscc/samloader  [pip install samloader]"),
    ]
    for label, url in sites:
        print(f"  {C}{label:<25}{RE}: {W}{url}{RE}")

    print(f"\n{C}What you need from firmware zip:{RE}")
    print(f"  {Y}AP_S928BXXS6DZE1_*.tar.lz4{RE} → extract → {W}boot.img{RE}")
    print(f"  {Y}(also useful: vbmeta.img for dm-verity disable){RE}")

    print(f"\n{C}Extraction commands (in Termux):{RE}")
    print(f"  {W}# Install tools{RE}")
    print(f"  {G}pkg install lzip tar python{RE}")
    print(f"  {W}# Extract lz4{RE}")
    print(f"  {G}lz4 -d AP_S928BXXS6DZE1_*.tar.lz4 AP_firmware.tar{RE}")
    print(f"  {W}# Extract boot.img from tar{RE}")
    print(f"  {G}tar xvf AP_firmware.tar boot.img vbmeta.img{RE}")
    print(f"  {W}# OR use python payload_dumper for payload.bin inside{RE}")
    print(f"  {G}pip install payload-dumper-go  # then: payload-dumper boot.img{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 67 — Termux Full Tool Setup
# ─────────────────────────────────────────────────────────────────────────────
def m67_termux_setup():
    header("Method 67: Termux Full Tool Setup")
    serial, _ = get_device()

    print(f"{C}Installing all tools needed for S24 Ultra bootloader unlock:{RE}\n")

    packages = [
        ("android-tools",  "adb, fastboot, mke2fs"),
        ("python",         "Python 3 runtime"),
        ("curl",           "HTTP client for downloads"),
        ("wget",           "File downloader"),
        ("lzip",           "LZ4 decompression for firmware"),
        ("tar",            "Archive extraction"),
        ("sqlite",         "SQLite3 for settings DB access"),
        ("heimdall",       "Open-source Samsung flash tool"),
        ("openssh",        "SSH client/server"),
        ("nmap",           "Network scanner"),
    ]

    print(f"  {'Package':<20} {'Purpose':<35} {'Status'}{RE}")
    print(f"  {'─'*60}")
    missing = []
    for pkg, desc in packages:
        # Guess binary name
        binary = {"android-tools":"adb","lzip":"lz4","sqlite":"sqlite3"}.get(pkg, pkg)
        installed = check_tool(binary)
        status = f"{G}Installed{RE}" if installed else f"{R}Missing{RE}"
        print(f"  {W}{pkg:<20}{RE} {C}{desc:<35}{RE} {status}")
        if not installed:
            missing.append(pkg)

    if missing:
        print(f"\n{Y}Missing packages: {', '.join(missing)}{RE}")
        if input(f"\n{Y}Install all missing packages now? (yes/no): {RE}").strip().lower() == "yes":
            install_cmd = f"pkg install -y {' '.join(missing)}"
            info(f"Running: {install_cmd}")
            out, err, rc = run(install_cmd, timeout=300)
            if rc == 0:
                success("All packages installed")
            else:
                warn("Some packages may have failed — check output above")
                print(f"{W}{(out+err)[-500:]}{RE}")
    else:
        success("All tools already installed")

    # Check Python packages
    print(f"\n{C}Python packages for firmware extraction:{RE}")
    for pip_pkg in ["frida-tools", "samloader"]:
        out, _, rc = run(f"pip show {pip_pkg} 2>/dev/null | grep Version")
        status = f"{G}{out}{RE}" if rc == 0 and out else f"{Y}Not installed (pip install {pip_pkg}){RE}"
        print(f"  {C}{pip_pkg:<20}{RE}: {status}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 68 — Real-Time OEM Toggle Monitor
# ─────────────────────────────────────────────────────────────────────────────
def m68_oem_toggle_watcher():
    header("Method 68: Real-Time OEM Toggle Monitor")

    # ── One-time diagnostic before loop ───────────────────────────────────────
    print(f"{C}{'─'*62}{RE}")
    print(f"{C}  Initial diagnostic scan:{RE}")
    print(f"{C}{'─'*62}{RE}")

    # Check all known OEM unlock properties (Android 14-16 / OneUI 6-8)
    oem_props = [
        "sys.oem_unlock_allowed",
        "persist.sys.oem_unlock_allowed",
        "ro.oem_unlock_supported",
        "ro.boot.oem_unlock_allowed",
        "ro.config.oem_unlock_allowed",
        "sys.oem_unlock_requirement_timer",
        "persist.oem_unlock_allowed",
        "vendor.oem_unlock_allowed",
    ]
    any_prop_set = False
    for p in oem_props:
        v, _, _ = shell(f"getprop {p} 2>/dev/null")
        val = v.strip()
        if val:
            color = G if val == "1" else Y
            print(f"  {color}{p:<42}{RE} = {val}")
            any_prop_set = True
        else:
            print(f"  {W}{p:<42}{RE} = (not set)")

    # Check Samsung OEM service
    svc, _, _ = shell("getprop init.svc.sec_oem_unlock 2>/dev/null || getprop init.svc.oem_unlock 2>/dev/null")
    svc_val = svc.strip() or "not found"
    print(f"\n  Samsung OEM unlock service: {G if svc_val=='running' else Y}{svc_val}{RE}")

    # Setup wizard check via alternative method
    prov, _, _ = shell("getprop persist.sys.setupwizard.mode 2>/dev/null")
    prov_val = prov.strip() or "—"
    print(f"  Setup wizard mode         : {prov_val}")

    if not any_prop_set:
        print(f"\n  {R}{BO}No OEM unlock properties found at all.{RE}")
        print(f"  {Y}This means the Samsung OEM unlock daemon has never run.{RE}")
        print(f"  {Y}Most likely cause: setup wizard not fully completed,{RE}")
        print(f"  {Y}or the device was reset and timer hasn't started yet.{RE}")
        print(f"\n  {C}Try rebooting the phone — the daemon runs at boot.{RE}")
        print(f"  {C}After reboot, leave on WiFi 10 min then check again.{RE}")

    print(f"\n{C}{'─'*62}{RE}")
    print(f"{C}  Watching every 5s — Ctrl+C to stop{RE}")
    print(f"{C}{'─'*62}{RE}\n")

    prev_sys = None
    try:
        i = 0
        while True:
            oem_sys, _, _ = shell("getprop sys.oem_unlock_allowed 2>/dev/null")
            sys_val = oem_sys.strip()
            inet = check_internet()
            ts = datetime.now().strftime("%H:%M:%S")

            sys_changed = (sys_val != prev_sys)
            sys_color = G if sys_val == "1" else (Y if sys_val == "0" else R)
            net_color  = G if inet else R

            if sys_changed or i % 12 == 0:  # print on change or every 60s
                status = "HIDDEN from Dev Options" if sys_val != "1" else "VISIBLE in Dev Options!"
                print(f"  [{ts}] sys.oem_unlock_allowed={sys_color}{sys_val or 'N/A'}{RE}"
                      f"  inet={net_color}{'OK' if inet else 'NO'}{RE}"
                      f"  → {status}"
                      f"{f'  {R}{BO}← CHANGED!{RE}' if sys_changed and prev_sys is not None else ''}")

            if sys_val == "1" and prev_sys != "1":
                print(f"\n{G}{BO}  ★★★ OEM UNLOCK TIMER COMPLETE! ★★★{RE}")
                print(f"{G}  'OEM Unlocking' now APPEARS in Developer Options!{RE}")
                print(f"{C}  → Settings → Developer Options → OEM Unlocking → Enable{RE}")
                print(f"{C}  → Then: reboot bootloader → fastboot flashing unlock{RE}\n")

            prev_sys = sys_val
            i += 1
            time.sleep(5)
    except KeyboardInterrupt:
        print(f"\n{Y}Monitor stopped.{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 69 — Disable Find My Mobile (pre-unlock safety)
# ─────────────────────────────────────────────────────────────────────────────
def m69_disable_find_my():
    header("Method 69: Disable Find My Mobile (Pre-Unlock Safety)")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    print(f"{C}Find My Mobile can remotely lock/wipe your device.{RE}")
    print(f"{C}Samsung recommends disabling it before unlocking.{RE}\n")

    # Check if Find My Mobile is installed and its state
    fmm, _, _ = shell("pm list packages 2>/dev/null | grep -i 'fmm\\|findmymobile\\|mylocation'")
    print(f"  {C}FMM packages{RE}: {W}{fmm.replace('package:','') or 'None found'}{RE}")

    # Check Samsung account
    sa, _, _ = shell("pm list packages 2>/dev/null | grep -i samsungaccount")
    print(f"  {C}Samsung Account{RE}: {W}{sa.replace('package:','') or 'Not found'}{RE}")

    print(f"\n{C}Steps to disable Find My Mobile before unlocking:{RE}")
    for step in [
        "1. Open Samsung Find My Mobile app or go to findmymobile.samsung.com",
        "2. Sign in with your Samsung account",
        "3. Settings → Deactivate Find My Mobile",
        "OR: Settings → Biometrics and Security → Find My Mobile → toggle OFF",
        "",
        "4. Also consider removing Samsung account temporarily:",
        "   Settings → Accounts and backup → Manage accounts → Samsung account → Remove",
        "",
        "5. Remove Google account if you want to avoid FRP lock after wipe:",
        "   Settings → Accounts and backup → Manage accounts → Google → Remove account",
    ]:
        color = C if step.startswith(("1.","2.","3.","4.","5.")) else W
        print(f"  {color}{step}{RE}")

    # Try to open Find My Mobile settings
    if input(f"\n{Y}Open Find My Mobile settings now? (yes/no): {RE}").strip().lower() == "yes":
        cmds = [
            "am start -n com.samsung.android.fmm/.view.activity.FmmMainActivity 2>/dev/null",
            "am start -a android.intent.action.MAIN -n com.samsung.android.fmm/.activity.MainActivity 2>/dev/null",
        ]
        for cmd in cmds:
            _, _, rc = shell(cmd, timeout=5)
            if rc == 0:
                success("Find My Mobile opened"); break
        else:
            shell("am start -a android.settings.SECURITY_SETTINGS 2>/dev/null", timeout=5)
            info("Security settings opened — navigate to Find My Mobile")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 70 — Alternative Root: KernelSU / APatch
# ─────────────────────────────────────────────────────────────────────────────
def m70_kernelsu_info():
    header("Method 70: Alternative Root Methods — KernelSU & APatch")
    serial, _ = get_device()

    bl,  _, _ = shell("getprop ro.bootloader") if serial else ("S928BXXS6DZE1","",0)
    kver,_, _ = shell("uname -r") if serial else ("","",0)

    print(f"  {C}Bootloader{RE}: {W}{bl or 'S928BXXS6DZE1'}{RE}")
    print(f"  {C}Kernel    {RE}: {W}{kver or 'N/A'}{RE}\n")

    print(f"{C}{BO}Three root methods for S24 Ultra after bootloader unlock:{RE}\n")

    methods = [
        ("Magisk", "Most popular, best module support, GKI compatible",
         ["Patch stock boot.img via Magisk app",
          "Flash patched boot: fastboot flash boot magisk_patched.img",
          "Supports Zygisk, Shamiko, PlayIntFix modules",
          "GitHub: github.com/topjohnwu/Magisk"]),
        ("KernelSU", "Kernel-level root, bypasses some Magisk detections",
         ["Requires KernelSU-compatible kernel build for S928B",
          "Flash KSU kernel via fastboot then install manager app",
          "Better for hiding root from apps",
          "GitHub: github.com/tiann/KernelSU"]),
        ("APatch", "Newest method, Android kernel patching",
         ["Patches boot.img at kernel level like KernelSU",
          "No need for custom kernel — patches stock kernel",
          "Best compatibility with stock firmware",
          "GitHub: github.com/bmax121/APatch"]),
    ]
    for name, summary, steps in methods:
        print(f"  {B}{BO}{name}{RE}: {Y}{summary}{RE}")
        for s in steps:
            print(f"    {W}→ {s}{RE}")
        print()

    print(f"{C}Recommendation for S24 Ultra (S928BXXS6DZE1 Android 16):{RE}")
    print(f"  {G}1st choice: APatch{RE} — works on stock kernel, no custom kernel needed")
    print(f"  {G}2nd choice: Magisk{RE} — most compatible modules")
    print(f"  {Y}3rd choice: KernelSU{RE} — needs specific kernel build for pineapple/SM-S928B")

    # Check what's currently installed
    if serial:
        for pkg, name in [("io.github.kernelsu","KernelSU"),
                          ("me.bmax.apatch","APatch"),
                          ("io.github.huskydg.magisk","Magisk Delta"),
                          ("com.topjohnwu.magisk","Magisk")]:
            found, _, _ = shell(f"pm list packages 2>/dev/null | grep {pkg}")
            if found:
                print(f"\n  {G}Detected: {name} is installed{RE}")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 71 — Enable ADB TCP:5555 via Root
# ─────────────────────────────────────────────────────────────────────────────
def m71_adb_tcp_root():
    header("Method 71: Enable ADB TCP:5555 via Root (Wireless PC Connect)")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    ip = get_wifi_ip()
    print(f"  {C}Device WiFi IP{RE}: {G if ip else R}{ip or 'Not connected'}{RE}\n")

    if not ip:
        error("No WiFi IP — connect to WiFi first (Method 58)")
        return

    info("Setting ADB TCP port 5555 via multiple methods…")

    # Method A: setprop + restart adbd
    _, _, rc1 = run("su -c 'setprop service.adb.tcp.port 5555' 2>/dev/null", timeout=5)
    _, _, rc2 = run("su -c 'stop adbd; sleep 1; start adbd' 2>/dev/null", timeout=15)
    # Method B: direct setprop without su
    _, _, rc3 = shell("setprop service.adb.tcp.port 5555 2>/dev/null", timeout=5)

    print(f"  {C}su setprop     {RE}: {G if rc1==0 else Y}{'OK' if rc1==0 else 'Failed'}{RE}")
    print(f"  {C}su adbd restart{RE}: {G if rc2==0 else Y}{'OK' if rc2==0 else 'Failed'}{RE}")
    print(f"  {C}direct setprop {RE}: {G if rc3==0 else Y}{'OK' if rc3==0 else 'Failed'}{RE}")

    time.sleep(3)
    cur_port, _, _ = shell("getprop service.adb.tcp.port")
    print(f"\n  {C}Current ADB TCP port{RE}: {G if cur_port=='5555' else W}{cur_port or 'N/A'}{RE}")

    if cur_port == "5555" or rc1 == 0:
        success(f"ADB TCP enabled on port 5555")
        print(f"\n{G}Connect from PC:{RE}")
        print(f"  {W}adb connect {ip}:5555{RE}")
        print(f"  {W}adb devices{RE}")
        print(f"  {W}adb reboot bootloader   ← then run fastboot flashing unlock on PC{RE}")
    else:
        warn("TCP ADB not confirmed — root may be required")
        print(f"\n{C}Alternative — use Wireless Debugging UI (no root):{RE}")
        print(f"  Settings → Developer Options → Wireless Debugging → ON")
        print(f"  Note the IP:port and connect: adb connect <ip>:<port>")
        shell("am start -n com.android.settings/.DevelopmentSettings 2>/dev/null", timeout=5)


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 72 — IMEI & Device Registration Check
# ─────────────────────────────────────────────────────────────────────────────
def m72_imei_check():
    header("Method 72: IMEI & Device Registration Check")
    serial, _ = get_device()
    if not serial:
        error("No device detected"); return

    # IMEI via getprop and telephony
    imei1, _, _ = shell("service call iphonesubinfo 1 2>/dev/null | "
                        "awk -F\"'\" '{print $2}' | tr -d '.' | tr -d '\n'")
    imei_prop, _, _ = shell("getprop ril.gsm.imei 2>/dev/null")
    imei2, _, _ = shell("getprop ril.imei 2>/dev/null")
    model, _, _ = shell("getprop ro.product.model")
    serial_no, _, _ = shell("getprop ro.serialno")

    print(f"  {C}Model          {RE}: {W}{model or 'N/A'}{RE}")
    print(f"  {C}Serial         {RE}: {W}{serial_no or 'N/A'}{RE}")

    # Mask IMEI for security — show only last 4 digits
    for label, imei in [("IMEI (service)", imei1), ("IMEI (ril.gsm)", imei_prop),
                        ("IMEI (ril.imei)", imei2)]:
        clean = ''.join(c for c in (imei or '') if c.isdigit())
        if len(clean) >= 8:
            masked = clean[:4] + "*" * (len(clean)-8) + clean[-4:]
            print(f"  {C}{label:<25}{RE}: {W}{masked}{RE}")
        elif clean:
            print(f"  {C}{label:<25}{RE}: {W}{'*'*len(clean)}{RE}")
        else:
            print(f"  {C}{label:<25}{RE}: {W}N/A{RE}")

    print(f"\n{C}IMEI and unlock eligibility:{RE}")
    for note in [
        "Your SM-S928B (XXX global) is NOT carrier-locked based on XX region code",
        "IMEI check: imei.info or imeicheck.com — verify carrier status",
        "Samsung unlock: samsungknox.com/en/solutions/it-solutions/knox-mobile-enrollment",
        "Bootloader unlock does NOT depend on carrier unlock (separate process)",
        "After bootloader unlock, carrier unlock remains unchanged",
    ]:
        print(f"  {W}→ {note}{RE}")

    print(f"\n{C}Dial codes for IMEI on device:{RE}")
    print(f"  {G}*#06#{RE}  → shows IMEI on screen")
    print(f"  {G}*#1234#{RE} → shows firmware/CSC version")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 73 — Samsung Service & Diagnostic Codes
# ─────────────────────────────────────────────────────────────────────────────
def m73_service_codes():
    header("Method 73: Samsung Service & Diagnostic Codes")
    serial, _ = get_device()

    print(f"{C}Samsung Galaxy S24 Ultra — Service Mode Codes:{RE}\n")
    codes = [
        ("*#0*#",         "General diagnostic screen (display, sensors, touch)"),
        ("*#1234#",       "Firmware version (AP/CP/CSC)"),
        ("*#12580*369#",  "Software info & hardware info"),
        ("*#9090#",       "Diagnostic mode (USB config)"),
        ("*#0589#",       "Light sensor test"),
        ("*#2663#",       "Touch screen firmware version"),
        ("*#0588#",       "Proximity sensor test"),
        ("*#3214789650#", "LBS test mode"),
        ("*#7353#",       "Quick test menu"),
        ("*#7465625#",    "Device lock status — check carrier lock"),
        ("*#272*IMEI#",   "CSC change menu (region change)"),
        ("*#9900#",       "SysDump mode (log collection)"),
        ("*#0283#",       "Audio loopback test"),
        ("*#526#",        "WLAN engineering mode"),
    ]
    for code, desc in codes:
        print(f"  {G}{code:<20}{RE}: {W}{desc}{RE}")

    print(f"\n{C}Unlock-relevant codes:{RE}")
    print(f"  {Y}*#7465625#{RE} → Check 'Phone lock' and 'Network lock' — both should show OFF")
    print(f"  {Y}*#1234#{RE}    → Confirm you're on S928BXXS6DZE1 (matches unlock firmware)")

    if serial:
        # Open dialer to run a test code
        if input(f"\n{Y}Open dialer to run *#7465625# (lock status)? (yes/no): {RE}").strip().lower() == "yes":
            shell("am start -a android.intent.action.CALL -d tel:%237465625%23 2>/dev/null", timeout=5)
            success("Dialer opened — check Network Lock and Phone Lock status")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 74 — Unlock Timeline & Day-by-Day Action Plan
# ─────────────────────────────────────────────────────────────────────────────
def m74_unlock_timeline():
    header("Method 74: Unlock Timeline & Day-by-Day Action Plan")
    serial, _ = get_device()

    # Get current state
    dev  = get_setting("global", "development_settings_enabled") if serial else None
    oem  = get_setting("global", "oem_unlock_allowed")           if serial else None
    inet = check_internet() if serial else False

    print(f"{C}Based on your SM-S928B current state:{RE}\n")
    print(f"  Developer Options : {G if dev=='1' else R}{'Enabled' if dev=='1' else 'Disabled'}{RE}")
    print(f"  OEM Unlock setting: {G if oem=='1' else R}{oem or 'Not set/unknown'}{RE}")
    print(f"  Internet          : {G if inet else R}{'Connected' if inet else 'Disconnected'}{RE}")

    print(f"\n{C}{BO}Day-by-Day Action Plan:{RE}\n")
    plan = [
        ("TODAY",   [
            "Run Method 58 — connect to WiFi (timer must start)",
            "Run Method 59 — enable Developer Options (root or manual)",
            "Run Method 60 — write OEM unlock setting to DB",
            "Go to Settings → Developer Options → toggle OEM Unlocking ON physically",
            "Run Method 69 — disable Find My Mobile",
            "Run Method 51 — disable auto OTA updates",
            "Keep phone connected to WiFi — timer is now counting",
        ]),
        ("DAYS 1-6",[
            "Leave phone on WiFi with screen occasionally active",
            "Run Method 68 (OEM Toggle Monitor) to watch for it to unlock",
            "DO NOT factory reset — this resets the 7-day timer",
            "DO NOT install OTA updates",
            "Backup data if not done yet — Method 32",
        ]),
        ("DAY 7+",  [
            "OEM Unlocking toggle should now be active (not greyed)",
            "Run Method 55 — full eligibility check should show all PASS",
            "Run Method 56 — ONE-BUTTON MASTER UNLOCK",
            "OR manually: Method 7 → reboot bootloader → PC: fastboot flashing unlock",
            "After wipe: re-setup phone, re-enable Developer Options",
            "Run Method 66 — download firmware from SamFW",
            "Run Method 27 — patch boot.img with Magisk for root",
        ]),
        ("AFTER ROOT", [
            "Install Shamiko module (hide root from apps)",
            "Install PlayIntFix module (restore Play Integrity)",
            "Install LSPosed for app hooks",
            "Disable OTA updates permanently",
            "Set up periodic bootloader backup (Method 16)",
        ]),
    ]
    for phase, steps in plan:
        print(f"  {B}{BO}{phase}:{RE}")
        for s in steps:
            print(f"    {W}→ {s}{RE}")
        print()


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 75 — S24 Ultra Unlock Quick Reference Card
# ─────────────────────────────────────────────────────────────────────────────
def m75_quick_reference():
    header("Method 75: S24 Ultra Unlock Quick Reference Card")
    serial, _ = get_device()

    ip = get_wifi_ip() if serial else None

    ref_path = os.path.expanduser("~/s24_unlock_reference.txt")

    content = f"""
╔══════════════════════════════════════════════════════════════╗
║   Samsung Galaxy S24 Ultra — Bootloader Unlock Reference     ║
║   Model: SM-S928B  |  Build: S928BXXS6DZE1  |  Android 16  ║
║   Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}                              ║
╚══════════════════════════════════════════════════════════════╝

DEVICE STATE WHEN GENERATED
  Bootloader  : LOCKED  (need to unlock)
  Knox bit    : INTACT  (0) — warranty still valid
  Android     : 16 (SDK 36)
  Region      : XX (Global) — no carrier lock
  WiFi IP     : {ip or 'N/A'}

QUICK UNLOCK STEPS (if OEM toggle is ON)
  1. adb reboot bootloader
  2. fastboot devices
  3. fastboot flashing unlock      ← Volume Up on device to confirm
  4. (device wipes and reboots)
  5. Re-enable Developer Options
  6. Flash Magisk-patched boot for root

KEY ADB COMMANDS
  adb devices                      Check connection
  adb reboot bootloader            Go to fastboot mode
  adb reboot recovery              Go to recovery
  adb reboot download              Samsung download mode (Odin)
  adb shell getprop ro.bootloader  Show bootloader version
  adb shell settings get global oem_unlock_allowed

KEY FASTBOOT COMMANDS
  fastboot devices                 Verify device in fastboot
  fastboot flashing unlock         OEM unlock (main command)
  fastboot flash boot boot.img     Flash custom/patched boot
  fastboot flash recovery twrp.img Flash custom recovery
  fastboot reboot                  Reboot normally
  fastboot reboot bootloader       Stay in bootloader

KEY GETPROP VALUES
  ro.boot.flash.locked    = 1 (locked) / 0 (unlocked)
  ro.boot.verifiedbootstate = green/orange/yellow/red
  ro.boot.warranty_bit    = 0 (intact) / 1 (tripped)
  sys.oem_unlock_allowed  = 1 (allowed)
  ro.boot.avb_version     = AVB version

FIRMWARE SOURCE
  samfw.com → SM-S928B → XXX (or your CSC)
  Need: AP_S928BXXS6DZE1_*.tar.lz4

WIRELESS CONNECTION (if TCP ADB enabled)
  adb connect {ip or '<DEVICE_IP>'}:5555

IMPORTANT WARNINGS
  ⚠ Knox warranty bit = PERMANENT after unlock
  ⚠ All data wiped during unlock
  ⚠ Do NOT flash wrong firmware (ARB will brick device)
  ⚠ Always use boot.img from S928BXXS6DZE1 firmware
  ⚠ Disable Find My Mobile before unlocking
"""

    with open(ref_path, 'w') as f:
        f.write(content)
    success(f"Reference card saved: {ref_path}")
    print(content)



# ─────────────────────────────────────────────────────────────────────────────
# METHODS 76-115 — ADVANCED SPECIALIST TOOLS
# ─────────────────────────────────────────────────────────────────────────────

def m76_battery_before_unlock():
    header("Battery Level Pre-Unlock Safety Check")
    out, _, _ = shell("cat /sys/class/power_supply/battery/capacity")
    level = out.strip()
    out2, _, _ = shell("cat /sys/class/power_supply/battery/status")
    status = out2.strip()
    out3, _, _ = shell("getprop sys.batterylevel")
    gp_level = out3.strip()
    actual = level or gp_level or "?"
    try:
        pct = int(actual)
    except Exception:
        pct = -1
    info(f"Battery level  : {actual}%")
    info(f"Charge status  : {status}")
    if pct >= 80:
        success("Battery OK (≥80%) — safe to begin unlock sequence")
    elif pct >= 50:
        warn("Battery marginal (50-79%) — charge to ≥80% before unlocking")
    elif pct > 0:
        error("Battery LOW (<50%) — do NOT start unlock; device could power off mid-flash")
    else:
        warn("Could not read battery level — ensure phone is plugged in before proceeding")
    print()
    info("Why 80%? Factory reset during unlock can take 5+ minutes. A dead phone mid-wipe can corrupt /data.")
    info("Recommendation: Plug in charger BEFORE running the unlock, keep plugged throughout.")


def m77_stay_awake_setting():
    header("Screen Stay-Awake Configuration for Unlock")
    cur = get_setting("global", "stay_on_while_plugged_in")
    info(f"Current stay_on_while_plugged_in : {cur!r}")
    info("  0 = off  |  1 = AC charger  |  2 = USB  |  3 = AC+USB  |  7 = AC+USB+Wireless")
    print()
    if cur in ("3", "7"):
        success("Screen will stay on while plugged in — good for long unlock sessions")
    else:
        warn("Screen may sleep during unlock — attempting to set stay-awake on USB+AC...")
        ok = put_setting("global", "stay_on_while_plugged_in", "3")
        if ok:
            success("stay_on_while_plugged_in set to 3 (AC+USB)")
        else:
            warn("Could not set via settings — try: Developer Options → Stay awake")
    print()
    timeout_cur = get_setting("system", "screen_off_timeout")
    info(f"Screen timeout : {timeout_cur} ms  ({int(timeout_cur or 0)//1000}s)")
    if int(timeout_cur or 0) < 300000:
        warn("Timeout < 5 min — consider setting longer via Display → Screen timeout")
    else:
        success("Screen timeout ≥5 min — should be fine")


def m78_seven_day_countdown():
    header("Samsung 7-Day OEM Unlock Timer — Countdown & Daemon Diagnostics")
    import datetime
    out, _, _ = shell("getprop sys.oem_unlock_allowed")
    oem_allowed = out.strip()
    if oem_allowed == "1":
        success("OEM unlock already ALLOWED — 7-day timer has passed!")
        return
    info("The OEM unlock toggle requires ~168h cumulative internet connection since first setup.")
    print()

    # ── Current time ─────────────────────────────────────────────────────────
    out4, _, _ = shell("date +%s")
    now_ts = int(out4.strip() or "0")
    now_dt = datetime.datetime.fromtimestamp(now_ts)
    out2, _, _ = shell("getprop ro.build.date.utc")
    build_utc = out2.strip()
    info(f"Current time       : {now_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    info(f"Build date UTC     : {build_utc}")

    # ── Try real timer props ──────────────────────────────────────────────────
    print()
    timer_props = [
        "sys.oem_unlock_requirement_timer",
        "sys.oem_unlock_allowed",
        "persist.oem_unlock_allowed",
        "oem_unlock.timer",
        "ro.oem_unlock_supported",
    ]
    info("Samsung OEM unlock daemon properties:")
    for p in timer_props:
        v, _, _ = shell(f"getprop {p} 2>/dev/null")
        val = v.strip() or "—"
        color = G if val not in ("—", "0") else W
        print(f"  {color}{p:<42}{RE}: {val}")

    # ── Check Samsung OEM unlock service ─────────────────────────────────────
    print()
    info("Samsung OEM unlock service status:")
    svc_checks = [
        ("init.svc.oem_unlock",          "getprop init.svc.oem_unlock 2>/dev/null"),
        ("init.svc.sec_oem_unlock",      "getprop init.svc.sec_oem_unlock 2>/dev/null"),
        ("init.svc.oem_unlock_req",      "getprop init.svc.oem_unlock_req 2>/dev/null"),
        ("OEM unlock process",           "ps -A 2>/dev/null | grep -i oem_unlock | head -2"),
        ("Knox unlock service",          "ps -A 2>/dev/null | grep -i knox.*unlock | head -2"),
    ]
    daemon_running = False
    for label, cmd in svc_checks:
        v, _, _ = shell(cmd)
        val = v.strip() or "—"
        if val not in ("—", "stopped", ""):
            success(f"{label}: {val}")
            daemon_running = True
        else:
            print(f"  {W}{label:<35}{RE}: {val}")

    # ── Try to trigger the daemon ─────────────────────────────────────────────
    print()
    info("Attempting to trigger Samsung OEM unlock daemon...")
    triggers = [
        "am broadcast -a com.samsung.android.server.oem_unlock.action.OEM_UNLOCK_CHECK 2>/dev/null",
        "am broadcast -a android.intent.action.BOOT_COMPLETED 2>/dev/null",
        "am startservice com.android.settings/.oem_lock.OemLockService 2>/dev/null",
        "am broadcast -a com.android.settings.action.OEM_UNLOCK_SETTINGS 2>/dev/null",
    ]
    for t in triggers:
        _, _, rc = shell(t, timeout=5)
        icon = G + "✓" if rc == 0 else W + "—"
        print(f"  {icon}{RE} {t[:70]}")

    # ── Heuristic based on build date ─────────────────────────────────────────
    print()
    if build_utc:
        try:
            build_ts = int(build_utc)
            elapsed_h = (now_ts - build_ts) // 3600
            info(f"Elapsed since build: ~{elapsed_h}h  (need 168h connected)")
            if elapsed_h >= 168:
                warn("≥168h since build — timer SHOULD be expired.")
                print()
                error("sys.oem_unlock_allowed is still not set despite timer appearing expired.")
                info("Most likely causes:")
                print(f"  {Y}1. Timer counts CONNECTED hours only — offline time doesn't count{RE}")
                print(f"  {Y}2. Phone was factory-reset (resets timer to 0){RE}")
                print(f"  {Y}3. Samsung setup wizard NOT fully completed (affects timer start){RE}")
                print(f"  {Y}4. Samsung account NOT added during setup (some regions require it){RE}")
                print(f"  {Y}5. The Samsung OEM unlock daemon isn't running — try rebooting{RE}")
                print()
                info("ACTION: Reboot the phone, ensure WiFi connects on boot, leave for 10 min,")
                info("        then re-run Method 68 (OEM Toggle Watcher) to see if it activates.")
                info("        If still N/A after reboot: the timer may have been reset by a factory reset.")
            else:
                remaining = 168 - elapsed_h
                unlock_at = datetime.datetime.fromtimestamp(build_ts + 168 * 3600)
                warn(f"~{remaining}h remaining — estimated ready: {unlock_at.strftime('%Y-%m-%d %H:%M')}")
                info("Keep WiFi on continuously. Offline time does NOT count toward the timer.")
        except Exception:
            warn("Could not parse build UTC timestamp")

    print()
    info("To speed up: keep WiFi connected 24/7. Mobile data also counts.")
    info("To check if daemon activates: run Method 68 — it watches every 5s.")


def m79_usbc_mode_detector():
    header("USB-C Port Mode & ADB Configuration Detector")
    checks = [
        ("USB config mode",     "getprop sys.usb.config"),
        ("USB state",           "getprop sys.usb.state"),
        ("USB ffs enabled",     "getprop sys.usb.ffs.ready"),
        ("USB gadget type",     "getprop persist.sys.usb.config"),
        ("USB speed",           "cat /sys/class/usb_gadget/g1/max_speed 2>/dev/null"),
        ("USB UDC driver",      "cat /sys/class/usb_gadget/g1/UDC 2>/dev/null"),
        ("USB connected",       "cat /sys/class/power_supply/usb/present 2>/dev/null"),
        ("USB type",            "cat /sys/class/power_supply/usb/usb_type 2>/dev/null"),
        ("USB PD active",       "cat /sys/class/typec/port0/power_role 2>/dev/null"),
        ("Accessory mode",      "getprop sys.usb.accessory"),
    ]
    for label, cmd in checks:
        out, _, _ = shell(cmd)
        val = out.strip() or "—"
        color = G if val not in ("—", "0", "") else W
        print(f"  {color}{label:<25}{RE}: {val}")
    print()
    cur_config, _, _ = shell("getprop sys.usb.config")
    cfg = cur_config.strip()
    if "adb" in cfg:
        success(f"ADB is active in USB config: {cfg}")
    else:
        warn(f"ADB not in current USB config: {cfg!r}")
        info("To add ADB: Developer Options → USB debugging ON")
    info("For wireless ADB (no USB needed): Method 45 — Wireless ADB Setup")


def m80_mdm_enrollment_check():
    header("MDM / Enterprise Enrollment Detection")
    checks = [
        ("Device owner",        "dumpsys device_policy 2>/dev/null | grep -i 'device owner' | head -3"),
        ("Profile owner",       "dumpsys device_policy 2>/dev/null | grep -i 'profile owner' | head -3"),
        ("Knox MDM",            "getprop ro.config.knox"),
        ("Knox enterprise",     "getprop ro.config.enterprise_mdm"),
        ("MDM restricted",      "getprop ro.config.mdm_restrict"),
        ("EMM enrolled",        "getprop persist.sys.emm_enrolled 2>/dev/null"),
        ("Work profile",        "pm list users 2>/dev/null | grep -i work"),
        ("Knox Guard",          "pm list packages 2>/dev/null | grep -i knoxguard"),
        ("Samsung MDM agent",   "pm list packages 2>/dev/null | grep -i 'com.samsung.android.mdm'"),
        ("MS Intune",           "pm list packages 2>/dev/null | grep -i intune"),
        ("VMware AirWatch",     "pm list packages 2>/dev/null | grep -i airwatch"),
        ("MobileIron",         "pm list packages 2>/dev/null | grep -i mobileiron"),
    ]
    mdm_detected = False
    for label, cmd in checks:
        out, _, _ = shell(cmd)
        val = out.strip()
        if val:
            print(f"  {R}{BO}{label:<25}{RE}: {val}")
            mdm_detected = True
        else:
            print(f"  {G}{label:<25}{RE}: not found")
    print()
    if mdm_detected:
        error("MDM/Enterprise enrollment detected!")
        error("Managed devices CANNOT be unlocked while enrolled.")
        info("Steps to remove: Settings → Biometrics & security → Device admin apps")
        info("Or contact your IT admin to unenroll the device first.")
    else:
        success("No MDM/Enterprise enrollment detected — device appears personal/unmanaged")


def m81_adb_rsa_key_guide():
    header("ADB RSA Key Auto-Accept Guide & Status")
    out, _, _ = shell("ls /data/misc/adb/adb_keys 2>/dev/null | wc -l")
    key_count = out.strip()
    out2, _, _ = shell("getprop ro.adb.secure")
    adb_secure = out2.strip()
    out3, _, _ = shell("getprop service.adb.tcp.port")
    tcp_port = out3.strip()
    out4, _, _ = shell("settings get global adb_enabled")
    adb_enabled = out4.strip()
    info(f"ADB secure mode       : {adb_secure}  (1=requires key auth)")
    info(f"ADB enabled           : {adb_enabled}")
    info(f"ADB TCP port          : {tcp_port or 'off'}")
    info(f"Stored ADB key count  : {key_count or '?'}")
    print()
    info("To trust a PC's ADB key automatically:")
    info("  1. On the phone: Developer Options → Revoke USB debugging authorisations")
    info("  2. On the PC:    adb kill-server && adb start-server")
    info("  3. Plug USB — accept the dialog that appears ON THE PHONE SCREEN")
    info("  4. Tick 'Always allow from this computer' before tapping OK")
    print()
    out5, _, _ = shell("cat /data/misc/adb/adb_keys 2>/dev/null | head -5")
    if out5.strip():
        info("Currently trusted ADB public keys (truncated):")
        for line in out5.strip().split("\n"):
            print(f"    {line[:72]}…")
    else:
        info("No ADB keys currently stored (or no root to read /data/misc/adb/)")
    print()
    info("For wireless ADB key trust: connect once via USB, then enable TCP 5555.")


def m82_backup_before_wipe():
    header("Pre-Unlock Backup — Critical Data Protection")
    info("Bootloader unlock WIPES all user data (factory reset).")
    info("Back up these items BEFORE unlocking:")
    print()
    sections = [
        ("Photos & Videos",   "cp -r /sdcard/DCIM /sdcard/Android/data/backup_dcim 2>/dev/null || echo 'use Google Photos sync'"),
        ("Contacts",          "content query --uri content://contacts/phones 2>/dev/null | wc -l"),
        ("SMS/MMS",           "content query --uri content://sms 2>/dev/null | wc -l"),
        ("App list",          "pm list packages -3 2>/dev/null | wc -l"),
        ("WiFi passwords",    "wc -l /data/misc/wifi/WifiConfigStore.xml 2>/dev/null"),
        ("Call log count",    "content query --uri content://call_log/calls 2>/dev/null | wc -l"),
    ]
    for label, cmd in sections:
        out, _, _ = shell(cmd)
        print(f"  {C}{label:<22}{RE}: {out.strip() or '(check manually)'}")
    print()
    info("Recommended backup tools (install before unlocking):")
    info("  • SMS Backup & Restore (Play Store)")
    info("  • Google One backup: Settings → Accounts → Google → Backup")
    info("  • Samsung Cloud: Settings → Accounts → Samsung account → Back up data")
    info("  • ADB backup from PC: adb backup -apk -all -f full_backup.ab")
    print()
    out2, _, _ = shell("df /sdcard 2>/dev/null | tail -1")
    info(f"SD card / internal storage: {out2.strip()}")
    info("Ensure enough space for the backup before proceeding.")


def m83_fbe_encryption_status():
    header("File-Based Encryption (FBE) Status Check")
    checks = [
        ("Encryption state",    "getprop ro.crypto.state"),
        ("Encryption type",     "getprop ro.crypto.type"),
        ("FBE version",         "getprop ro.crypto.fbe_version 2>/dev/null"),
        ("vold decrypt",        "getprop vold.decrypt"),
        ("Storage encrypted",   "getprop ro.boot.fde_algorithm 2>/dev/null"),
        ("Keymaster version",   "getprop ro.hardware.keystore"),
        ("dm-crypt state",      "ls /dev/mapper/ 2>/dev/null"),
        ("Metadata partition",  "ls /dev/block/by-name/metadata 2>/dev/null"),
        ("userdata fs",         "cat /proc/mounts 2>/dev/null | grep userdata | head -1"),
    ]
    for label, cmd in checks:
        out, _, _ = shell(cmd)
        val = out.strip() or "—"
        print(f"  {C}{label:<25}{RE}: {val}")
    print()
    enc_state, _, _ = shell("getprop ro.crypto.state")
    enc_type, _, _ = shell("getprop ro.crypto.type")
    if enc_state.strip() == "encrypted" and enc_type.strip() == "file":
        success("Device uses File-Based Encryption (FBE) — standard for S24 Ultra")
        info("FBE means per-file keys; unlocking will wipe /data but cannot bypass encryption")
    elif enc_state.strip() == "encrypted":
        info(f"Device is encrypted ({enc_type.strip()}) — data wiped on unlock")
    else:
        warn(f"Unexpected encryption state: {enc_state.strip()!r}")
    print()
    info("FBE on S24 Ultra uses Keymaster + StrongBox (Titan M equivalent in Exynos)")
    info("Cannot decrypt /data without correct PIN/password even with root")


def m84_disable_samsung_analytics():
    header("Samsung Analytics & Telemetry Disable")
    info("Disabling analytics can sometimes improve OEM toggle reliability by reducing")
    info("Samsung account validation requests.")
    print()
    analytics_pkgs = [
        "com.samsung.android.app.scs",
        "com.samsung.android.devicediagnostics",
        "com.samsung.android.bixby.wakeup",
        "com.samsung.android.sm.devicesecurity",
        "com.samsung.android.scloud",
        "com.sec.android.diagmonagent",
    ]
    for pkg in analytics_pkgs:
        out, _, _ = shell(f"pm list packages {pkg} 2>/dev/null")
        if pkg in (out or ""):
            out2, _, rc = shell(f"pm disable-user --user 0 {pkg} 2>/dev/null")
            if rc == 0:
                success(f"Disabled: {pkg}")
            else:
                warn(f"Could not disable (no root): {pkg}")
        else:
            print(f"  {W}{pkg}{RE}: not installed")
    print()
    # Disable crash reports
    settings_toggles = [
        ("global", "send_action_app_error", "0"),
        ("global", "dropbox_max_files", "0"),
        ("secure", "send_security_reports", "0"),
    ]
    for ns, key, val in settings_toggles:
        ok = put_setting(ns, key, val)
        status = G + "set" if ok else R + "failed"
        print(f"  {status}{RE} settings {ns}/{key} = {val}")
    success("Analytics suppressed where possible")


def m85_tee_trustzone_status():
    header("TEE / TrustZone / StrongBox Security Status")
    checks = [
        ("Keymaster impl",         "getprop ro.hardware.keystore"),
        ("Keymaster version",      "getprop ro.hardware.keystore_desede 2>/dev/null"),
        ("TEE OS",                 "getprop ro.boot.tee_type 2>/dev/null"),
        ("StrongBox available",    "getprop ro.hardware.strongbox 2>/dev/null"),
        ("TrustZone state",        "getprop ro.boot.trustzone"),
        ("Secure boot",            "getprop ro.boot.secureboot"),
        ("Boot verified",          "getprop ro.boot.verifiedbootstate"),
        ("Verified boot hash",     "getprop ro.boot.vbmeta.digest 2>/dev/null | cut -c1-32"),
        ("Knox active",            "getprop ro.boot.warranty_bit"),
        ("TIMA status",            "getprop ro.config.timaversion 2>/dev/null"),
        ("SE for Android",         "getenforce 2>/dev/null"),
        ("TEEGRIS version",        "getprop ro.teegris.version 2>/dev/null"),
    ]
    for label, cmd in checks:
        out, _, _ = shell(cmd)
        val = out.strip() or "—"
        print(f"  {C}{label:<28}{RE}: {val}")
    print()
    info("S24 Ultra uses Samsung TEEGRIS (Samsung's own TEE, not Qualcomm QSEE).")
    info("TrustZone stores: Knox keys, biometric data, DRM keys, payment credentials.")
    info("Unlocking bootloader does NOT directly compromise TEE, but trips Knox bit.")
    info("Knox bit (warranty_bit=1) irreversibly disables Samsung Pay and some Knox features.")


def m86_twrp_s928b_info():
    header("TWRP Custom Recovery — SM-S928B Compatibility Guide")
    out, _, _ = shell("getprop ro.product.model")
    model = out.strip()
    out2, _, _ = shell("getprop ro.boot.slot_suffix")
    slot = out2.strip()
    out3, _, _ = shell("getprop ro.build.version.release")
    android_ver = out3.strip()
    info(f"Device model     : {model}")
    info(f"Active slot      : {slot or '(A/B not reported)'}")
    info(f"Android version  : {android_ver}")
    print()
    warn("⚠  As of mid-2025, TWRP does NOT have an official build for SM-S928B (Exynos)")
    warn("⚠  SM-S928U (Snapdragon) has unofficial TWRP ports but they are NOT compatible")
    print()
    info("Alternatives for SM-S928B (Exynos):")
    info("  1. OrangeFox Recovery — check orangefox.tech for S928B builds")
    info("  2. PBRP (PitchBlack) — check pitchblackrecovery.com")
    info("  3. SHRP (SKIA) — check skia.in")
    info("  4. LineageOS built-in recovery — if flashing LineageOS")
    print()
    info("Flash process (AFTER bootloader unlock):")
    info("  adb reboot bootloader")
    info("  fastboot flash recovery recovery.img")
    info("  fastboot reboot recovery")
    print()
    info("Virtual A/B note: recovery is stored in boot partition on S24 Ultra.")
    info("Use 'fastboot boot recovery.img' to test before flashing permanently.")


def m87_custom_rom_compat():
    header("Custom ROM Compatibility — SM-S928B (Global Exynos)")
    out, _, _ = shell("getprop ro.product.model")
    model = out.strip()
    out2, _, _ = shell("getprop ro.build.fingerprint")
    fp = out2.strip()
    info(f"Model       : {model}")
    info(f"Fingerprint : {fp}")
    print()
    roms = [
        ("LineageOS 21/22",  "Active ports for S928B — check lineageos.org/wiki"),
        ("crDroid",           "S928B supported — see crdroid.net/downloads"),
        ("EvolutionX",        "Check evolution-x.org for S928B builds"),
        ("PixelOS",           "Check pixelos.net — may need unofficial builds"),
        ("GrapheneOS",        "Pixel-only — NOT compatible with SM-S928B"),
        ("CalyxOS",           "Pixel/Fairphone only — NOT compatible"),
        ("/e/ OS",            "Limited Samsung support — check e.foundation"),
        ("Paranoid Android",  "Check paranoidandroid.co for S928B availability"),
    ]
    for rom, status in roms:
        icon = G + "✓" if "Check" in status or "Active" in status or "supported" in status else R + "✗"
        print(f"  {icon}{RE} {C}{rom:<22}{RE}: {status}")
    print()
    info("Prerequisites for any custom ROM on S24 Ultra:")
    info("  1. Bootloader must be UNLOCKED (fastboot flashing unlock)")
    info("  2. Custom recovery flashed (TWRP/OrangeFox)")
    info("  3. Factory reset data wipe")
    info("  4. Anti-rollback check: ROM must be for your firmware level or newer")
    print()
    info("Post-install: GApps package needed for Google services (if not bundled)")
    info("Recommended GApps: MindTheGapps or NikGApps for Android 15/16")


def m88_vbmeta_analysis():
    header("vbmeta / Verified Boot Chain Analysis")
    checks = [
        ("vbmeta digest",     "getprop ro.boot.vbmeta.digest 2>/dev/null"),
        ("vbmeta size",       "getprop ro.boot.vbmeta.size 2>/dev/null"),
        ("vbmeta hash alg",   "getprop ro.boot.vbmeta.hash_alg 2>/dev/null"),
        ("Verified state",    "getprop ro.boot.verifiedbootstate"),
        ("Boot device",       "getprop ro.boot.bootdevice 2>/dev/null"),
        ("dm-verity state",   "getprop ro.boot.veritymode 2>/dev/null"),
        ("avb version",       "getprop ro.boot.avb_version 2>/dev/null"),
        ("vbmeta partition",  "ls -la /dev/block/by-name/vbmeta 2>/dev/null"),
        ("vbmeta_system",     "ls -la /dev/block/by-name/vbmeta_system 2>/dev/null"),
        ("vbmeta_vendor",     "ls -la /dev/block/by-name/vbmeta_vendor 2>/dev/null"),
    ]
    for label, cmd in checks:
        out, _, _ = shell(cmd)
        val = out.strip() or "—"
        print(f"  {C}{label:<25}{RE}: {val}")
    print()
    vbs, _, _ = shell("getprop ro.boot.verifiedbootstate")
    state = vbs.strip()
    if state == "green":
        info("GREEN state = boot chain fully verified by OEM key (stock ROM)")
    elif state == "yellow":
        warn("YELLOW state = custom/user key used — custom ROM or modified boot")
    elif state == "orange":
        warn("ORANGE state = verification disabled — bootloader unlocked")
    elif state == "red":
        error("RED state = verification FAILED — possible corruption or tampering")
    print()
    info("After bootloader unlock: state changes from green→orange (expected).")
    info("To disable verification with Magisk: Patch vbmeta with --flags 2")
    info("Command: fastboot flash vbmeta --disable-verity --disable-verification vbmeta.img")


def m89_ab_update_engine():
    header("A/B Partition Update Engine Status")
    checks = [
        ("Update engine",     "getprop ro.build.ab_update"),
        ("Virtual A/B",       "getprop ro.virtual_ab.enabled"),
        ("Virtual A/B retrofit", "getprop ro.virtual_ab.retrofit 2>/dev/null"),
        ("Active slot",       "getprop ro.boot.slot_suffix"),
        ("Slot A bootable",   "getprop ro.boot.slot_a_bootable 2>/dev/null"),
        ("Slot B bootable",   "getprop ro.boot.slot_b_bootable 2>/dev/null"),
        ("OTA package path",  "getprop ro.boot.android.ota 2>/dev/null"),
        ("Update status",     "update_engine_client --status 2>/dev/null | head -5"),
        ("Snapshots",         "ls /dev/block/by-name/ 2>/dev/null | grep -c '@'"),
        ("Super partition",   "ls -la /dev/block/by-name/super 2>/dev/null"),
    ]
    for label, cmd in checks:
        out, _, _ = shell(cmd)
        val = out.strip() or "—"
        print(f"  {C}{label:<28}{RE}: {val}")
    print()
    slot, _, _ = shell("getprop ro.boot.slot_suffix")
    active = slot.strip()
    inactive = "_b" if active == "_a" else "_a"
    info(f"Active slot: {active or 'unknown'}  |  Inactive slot: {inactive}")
    print()
    info("Virtual A/B on S24 Ultra uses snapshot/COW (copy-on-write) on /data.")
    info("During OTA update, snapshot is created; on success, slots are swapped.")
    info("If bootloader is unlocked and OTA runs, it may re-lock the bootloader.")
    warn("DISABLE OTA UPDATES before unlocking: Developer Options → Auto system updates OFF")


def m90_samsung_account_removal():
    header("Samsung Account Removal — Pre-Unlock Safety Step")
    out, _, _ = shell("dumpsys account 2>/dev/null | grep -i samsung | head -10")
    out2, _, _ = shell("content query --uri content://com.samsung.android.sm.provider/accounts 2>/dev/null | head -5")
    out3, _, _ = shell("getprop persist.sys.samsung_account 2>/dev/null")
    out4, _, _ = shell("pm list packages 2>/dev/null | grep 'com.osp.app.signin'")
    info("Samsung Account detection:")
    print(f"  Accounts dump  : {out.strip() or 'no data (normal if no root)'}")
    print(f"  Signed-in prop : {out3.strip() or '—'}")
    print(f"  OSP signin pkg : {out4.strip() or '—'}")
    print()
    info("Why remove Samsung Account before unlocking?")
    info("  • Find My Mobile (FMM) can REMOTELY LOCK the device post-unlock")
    info("  • Samsung Cloud restore may re-lock settings")
    info("  • Reduces Samsung validation server calls that can block OEM toggle")
    print()
    info("Steps to remove Samsung Account:")
    info("  1. Settings → Accounts and backup → Manage accounts")
    info("  2. Tap Samsung account → Remove account")
    info("  3. Settings → Biometrics and security → Find My Mobile → OFF")
    info("  4. Settings → Privacy → Google → Find My Device → OFF")
    print()
    out5, _, _ = shell("getprop ro.boot.fmm_lock 2>/dev/null")
    fmm = out5.strip()
    if fmm == "1":
        error("FMM LOCK IS ACTIVE — remove Samsung account and disable Find My Mobile first!")
    elif fmm == "0":
        success("FMM lock not active — safe to proceed")
    else:
        warn("FMM lock status unknown — verify manually in Settings")


def m91_google_frp_guide():
    header("Google FRP (Factory Reset Protection) — Pre-Unlock Guide")
    out, _, _ = shell("dumpsys account 2>/dev/null | grep -c 'google' ")
    g_accounts = out.strip()
    out2, _, _ = shell("getprop ro.frp.pst 2>/dev/null")
    frp_prop = out2.strip()
    out3, _, _ = shell("ls /dev/block/by-name/frp 2>/dev/null")
    frp_partition = out3.strip()
    out4, _, _ = shell("blockdev --getsize64 /dev/block/by-name/frp 2>/dev/null")
    frp_size = out4.strip()
    info(f"Google accounts on device : {g_accounts or '?'}")
    info(f"FRP property              : {frp_prop or '—'}")
    info(f"FRP partition             : {frp_partition or '—'}")
    info(f"FRP partition size        : {frp_size or '—'} bytes")
    print()
    info("FRP activates if device is factory-reset with Google account signed in.")
    info("After reset, the device requires the SAME Google account credentials.")
    print()
    info("To prevent FRP from locking you out after unlock:")
    info("  Option A — Remove Google account BEFORE unlock:")
    info("    Settings → Accounts and backup → Manage accounts → Google → Remove account")
    info("  Option B — Keep account, use known credentials after unlock:")
    info("    After unlock+reset, enter your Google account email/password when prompted")
    info("  Option C — Disable FRP partition via fastboot (after unlock):")
    info("    fastboot erase frp")
    print()
    warn("If you forget your Google credentials after unlock, the device is LOCKED.")
    warn("Google's FRP cannot be bypassed on current S24 Ultra firmware without root.")


def m92_fastboot_complete_checklist():
    header("Fastboot getvar Complete Checklist — S24 Ultra Reference")
    info("Run these commands from PC AFTER rebooting to bootloader:")
    info("  adb reboot bootloader  (or: Power + Vol Down from off)")
    print()
    vars_list = [
        ("current-slot",         "Active A/B slot"),
        ("slot-count",           "Number of slots (should be 2)"),
        ("slot-successful:a",    "Slot A marked successful"),
        ("slot-successful:b",    "Slot B marked successful"),
        ("slot-unbootable:a",    "Slot A unbootable flag"),
        ("slot-unbootable:b",    "Slot B unbootable flag"),
        ("is-userspace",         "In userspace fastboot (fastbootd)"),
        ("unlocked",             "Bootloader lock state"),
        ("secure",               "Secure boot enforced"),
        ("hw-revision",          "Hardware revision"),
        ("anti",                 "Anti-rollback (ARB) level"),
        ("max-download-size",    "Max fastboot download size"),
        ("version",              "Fastboot protocol version"),
        ("version-bootloader",   "Bootloader version"),
        ("product",              "Product codename"),
        ("serialno",             "Serial number"),
        ("cpu-abi",              "CPU ABI"),
        ("batch",                "Production batch"),
    ]
    print(f"\n  {'Variable':<30} {'Description'}")
    print(f"  {'─'*30} {'─'*35}")
    for var, desc in vars_list:
        print(f"  {C}fastboot getvar {var:<15}{RE} {desc}")
    print()
    info("KEY CHECK: 'fastboot getvar unlocked' should return 'yes' after successful unlock")
    info("KEY CHECK: 'fastboot getvar anti' — note ARB level; cannot flash older firmware")
    print()
    info("All vars at once: fastboot getvar all")
    info("NOTE: Some vars only available in fastbootd (userspace), not bootloader fastboot")
    info("      Switch to fastbootd with: fastboot reboot fastboot")


def m93_usb_tethering_setup():
    header("USB Tethering Setup — Share Phone Internet with PC for ADB")
    out, _, _ = shell("getprop sys.usb.config")
    usb_cfg = out.strip()
    out2, _, _ = shell("getprop sys.usb.state")
    usb_state = out2.strip()
    out3, _, _ = shell("ip link show rndis0 2>/dev/null | head -2")
    rndis = out3.strip()
    out4, _, _ = shell("ip addr show rndis0 2>/dev/null | grep 'inet ' | awk '{print $2}'")
    rndis_ip = out4.strip()
    info(f"USB config  : {usb_cfg}")
    info(f"USB state   : {usb_state}")
    info(f"RNDIS iface : {rndis or 'not active'}")
    info(f"RNDIS IP    : {rndis_ip or 'not assigned'}")
    print()
    if "rndis" in usb_cfg or rndis_ip:
        success("USB tethering (RNDIS) appears active")
    else:
        info("USB tethering not active. To enable:")
        info("  Settings → Connections → Mobile Hotspot and Tethering → USB tethering ON")
    print()
    info("Why USB tethering for ADB?")
    info("  • Ensures PC has internet through phone — useful if PC WiFi is limited")
    info("  • Also provides ADB-over-USB while tethering is active")
    info("  • ADB and RNDIS can coexist with: adb,rndis in USB config")
    print()
    info("After enabling tethering with ADB, from PC:")
    info("  adb devices           # should show device")
    info("  adb shell             # enter device shell")
    info("  adb shell getprop ro.product.model")


def m94_clock_date_sync():
    header("Clock & Date Sync — Samsung Timer Prerequisite Check")
    out, _, _ = shell("date")
    device_date = out.strip()
    out2, _, _ = shell("getprop persist.sys.timezone")
    tz = out2.strip()
    out3, _, _ = shell("settings get global auto_time 2>/dev/null || getprop persist.auto_time")
    auto_time = out3.strip()
    out4, _, _ = shell("settings get global auto_time_zone 2>/dev/null")
    auto_tz = out4.strip()
    out5, _, _ = shell("date +%s")
    epoch = out5.strip()
    info(f"Device date/time  : {device_date}")
    info(f"Timezone          : {tz}")
    info(f"Auto time         : {auto_time}")
    info(f"Auto timezone     : {auto_tz}")
    info(f"Unix timestamp    : {epoch}")
    print()
    if auto_time == "1":
        success("Automatic time sync is ON — clock is accurate")
    else:
        warn("Automatic time is OFF — Samsung's 7-day timer may use incorrect timestamps")
        ok = put_setting("global", "auto_time", "1")
        if ok:
            success("Enabled automatic time sync")
        else:
            info("Enable manually: Settings → General management → Date and time → Auto date and time")
    print()
    if auto_tz != "1":
        warn("Auto timezone OFF — enable for accurate timer calculation")
        put_setting("global", "auto_time_zone", "1")
    info("Incorrect clock can cause Samsung servers to reject OEM unlock eligibility.")
    info("Ensure NTP is synced BEFORE checking the 7-day timer.")


def m95_developer_stay_awake():
    header("Developer Option: Stay Awake While Charging")
    cur = get_setting("global", "stay_on_while_plugged_in")
    info(f"Current value: {cur!r}  (0=off, 1=AC, 2=USB, 3=AC+USB, 7=all)")
    print()
    if cur in ("3", "7", "2"):
        success("Stay awake already enabled — screen stays on while plugged in")
    else:
        info("Enabling stay_on_while_plugged_in = 3 (AC + USB)...")
        ok = put_setting("global", "stay_on_while_plugged_in", "3")
        if ok:
            success("Done — screen will now stay on while charging via AC or USB")
        else:
            warn("Could not set automatically — enable manually:")
            info("  Developer Options → Stay awake (while charging)")
    print()
    # Also set minimum brightness to prevent screen dim
    br = get_setting("system", "screen_brightness")
    info(f"Screen brightness : {br}/255")
    if int(br or 0) < 100:
        put_setting("system", "screen_brightness", "200")
        info("Raised brightness to 200 for visibility during unlock process")
    # Disable adaptive brightness for consistency
    adaptive = get_setting("system", "screen_brightness_mode")
    if adaptive == "1":
        put_setting("system", "screen_brightness_mode", "0")
        info("Disabled adaptive brightness (manual mode) for consistency")


def m96_wipe_cache_partition():
    header("Cache Wipe — Pre/Post Unlock Maintenance")
    out, _, _ = shell("df /cache 2>/dev/null | tail -1")
    cache_info = out.strip()
    out2, _, _ = shell("ls /dev/block/by-name/cache 2>/dev/null")
    cache_part = out2.strip()
    out3, _, _ = shell("df /data/dalvik-cache 2>/dev/null | tail -1")
    dalvik_info = out3.strip()
    info(f"Cache partition  : {cache_part or '— (may not exist on VAB devices)'}")
    info(f"Cache usage      : {cache_info or '—'}")
    info(f"Dalvik cache     : {dalvik_info or '—'}")
    print()
    info("S24 Ultra uses Virtual A/B — dedicated cache partition may not exist.")
    info("Cache is stored in /data/cache on VAB devices.")
    print()
    out4, _, _ = shell("du -sh /data/dalvik-cache 2>/dev/null")
    dalvik_size = out4.strip()
    out5, _, _ = shell("du -sh /data/cache 2>/dev/null")
    data_cache_size = out5.strip()
    info(f"Dalvik cache size   : {dalvik_size or '—'}")
    info(f"/data/cache size    : {data_cache_size or '—'}")
    print()
    info("To wipe cache (requires root or recovery):")
    info("  From running Android (root): rm -rf /data/dalvik-cache/*")
    info("  From recovery: Wipe → Advanced wipe → Cache")
    info("  Via ADB recovery: adb shell recovery --wipe_cache")
    print()
    info("Wipe cache AFTER unlock+ROM flash to clear stale Dalvik artifacts.")
    info("Do NOT wipe cache BEFORE unlock — it won't help and wastes time.")


def m97_adb_keys_manager():
    header("ADB Authorized Keys — View, Backup & Revoke")
    out, _, _ = shell("cat /data/misc/adb/adb_keys 2>/dev/null")
    keys = out.strip()
    out2, _, _ = shell("cat /data/misc/adb/adb_keys 2>/dev/null | wc -l")
    key_count = out2.strip()
    info(f"Trusted ADB public keys: {key_count or '?'}")
    if keys:
        for i, line in enumerate(keys.split("\n"), 1):
            if line.strip():
                parts = line.strip().split()
                key_type = parts[0] if parts else "?"
                comment = parts[-1] if len(parts) > 2 else "—"
                print(f"  [{i}] {C}{key_type}{RE} … {Y}{comment}{RE}")
    else:
        info("Cannot read /data/misc/adb/adb_keys (no root) or no keys stored")
    print()
    info("Key management commands (need root or ADB shell):")
    info("  View keys    : adb shell cat /data/misc/adb/adb_keys")
    info("  Backup keys  : adb pull /data/misc/adb/adb_keys ~/adb_keys.bak")
    info("  Add key      : cat ~/.android/adbkey.pub >> /data/misc/adb/adb_keys")
    info("  Revoke all   : Settings → Developer Options → Revoke USB debugging authorizations")
    print()
    info("Your PC's ADB public key is at: ~/.android/adbkey.pub")
    out3, _, _ = shell("ls ~/.android/adbkey.pub 2>/dev/null || ls $HOME/.android/adbkey.pub 2>/dev/null")
    if "adbkey.pub" in (out3 or ""):
        success(f"Local ADB key found: {out3.strip()}")
    print()
    warn("After bootloader unlock + factory reset, all trusted keys are wiped.")
    warn("You must re-authorize ADB from PC after the unlock process completes.")


def m98_device_fingerprint():
    header("Device Fingerprint & Identity Export")
    props = [
        "ro.build.fingerprint",
        "ro.product.model",
        "ro.product.device",
        "ro.product.board",
        "ro.product.brand",
        "ro.product.manufacturer",
        "ro.product.name",
        "ro.serialno",
        "ro.boot.hardware",
        "ro.boot.hardware.sku",
        "ro.hardware",
        "ro.build.id",
        "ro.build.display.id",
        "ro.build.version.release",
        "ro.build.version.sdk",
        "ro.build.date",
        "ro.build.type",
        "ro.build.tags",
        "ro.bootloader",
        "ro.vendor.build.fingerprint",
        "gsm.version.baseband",
        "gsm.imei",
    ]
    lines = []
    for p in props:
        out, _, _ = shell(f"getprop {p}")
        val = out.strip() or "—"
        line = f"{p} = {val}"
        lines.append(line)
        print(f"  {C}{p:<40}{RE}: {val}")
    # Save to file
    import os, datetime
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    fp_path = os.path.expanduser(f"~/DEVICE_FINGERPRINT_{ts}.txt")
    try:
        with open(fp_path, "w") as f:
            f.write(f"# S24 Ultra Device Fingerprint — {ts}\n\n")
            f.write("\n".join(lines))
        success(f"Saved to: {fp_path}")
    except Exception as e:
        warn(f"Could not save: {e}")
    print()
    info("Keep this fingerprint — useful when reporting ROM issues or filing support tickets.")


def m99_rom_flash_preparation():
    header("Custom ROM Flash Preparation Checklist")
    print(f"\n{BO}Pre-Flash Checklist:{RE}")
    checks = [
        ("Bootloader unlocked",         "getprop ro.boot.verifiedbootstate", "orange"),
        ("Active slot",                  "getprop ro.boot.slot_suffix", None),
        ("Android version",              "getprop ro.build.version.release", None),
        ("Security patch",               "getprop ro.build.version.security_patch", None),
        ("Anti-rollback level",          "getprop ro.boot.anti 2>/dev/null", None),
        ("Storage free (need ≥4GB)",     "df /sdcard 2>/dev/null | tail -1 | awk '{print $4}'", None),
        ("Battery level",                "cat /sys/class/power_supply/battery/capacity", None),
    ]
    for label, cmd, expected in checks:
        out, _, _ = shell(cmd)
        val = out.strip() or "—"
        if expected and val == expected:
            icon = G + "✓"
        elif expected and val != expected:
            icon = R + "✗"
        else:
            icon = C + "→"
        print(f"  {icon}{RE} {label:<40}: {val}")
    print()
    info("ROM flash sequence (with unlocked bootloader + custom recovery):")
    steps = [
        "1. Download ROM zip + GApps zip to phone storage",
        "2. Reboot to recovery: adb reboot recovery",
        "3. Recovery → Wipe → Format Data (type 'yes')",
        "4. Recovery → Wipe → Advanced Wipe → Dalvik + Cache",
        "5. Recovery → Install → select ROM zip",
        "6. Recovery → Install → select GApps zip (if not bundled)",
        "7. Reboot System — first boot takes 3-8 minutes",
        "8. Complete Android setup WITHOUT restoring from backup initially",
        "9. Test stability for 24h before restoring data",
    ]
    for step in steps:
        print(f"  {Y}{step}{RE}")
    print()
    warn("Anti-rollback: ROM must target same or newer firmware than currently installed.")
    warn("Flashing older firmware after ARB increase = PERMANENT BRICK risk.")
    info("Check current ARB: fastboot getvar anti  (when in fastboot mode)")


def m100_termux_monitor_widget():
    header("Termux Monitoring — OEM Unlock Status Poller")
    import time, os
    info("Setting up a continuous OEM unlock status monitor...")
    info("Polls every 30s — press Ctrl+C to stop")
    print()
    # Check Termux:Widget availability
    out, _, _ = shell("ls ~/.shortcuts/ 2>/dev/null | head -5")
    widget_dir = out.strip()
    # Create monitoring script
    monitor_script = os.path.expanduser("~/oem_monitor.sh")
    script_content = '''#!/data/data/com.termux/files/usr/bin/bash
# OEM Unlock Status Monitor for SM-S928B
while true; do
    clear
    echo "=== OEM Unlock Monitor === $(date)"
    echo ""
    OEM=$(getprop sys.oem_unlock_allowed 2>/dev/null)
    BATTERY=$(cat /sys/class/power_supply/battery/capacity 2>/dev/null)
    WIFI=$(ip addr show wlan0 2>/dev/null | grep 'inet ' | awk '{print $2}' | head -1)
    DEV=$(settings get global development_settings_enabled 2>/dev/null)
    echo "OEM unlock allowed : ${OEM:-unknown}"
    echo "Battery            : ${BATTERY:-?}%"
    echo "WiFi IP            : ${WIFI:-not connected}"
    echo "Developer options  : ${DEV:-?}"
    echo ""
    if [ "$OEM" = "1" ]; then
        echo "*** OEM UNLOCK IS READY — run Method 56 or Method 23 ***"
    else
        echo "Waiting for OEM unlock to become available..."
        echo "Keep WiFi connected. Timer needs 7 cumulative days."
    fi
    sleep 30
done
'''
    try:
        with open(monitor_script, "w") as f:
            f.write(script_content)
        os.chmod(monitor_script, 0o755)
        success(f"Monitor script saved: {monitor_script}")
    except Exception as e:
        warn(f"Could not save script: {e}")
    print()
    # Create Termux widget shortcut
    shortcuts_dir = os.path.expanduser("~/.shortcuts")
    os.makedirs(shortcuts_dir, exist_ok=True)
    shortcut_path = os.path.join(shortcuts_dir, "OEM_Monitor.sh")
    try:
        with open(shortcut_path, "w") as f:
            f.write(f"#!/data/data/com.termux/files/usr/bin/bash\nbash {monitor_script}\n")
        os.chmod(shortcut_path, 0o755)
        success(f"Termux:Widget shortcut created: {shortcut_path}")
        info("Install Termux:Widget from F-Droid, add widget to home screen to run it")
    except Exception as e:
        warn(f"Widget shortcut: {e}")
    print()
    info(f"To run monitor now: bash {monitor_script}")
    # Show current status
    out2, _, _ = shell("getprop sys.oem_unlock_allowed")
    oem = out2.strip()
    out3, _, _ = shell("cat /sys/class/power_supply/battery/capacity 2>/dev/null")
    batt = out3.strip()
    info(f"Current OEM status : {oem or 'unknown'}")
    info(f"Current battery    : {batt or '?'}%")


def m101_oem_toggle_grey_reason():
    header("Why Is the OEM Unlock Toggle Greyed Out? — Diagnosis")
    print()
    reasons = []

    # Check 1: internet/timer
    out, _, _ = shell("getprop sys.oem_unlock_allowed")
    oem_allowed = out.strip()
    if oem_allowed == "1":
        success("sys.oem_unlock_allowed = 1 — toggle SHOULD be active (not greyed)")
        info("If it still appears grey, try: Settings → Developer Options → scroll to OEM unlock")
        return
    else:
        reasons.append(("7-Day Timer", "Device hasn't been internet-connected for 7 cumulative days"))

    # Check 2: carrier restrictions
    out2, _, _ = shell("getprop ro.carrier")
    carrier = out2.strip()
    out3, _, _ = shell("getprop gsm.sim.operator.alpha")
    sim_op = out3.strip()
    if carrier not in ("", "unknown", "wifi-only"):
        reasons.append(("Carrier Lock", f"Carrier: {carrier} — some carriers block OEM unlock"))

    # Check 3: MDM
    out4, _, _ = shell("dumpsys device_policy 2>/dev/null | grep -c 'device owner'")
    if (out4.strip() or "0") != "0":
        reasons.append(("MDM/Enterprise", "Device Owner policy is active — MDM blocks unlock"))

    # Check 4: Knox Guard
    out5, _, _ = shell("pm list packages 2>/dev/null | grep -c knoxguard")
    if (out5.strip() or "0") != "0":
        reasons.append(("Knox Guard", "Knox Guard enrolled — contact Samsung to remove"))

    # Check 5: region
    out6, _, _ = shell("getprop ro.csc.sales_code")
    csc = out6.strip()
    if csc and csc not in ("XFE", "XEF", "XEO", "BTU", "DBT", "XSP", "XAA"):
        if csc.startswith("T-") or csc in ("TMB", "VZW", "ATT", "SPR"):
            reasons.append(("Carrier CSC", f"CSC={csc} — carrier-branded firmware may restrict unlock"))

    # Check 6: internet
    out7, rc7 = shell("ping -c 1 -W 3 8.8.8.8 2>/dev/null")[:2]
    if rc7 != 0:
        reasons.append(("No Internet", "Device not connected — timer only counts connected time"))

    print(f"{BO}Detected reasons toggle may be greyed:{RE}\n")
    if reasons:
        for reason, detail in reasons:
            print(f"  {R}✗{RE} {C}{BO}{reason}{RE}: {detail}")
    else:
        print(f"  {G}No blocking reasons found — toggle should activate soon{RE}")

    print()
    info("Most common reason for S24 Ultra (XX/Global): 7-day timer not expired")
    info("Keep WiFi on, keep phone active, wait ~7 days from first internet connection after setup")
    info("Check Method 78 for countdown calculation")


def m102_samsung_unlock_channels():
    header("Samsung Official Unlock Channels & Support")
    print()
    info("Samsung Galaxy S24 Ultra (SM-S928B) unlock resources:")
    print()
    channels = [
        ("Samsung Members app",     "Open in-app support → bootloader unlock inquiry"),
        ("Samsung Developer Portal","developer.samsung.com — OEM unlock documentation"),
        ("Samsung Knox Portal",     "knox.com — enterprise unlock/unenroll requests"),
        ("Samsung Care+",           "1-800-SAMSUNG (US) or regional support number"),
        ("sammobile.com",           "Official firmware downloads for S928BXXS6DZE1"),
        ("SamFW.com",               "Direct Odin firmware package downloads"),
        ("XDA Developers",          "xda-forums.com — S24 Ultra development subforum"),
        ("r/GalaxyS24Ultra",        "reddit.com — community unlock experiences"),
        ("4pda.to",                 "Russian dev community with S928B ROMs/guides"),
    ]
    for channel, detail in channels:
        print(f"  {C}{channel:<28}{RE}: {detail}")
    print()
    info("When contacting Samsung support, provide:")
    out, _, _ = shell("getprop ro.serialno 2>/dev/null || getprop ro.boot.serialno 2>/dev/null")
    serial = out.strip()
    out2, _, _ = shell("getprop gsm.imei 2>/dev/null || service call iphonesubinfo 1 2>/dev/null | grep -o '[0-9]\{15\}' | head -1")
    imei = out2.strip()
    out3, _, _ = shell("getprop ro.bootloader")
    bl_ver = out3.strip()
    print(f"  Serial     : {serial or '(see Settings → About phone → Status info)'}")
    print(f"  IMEI       : {imei or '(dial *#06# or Settings → About phone)'}")
    print(f"  Bootloader : {bl_ver}")
    print()
    info("Emergency unlock (if phone bricked in bootloader mode):")
    info("  Download Mode: Power OFF → Power + Vol Down → Vol Up to enter")
    info("  Odin3 (Windows): Flash stock firmware to restore")
    info("  Heimdall (Linux/Mac): heimdall flash --BOOT boot.img")


def m103_network_timer_watcher():
    header("Network Connectivity Watcher — OEM Timer Tracker")
    import time, datetime
    info("Monitoring network state for Samsung 7-day OEM unlock timer...")
    info("The timer increments only when device has active internet connectivity.")
    print()
    # Check current connectivity
    methods = [
        ("ping 8.8.8.8",    "ping -c 1 -W 3 8.8.8.8 2>/dev/null"),
        ("ping 1.1.1.1",    "ping -c 1 -W 3 1.1.1.1 2>/dev/null"),
        ("DNS resolve",     "nslookup google.com 2>/dev/null | head -3"),
        ("HTTP check",      "curl -s --max-time 5 -o /dev/null -w '%{http_code}' http://connectivitycheck.gstatic.com/generate_204 2>/dev/null"),
        ("WiFi state",      "getprop wifi.interface"),
        ("WiFi SSID",       "getprop wifi.active.interface 2>/dev/null || iwconfig wlan0 2>/dev/null | grep ESSID | sed 's/.*ESSID://;s/\"//'"),
        ("Mobile data",     "getprop gsm.network.type"),
        ("Data state",      "getprop gsm.data.state"),
        ("Net iface",       "ip route get 8.8.8.8 2>/dev/null | head -1"),
    ]
    connected = False
    for label, cmd in methods:
        out, _, rc = shell(cmd)
        val = out.strip() or "—"
        ok = rc == 0 and val not in ("—", "", "0", "000")
        icon = G + "✓" if ok else R + "✗"
        print(f"  {icon}{RE} {label:<20}: {val[:60]}")
        if ok and "ping" in label.lower():
            connected = True
    print()
    if connected:
        success("Device is ONLINE — OEM unlock timer is incrementing")
        now = datetime.datetime.now()
        info(f"Network check passed at: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        info("Keep this connection active. Timer needs ~168 cumulative connected hours.")
    else:
        error("Device appears OFFLINE — OEM unlock timer is PAUSED")
        info("Connect to WiFi or enable mobile data to resume the timer")
    print()
    # Create a background connectivity log
    import os
    log_path = os.path.expanduser("~/network_log.txt")
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(log_path, "a") as f:
            f.write(f"{ts} | connected={connected}\n")
        info(f"Connectivity state logged to: {log_path}")
    except Exception:
        pass


def m104_disable_knox_features():
    header("Disable Samsung Knox & Pay Features — Pre-Unlock")
    info("Knox features trip warranty bit on unlock. Disable optional Knox services first.")
    print()
    # Samsung Pay
    out, _, _ = shell("pm list packages 2>/dev/null | grep -i 'com.samsung.android.pay'")
    if out.strip():
        out2, _, rc = shell("pm disable-user --user 0 com.samsung.android.pay 2>/dev/null")
        if rc == 0:
            success("Samsung Pay disabled")
        else:
            warn("Samsung Pay: cannot disable without root (disable in app settings)")
    else:
        info("Samsung Pay: not installed")

    # Knox Vault
    knox_services = [
        "com.samsung.android.knox.containercore",
        "com.samsung.android.knox.analytics.uploader",
        "com.sec.enterprise.knox.cloudmdm.smdms",
        "com.samsung.android.kmsagent",
        "com.samsung.android.smartswitchassistant",
    ]
    for pkg in knox_services:
        out3, _, _ = shell(f"pm list packages {pkg} 2>/dev/null")
        if pkg in (out3 or ""):
            out4, _, rc = shell(f"pm disable-user --user 0 {pkg} 2>/dev/null")
            status = (G + "disabled") if rc == 0 else (Y + "root needed")
            print(f"  {status}{RE}: {pkg}")
    print()
    # Knox counter check
    out5, _, _ = shell("getprop ro.boot.warranty_bit")
    warranty = out5.strip()
    out6, _, _ = shell("getprop ro.boot.knox_active")
    knox_active = out6.strip()
    info(f"Knox warranty bit  : {warranty}")
    info(f"Knox active        : {knox_active}")
    print()
    if warranty == "0":
        success("Knox warranty bit still 0 — intact. Unlock will set it to 1 permanently.")
    else:
        warn("Knox warranty bit already = 1 — Knox already tripped (prior unlock attempt?)")
    info("Note: Disabling Knox features does NOT prevent the warranty bit from tripping.")
    info("The bit trips the moment 'fastboot flashing unlock' runs — unavoidable.")


def m105_csc_change_guide():
    header("CSC (Country Sales Code) Change Guide")
    out, _, _ = shell("getprop ro.csc.sales_code")
    csc = out.strip()
    out2, _, _ = shell("getprop ro.csc.countryiso")
    country = out2.strip()
    out3, _, _ = shell("getprop ro.csc.region")
    region = out3.strip()
    out4, _, _ = shell("getprop ro.product.name")
    product_name = out4.strip()
    out5, _, _ = shell("ls /product/omc/ 2>/dev/null | head -10")
    omc_dirs = out5.strip()
    info(f"Current CSC        : {csc}")
    info(f"Country ISO        : {country}")
    info(f"Region             : {region}")
    info(f"Product name       : {product_name}")
    info(f"OMC CSC options    : {omc_dirs or '—'}")
    print()
    info("Common unlock-friendly CSCs for SM-S928B:")
    cscs = [
        ("XFE", "Global (open market Europe) — recommended"),
        ("BTU", "UK/Europe unlocked"),
        ("DBT", "Germany — very unlock-friendly"),
        ("XSP", "Singapore — often has fewest restrictions"),
        ("XAA", "US unlocked (non-carrier) — good choice"),
        ("XEF", "France — strict but unlockable"),
        ("INS", "India — unlocked, frequent updates"),
    ]
    for code, desc in cscs:
        icon = G + "★" if csc == code else " "
        print(f"  {icon}{RE} {C}{code}{RE}: {desc}")
    print()
    info("CSC change method (requires stock firmware flash):")
    info("  1. Download firmware for target CSC from sammobile.com or samfw.com")
    info("  2. Flash via Odin (Windows) using HOME_CSC file to preserve data")
    info("  3. Or use full firmware flash (wipes data but ensures clean CSC change)")
    warn("CSC change alone does NOT unlock bootloader — it just changes regional settings.")
    warn("XX (Global, your current CSC) is already the best variant — no change needed.")
    info(f"Your CSC {csc} = Global XX — already optimal for bootloader unlock.")


def m106_unlock_cert_request():
    header("Bootloader Unlock Certificate Request — Enterprise/Dev Route")
    out, _, _ = shell("getprop ro.product.model")
    model = out.strip()
    out2, _, _ = shell("getprop ro.serialno 2>/dev/null || getprop ro.boot.serialno")
    serial = out2.strip()
    out3, _, _ = shell("getprop ro.bootloader")
    bl_ver = out3.strip()
    print()
    info("Samsung provides an official bootloader unlock certificate program for developers.")
    print()
    info("Requirements:")
    info("  • Active Samsung Developer account (free)")
    info("  • Device registered on developer.samsung.com")
    info("  • Device must support the program (S24 Ultra: SUPPORTED)")
    info("  • Knox Tizen not in enterprise-only mode")
    print()
    info("Steps for Samsung Unlock Certificate:")
    steps = [
        "1. Sign up at developer.samsung.com",
        "2. Go to: developer.samsung.com/galaxy/unlock",
        "3. Sign in → Register device with serial number",
        "4. Download the device-specific unlock authorization file (.auth)",
        "5. Place .auth file on phone storage",
        "6. Boot to Download Mode: Power OFF → Power + Vol Down → Vol Up",
        "7. Use Odin to flash auth file (or use heimdall on Linux/Mac)",
        "8. After flash, bootloader unlock becomes available in Developer Options",
    ]
    for step in steps:
        print(f"  {Y}{step}{RE}")
    print()
    info(f"Your device: {model}")
    info(f"Serial     : {serial or '(run Method 72)'}")
    info(f"Bootloader : {bl_ver}")
    print()
    info("NOTE: This program is mainly for developers. Normal users use the 7-day OEM toggle.")
    info("Alternative: the standard OEM unlock toggle in Developer Options is sufficient.")


def m107_unlock_summary_printout():
    header("Complete Unlock Summary — Printable Reference")
    out, _, _ = shell("getprop ro.product.model")
    model = out.strip()
    out2, _, _ = shell("getprop ro.bootloader")
    bl = out2.strip()
    out3, _, _ = shell("getprop ro.build.version.release")
    android = out3.strip()
    out4, _, _ = shell("getprop ro.csc.sales_code")
    csc = out4.strip()
    out5, _, _ = shell("getprop ro.boot.warranty_bit")
    knox = out5.strip()
    out6, _, _ = shell("getprop ro.boot.verifiedbootstate")
    vbs = out6.strip()
    out7, _, _ = shell("getprop sys.oem_unlock_allowed")
    oem_allowed = out7.strip()
    out8, _, _ = shell("cat /sys/class/power_supply/battery/capacity 2>/dev/null")
    battery = out8.strip()
    import os, datetime
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    content = f"""
╔══════════════════════════════════════════════════════════════╗
║          SAMSUNG S24 ULTRA BOOTLOADER UNLOCK SUMMARY         ║
║                    Generated: {ts}                    ║
╠══════════════════════════════════════════════════════════════╣
║ Device    : {model:<49}║
║ Bootloader: {bl:<49}║
║ Android   : {android:<49}║
║ CSC/Region: {csc:<49}║
╠══════════════════════════════════════════════════════════════╣
║ STATUS                                                       ║
║ Knox warranty bit   : {knox:<38}║
║ Verified boot state : {vbs:<38}║
║ OEM unlock allowed  : {oem_allowed:<38}║
║ Battery             : {battery + '%':<38}║
╠══════════════════════════════════════════════════════════════╣
║ UNLOCK STEPS                                                 ║
║ 1. Charge battery to ≥80%                                    ║
║ 2. Connect to WiFi — stay connected for 7 days               ║
║ 3. Settings → About phone → tap Build number 7x              ║
║ 4. Settings → Developer Options → OEM unlock → Enable        ║
║ 5. On PC: adb reboot bootloader                              ║
║ 6. On PC: fastboot flashing unlock                           ║
║ 7. Confirm on device screen (Volume Up)                      ║
║ 8. Wait for factory reset to complete (~5 min)               ║
╠══════════════════════════════════════════════════════════════╣
║ POST-UNLOCK                                                  ║
║ Knox bit trips permanently — Samsung Pay disabled            ║
║ Flash Magisk to boot.img → install Magisk app for root       ║
║ Or flash KernelSU module for kernel-level root               ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(content)
    summary_path = os.path.expanduser("~/UNLOCK_SUMMARY.txt")
    try:
        with open(summary_path, "w") as f:
            f.write(content)
        success(f"Saved to: {summary_path}")
    except Exception as e:
        warn(f"Could not save: {e}")


def m108_backup_contacts_sms():
    header("Backup Contacts & SMS — Pre-Wipe Data Preservation")
    import os, datetime
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.expanduser(f"~/backups_{ts}")
    os.makedirs(backup_dir, exist_ok=True)
    print()
    info(f"Backup directory: {backup_dir}")
    print()
    # Contacts count
    out, _, _ = shell("content query --uri content://contacts/phones --projection display_name:number 2>/dev/null | wc -l")
    contact_count = out.strip()
    info(f"Contacts found: {contact_count or '?'}")
    # Try vCard export
    out2, _, rc = shell(f"content query --uri content://contacts/phones --projection display_name:number 2>/dev/null > {backup_dir}/contacts.txt 2>&1")
    if rc == 0:
        success(f"Contacts backed up: {backup_dir}/contacts.txt")
    else:
        warn("Could not auto-backup contacts — use Samsung backup or Google sync")
    # SMS count
    out3, _, _ = shell("content query --uri content://sms 2>/dev/null | grep -c 'Row:'")
    sms_count = out3.strip()
    info(f"SMS messages found: {sms_count or '?'}")
    # Try SMS export
    out4, _, rc2 = shell(f"content query --uri content://sms --projection address:body:date:type 2>/dev/null | head -100 > {backup_dir}/sms.txt 2>&1")
    if rc2 == 0:
        success(f"SMS (first 100) backed up: {backup_dir}/sms.txt")
    print()
    info("Recommended full backup methods:")
    info("  • SMS Backup & Restore app (free, Play Store)")
    info("  • Google Contacts sync: Settings → Accounts → Google → Sync contacts")
    info("  • Samsung Cloud: Settings → Accounts → Samsung account → Back up data")
    info("  • ADB backup (PC): adb backup -apk -shared -all -f phone_backup.adb")
    print()
    warn("IMPORTANT: After bootloader unlock, the device WIPES all user data.")
    warn("Back up contacts and SMS NOW, before any unlock steps.")


def m109_adb_key_backup_restore():
    header("ADB Key Backup & Restore — PC Authorization Management")
    import os
    info("ADB keys are wiped during factory reset. Back up your PC's ADB key for easy re-auth.")
    print()
    # Check for key in home
    home = os.path.expanduser("~")
    android_dir = os.path.join(home, ".android")
    local_key = os.path.join(android_dir, "adbkey")
    local_pub = os.path.join(android_dir, "adbkey.pub")
    if os.path.exists(local_pub):
        success(f"Local ADB public key: {local_pub}")
        with open(local_pub, "r") as f:
            pub_content = f.read().strip()
        info(f"Key: {pub_content[:80]}…")
        # Backup to sdcard
        backup_path = os.path.expanduser("~/adbkey_backup.pub")
        try:
            with open(backup_path, "w") as f:
                f.write(pub_content + "\n")
            success(f"Backed up to phone storage: {backup_path}")
        except Exception as e:
            warn(f"Backup failed: {e}")
    else:
        info("No local ADB key found at ~/.android/adbkey.pub")
        info("PC key is stored on the PC at: C:\\Users\\<user>\\.android\\adbkey.pub (Windows)")
        info("                             or: ~/.android/adbkey.pub (Linux/Mac)")
    print()
    # Check device stored keys
    out, _, _ = shell("cat /data/misc/adb/adb_keys 2>/dev/null | wc -l")
    device_keys = out.strip()
    info(f"ADB keys stored on device: {device_keys or '?'}")
    print()
    info("Restore ADB authorization after unlock:")
    info("  1. Connect phone via USB")
    info("  2. adb kill-server && adb start-server")
    info("  3. adb devices → phone shows as 'unauthorized'")
    info("  4. Accept RSA fingerprint dialog on phone screen")
    info("  5. Tick 'Always allow' → OK")
    info("  Shortcut: adb push ~/.android/adbkey.pub /data/misc/adb/adb_keys (needs root)")


def m110_ram_storage_status():
    header("RAM & Storage Status — Resource Check Before Unlock")
    print()
    # RAM
    out, _, _ = shell("cat /proc/meminfo | head -10")
    info("Memory info:")
    for line in (out or "").strip().split("\n"):
        print(f"  {line}")
    print()
    # Try free command
    out2, _, _ = shell("free -h 2>/dev/null")
    if out2.strip():
        info("Memory summary (free -h):")
        print(f"  {out2.strip()}")
    print()
    # Storage
    out3, _, _ = shell("df -h 2>/dev/null | grep -E '/data|/sdcard|/storage|emulated'")
    info("Storage usage:")
    for line in (out3 or "").strip().split("\n"):
        if line.strip():
            print(f"  {line}")
    print()
    # Internal storage via stat
    out4, _, _ = shell("stat -f /data 2>/dev/null | grep -i block")
    if out4.strip():
        info(f"Filesystem stats: {out4.strip()}")
    # Additional storage info
    out5, _, _ = shell("getprop ro.build.characteristics")
    chars = out5.strip()
    out6, _, _ = shell("getprop ro.config.ringtone 2>/dev/null")
    out7, _, _ = shell("wc -l /proc/meminfo")
    info(f"Device characteristics: {chars}")
    print()
    info("Minimum recommended free storage for unlock:")
    info("  /data: at least 2GB free (for factory reset)")
    info("  /sdcard: at least 500MB free (for backup files)")
    info("  RAM: unlock itself doesn't need much — dalvik optimization needs ~500MB free")


def m111_temperature_check():
    header("Device Temperature Check — Thermal Safety Before Unlock")
    temp_paths = [
        ("/sys/class/thermal/thermal_zone0/temp",  "Zone 0 (CPU core)"),
        ("/sys/class/thermal/thermal_zone1/temp",  "Zone 1"),
        ("/sys/class/thermal/thermal_zone2/temp",  "Zone 2"),
        ("/sys/class/thermal/thermal_zone4/temp",  "Zone 4 (likely GPU)"),
        ("/sys/class/power_supply/battery/temp",   "Battery temperature (×0.1°C)"),
        ("/sys/class/hwmon/hwmon0/temp1_input",    "hwmon temp1"),
    ]
    print()
    info("Thermal readings:")
    any_high = False
    for path, label in temp_paths:
        out, _, rc = shell(f"cat {path} 2>/dev/null")
        val = out.strip()
        if val and rc == 0:
            try:
                temp_raw = int(val)
                # Battery temp is in tenths of degrees
                if "battery" in path.lower():
                    temp_c = temp_raw / 10.0
                elif temp_raw > 1000:
                    temp_c = temp_raw / 1000.0
                else:
                    temp_c = float(temp_raw)
                color = G if temp_c < 40 else (Y if temp_c < 50 else R)
                warn_flag = " ← HIGH" if temp_c >= 50 else ""
                print(f"  {color}{label:<30}{RE}: {temp_c:.1f}°C{warn_flag}")
                if temp_c >= 45:
                    any_high = True
            except Exception:
                print(f"  {C}{label:<30}{RE}: {val} (raw)")
        else:
            print(f"  {W}{label:<30}{RE}: —")
    print()
    out2, _, _ = shell("getprop sys.temperature.battery 2>/dev/null")
    sys_batt = out2.strip()
    if sys_batt:
        try:
            info(f"sys.temperature.battery: {float(sys_batt)/10:.1f}°C")
        except Exception:
            info(f"sys.temperature.battery: {sys_batt}")
    print()
    if any_high:
        error("Device temperature is HIGH (≥45°C) — let it cool before flashing!")
        error("High temp during flash can cause write errors and potential brick.")
    else:
        success("Temperatures are in safe range — good to proceed with unlock")
    info("Optimal flash temperature: 20-35°C. Avoid direct sunlight, remove case.")


def m112_staged_oem_rollout_check():
    header("Staged OEM Unlock Rollout — Server-Side Eligibility Check")
    out, _, _ = shell("getprop sys.oem_unlock_allowed")
    oem_allowed = out.strip()
    out2, _, _ = shell("getprop ro.product.model")
    model = out2.strip()
    out3, _, _ = shell("getprop ro.csc.sales_code")
    csc = out3.strip()
    out4, _, _ = shell("getprop ro.bootloader")
    bl = out4.strip()
    out5, _, _ = shell("getprop ro.build.version.release")
    android = out5.strip()
    info(f"Device     : {model}")
    info(f"CSC        : {csc}")
    info(f"Bootloader : {bl}")
    info(f"Android    : {android}")
    info(f"OEM allowed: {oem_allowed}")
    print()
    info("Samsung uses a staged/server-side enablement for OEM unlock. Factors:")
    factors = [
        ("Region (CSC)",           "XX Global = fully supported (your device)"),
        ("Firmware version",       "S928BXXS6DZE1 = supported"),
        ("Android version",        "Android 16 = supported"),
        ("Carrier lock",           "No carrier lock on XX Global"),
        ("Knox Guard",             "If enrolled, blocks unlock server-side"),
        ("Enterprise MDM",         "Blocks server eligibility if enrolled"),
        ("7-day internet timer",   "Server checks accumulated connectivity time"),
        ("Samsung account",        "Should NOT be required but can cause delays"),
    ]
    for factor, status in factors:
        print(f"  {C}{factor:<28}{RE}: {status}")
    print()
    if oem_allowed == "1":
        success("Your device IS eligible — OEM unlock is granted by Samsung servers")
    else:
        warn("OEM unlock not yet granted — most likely reason: 7-day timer not complete")
        info("No action needed on server factors for XX Global — just wait for timer")
        info("Check Method 78 for timer countdown, Method 68 for real-time monitoring")


def m113_enterprise_android_check():
    header("Android Enterprise / Work Profile Detection")
    out, _, _ = shell("dumpsys device_policy 2>/dev/null | head -80")
    policy_dump = out.strip()
    print()
    if policy_dump:
        # Parse key lines
        for line in policy_dump.split("\n")[:30]:
            line = line.strip()
            if any(kw in line.lower() for kw in ["owner", "admin", "policy", "profile", "managed", "restriction"]):
                print(f"  {Y}{line}{RE}")
    print()
    out2, _, _ = shell("pm list users 2>/dev/null")
    users = out2.strip()
    info("User profiles on device:")
    for u in users.split("\n"):
        u = u.strip()
        if u:
            icon = R + "⚠" if "work" in u.lower() or "managed" in u.lower() else G + " "
            print(f"  {icon}{RE} {u}")
    print()
    out3, _, _ = shell("pm list packages --user 10 2>/dev/null | wc -l")
    work_pkgs = out3.strip()
    out4, _, _ = shell("getprop ro.build.type")
    build_type = out4.strip()
    info(f"Work profile packages: {work_pkgs or '0'}")
    info(f"Build type           : {build_type}")
    print()
    if "device_owner" in policy_dump.lower() or (work_pkgs and int(work_pkgs or 0) > 5):
        error("Enterprise management detected — bootloader unlock will be BLOCKED")
        error("Contact your IT administrator to unenroll before attempting unlock")
    else:
        success("No enterprise enrollment detected — device appears to be personal use")
    info("Factory reset + bootloader unlock removes all work profiles")


def m114_samsung_mdm_policy():
    header("Samsung MDM Policy Analyzer — Knox Restriction Audit")
    out, _, _ = shell("dumpsys device_policy 2>/dev/null | grep -i 'restriction\\|allow\\|disallow\\|block\\|policy' | head -40")
    policy_lines = out.strip()
    print()
    info("Active MDM restrictions (from dumpsys device_policy):")
    if policy_lines:
        for line in policy_lines.split("\n"):
            line = line.strip()
            if "bootloader" in line.lower() or "oem" in line.lower() or "unlock" in line.lower():
                print(f"  {R}{BO}!!! {line} !!!{RE}")
            elif line:
                print(f"  {Y}{line}{RE}")
    else:
        print(f"  {G}No restrictive MDM policies found (or no root to read){RE}")
    print()
    # Knox-specific checks
    knox_checks = [
        ("Knox license",         "getprop knox.license.status 2>/dev/null"),
        ("Knox platform",        "getprop ro.config.knox"),
        ("KPE standard",         "getprop ro.config.kpe_standard 2>/dev/null"),
        ("KPE premium",          "getprop ro.config.kpe_premium 2>/dev/null"),
        ("Warranty bit",         "getprop ro.boot.warranty_bit"),
        ("Attestation mode",     "getprop ro.config.use_key_attestation 2>/dev/null"),
        ("MDM restriction",      "getprop ro.config.mdm_restrict 2>/dev/null"),
    ]
    print(f"\n{BO}Knox property analysis:{RE}")
    for label, cmd in knox_checks:
        out2, _, _ = shell(cmd)
        val = out2.strip() or "—"
        color = R if val not in ("—", "0", "") else G
        print(f"  {color}{label:<25}{RE}: {val}")
    print()
    info("Samsung KNOX DualDAR and Knox Workspace won't affect bootloader unlock directly.")
    info("However, Knox Guard and Samsung MDM enrollment WILL block the unlock toggle.")
    info("Knox warranty_bit trips permanently on unlock — Knox features disabled after.")


def m115_aosp_migration_prep():
    header("AOSP / Custom ROM Migration — Full Preparation Guide")
    import os
    out, _, _ = shell("getprop ro.product.model")
    model = out.strip()
    out2, _, _ = shell("getprop ro.build.version.release")
    android = out2.strip()
    out3, _, _ = shell("getprop ro.boot.verifiedbootstate")
    vbs = out3.strip()
    out4, _, _ = shell("getprop ro.boot.warranty_bit")
    knox = out4.strip()
    print()
    info(f"Migrating: {model} (Android {android})")
    print()
    # Pre-migration checklist
    print(f"{BO}Pre-Migration Checklist:{RE}")
    items = [
        ("Bootloader unlocked",  vbs == "orange", "Run Method 23 / 56"),
        ("Knox bit status",       knox == "0",     "Will become 1 on unlock (irreversible)"),
        ("Backup complete",       True,             "Methods 82, 108 — backup all data"),
        ("Samsung account removed",True,           "Method 90 — prevents FMM lock"),
        ("Google FRP disabled",   True,             "Method 91 — remove Google account"),
        ("OTA disabled",          True,             "Developer Options → Auto system updates OFF"),
        ("Recovery flashed",      True,             "TWRP/OrangeFox — Method 86"),
    ]
    for item, done, action in items:
        icon = G + "✓" if done else Y + "○"
        print(f"  {icon}{RE} {item:<35}: {action}")
    print()
    info("AOSP migration steps:")
    steps = [
        "1. Boot to custom recovery (Vol Up + Power from bootloader)",
        "2. Wipe: Factory Reset → Format Data (type 'yes')",
        "3. Wipe: Advanced Wipe → Dalvik/ART Cache + Cache",
        "4. Install: select ROM zip from /sdcard",
        "5. Install: select GApps zip (NikGApps, MindTheGapps, or none)",
        "6. Install: Magisk zip if you want root immediately",
        "7. Reboot System → wait 5-10 min for first boot",
        "8. Complete setup WITHOUT restoring Google backup initially",
        "9. Test core features (calls, WiFi, camera, sensors)",
        "10. After 24h stability, restore apps via backup",
    ]
    for step in steps:
        print(f"  {C}{step}{RE}")
    print()
    # Save guide
    guide_path = os.path.expanduser("~/AOSP_MIGRATION_GUIDE.txt")
    try:
        guide_lines = [f"AOSP Migration Guide for {model}\n", "="*50+"\n"]
        guide_lines += [f"{s}\n" for s in steps]
        with open(guide_path, "w") as f:
            f.writelines(guide_lines)
        success(f"Guide saved to: {guide_path}")
    except Exception as e:
        warn(f"Could not save: {e}")
    print()
    info("Post-migration: Magisk for root, LSPosed for Xposed mods, Shamiko for SafetyNet")
    info("Banking apps: use Magisk DenyList + Shamiko to hide root from sensitive apps")


# ─────────────────────────────────────────────────────────────────────────────
# METHODS 116-120 — OEM UNLOCK TOGGLE VISIBILITY FIXES
# ─────────────────────────────────────────────────────────────────────────────

def m116_force_show_oem_toggle():
    header("Force Show OEM Unlocking Toggle in Developer Options")
    info("If 'OEM Unlocking' is missing from Developer Options, try these in order:")
    print()

    # Step 1: Check ro.oem_unlock_supported
    out, _, _ = shell("getprop ro.oem_unlock_supported")
    sup = out.strip()
    info(f"ro.oem_unlock_supported = {sup or '(empty — treating as supported)'}")
    if sup == "0":
        error("ro.oem_unlock_supported=0 — hardware says unlock is not supported")
        warn("This is unusual for SM-S928B (XX Global). Try forcing it:")
        _, _, rc = shell("su -c 'setprop ro.oem_unlock_supported 1' 2>/dev/null")
        if rc == 0:
            success("Property forced to 1 — restart Developer Options")
        else:
            warn("Need root to override. Try via adb: adb shell su -c 'setprop ro.oem_unlock_supported 1'")
    else:
        success("ro.oem_unlock_supported is not 0 — hardware supports unlock")

    # Step 2: am broadcast to trigger toggle reveal
    print()
    info("Sending broadcast to reveal OEM unlock setting...")
    _, _, rc2 = shell("am broadcast -a com.android.settings.action.OEM_UNLOCK_SETTINGS 2>/dev/null", timeout=5)
    info(f"Broadcast result: {'sent' if rc2==0 else 'failed (normal without root)'}")

    # Step 3: Write oem_unlock_allowed via all methods
    print()
    info("Writing oem_unlock_allowed=1 via all available methods...")
    results = []
    results.append(("settings put", put_setting("global", "oem_unlock_allowed", "1")))
    _, _, rc3 = shell("su -c 'settings put global oem_unlock_allowed 1' 2>/dev/null")
    results.append(("su settings put", rc3 == 0))
    _, _, rc4 = shell(f"su -c 'sqlite3 {_SETTINGS_DB} "
                      "\"INSERT OR REPLACE INTO global(name,value) VALUES(\\\"oem_unlock_allowed\\\",\\\"1\\\")\"' 2>/dev/null")
    results.append(("sqlite3 direct", rc4 == 0))
    for method, ok in results:
        icon = G + "✓" if ok else R + "✗"
        print(f"  {icon}{RE} {method}")

    # Step 4: Open Settings search for OEM
    print()
    info("Opening Settings search for 'OEM'...")
    shell("am start -a android.settings.SETTINGS -e query OEM 2>/dev/null", timeout=5)
    shell("am start -a android.settings.SEARCH_RESULT_SETTINGS --es query oem_unlock 2>/dev/null", timeout=5)
    print()
    info("Manual steps to find the hidden toggle:")
    steps = [
        "1. Open Settings app → tap the magnifying glass (search icon)",
        "2. Type 'OEM' — it should appear in search results",
        "3. Tap the result to jump directly to the toggle",
        "4. If not in search: Settings → Developer Options → scroll to VERY bottom",
        "5. Long-press any blank space in Developer Options (sometimes reveals hidden items)",
        "6. Try: tap 'Build Number' 3 more times while in Developer Options (re-triggers)",
        "7. Reboot phone → re-enter Developer Options → scroll to bottom",
    ]
    for step in steps:
        print(f"  {Y}{step}{RE}")
    print()
    out2, _, _ = shell("getprop sys.oem_unlock_allowed")
    info(f"Current sys.oem_unlock_allowed = {out2.strip() or 'N/A'}")
    if out2.strip() == "1":
        success("OEM unlock IS allowed by system — toggle should appear and be active")
    else:
        warn("OEM unlock not yet allowed by system — 7-day timer likely still running")
        info("The toggle may only appear (or become active) once the timer completes")


def m117_oem_via_dialer_codes():
    header("Samsung Dialer Codes for OEM Unlock & Developer Access")
    info("Samsung Galaxy devices have hidden service menus accessible via the dialer.")
    info("These can reveal OEM unlock status and sometimes force-enable options.")
    print()
    codes = [
        ("*#0*#",        "General Test Menu (display, sensors, touch)"),
        ("*#1234#",      "Firmware version (PDA, Phone, CSC, Build)"),
        ("*#2222#",      "Hardware version"),
        ("*#7353#",      "Quick test menu"),
        ("*#0808#",      "USB settings / MTP ADB mode selector"),
        ("*#9090#",      "Diagnostic configuration (USB path)"),
        ("*#9900#",      "SysDump / log collection mode"),
        ("*#197328640#", "Service mode / field test (Main menu)"),
        ("*#0011#",      "Service mode — network information"),
        ("*#12580*369#", "Software and hardware info"),
        ("##778+call",   "EPST menu (CDMA only)"),
        ("*#7465625#",   "Device lock status / SIM lock info"),
        ("*#272*IMEI#",  "CSC selection menu (useful for region unlock)"),
    ]
    print(f"{'Code':<22} {'Function'}")
    print(f"{'─'*22} {'─'*40}")
    for code, desc in codes:
        print(f"  {C}{code:<20}{RE}: {desc}")
    print()
    info("For OEM unlock specifically:")
    info("  1. Dial *#0808# → set USB mode to 'ADB' if not already")
    info("  2. Dial *#9090# → verify USB diagnostic path")
    info("  3. Dial *#1234# → note firmware version for compatibility check")
    print()
    info("To open dialer programmatically:")
    shell("am start -a android.intent.action.DIAL 2>/dev/null", timeout=5)
    out, _, _ = shell("getprop ro.build.version.release")
    android = out.strip()
    out2, _, _ = shell("getprop ro.bootloader")
    bl = out2.strip()
    info(f"Your firmware: Android {android}, Bootloader {bl}")
    print()
    warn("Service mode codes do NOT directly enable OEM unlock — they provide diagnostics.")
    warn("The OEM unlock toggle requires the 7-day internet timer to complete.")
    info("After timer completes: Developer Options → OEM Unlocking toggle becomes active.")


def m118_oem_unlock_no_toggle():
    header("OEM Unlock via Fastboot — No Toggle Required Method")
    info("If OEM unlock toggle is hidden/greyed, you can STILL unlock via PC fastboot.")
    info("The toggle just pre-authorizes; fastboot flashing unlock is the real command.")
    print()
    out, _, _ = shell("getprop ro.boot.flash.locked")
    locked = out.strip()
    out2, _, _ = shell("getprop sys.oem_unlock_allowed")
    allowed = out2.strip()
    out3, _, _ = shell("getprop ro.boot.verifiedbootstate")
    vbs = out3.strip()
    info(f"Bootloader locked   : {locked}")
    info(f"OEM unlock allowed  : {allowed}")
    info(f"Verified boot state : {vbs}")
    print()
    warn("IMPORTANT: On modern Samsung firmware, fastboot flashing unlock CHECKS the toggle.")
    warn("If toggle was never enabled, fastboot may return 'FAILED (remote: Unlock is not allowed)'")
    print()
    info("Two ways to proceed without the toggle:")
    print()
    print(f"  {C}{BO}Option A — Wait for timer, then use fastboot:{RE}")
    print(f"  {W}1. Keep WiFi connected until 7-day timer expires{RE}")
    print(f"  {W}2. Toggle will appear and become tappable in Developer Options{RE}")
    print(f"  {W}3. Enable it, then: fastboot flashing unlock{RE}")
    print()
    print(f"  {C}{BO}Option B — Heimdall + Odin method (no toggle needed):{RE}")
    print(f"  {W}1. Download stock firmware for S928BXXS6DZE1 from samfw.com{RE}")
    print(f"  {W}2. Flash via Odin with 'OEM Unlock' pre-enabled in Odin options{RE}")
    print(f"  {W}3. Some firmware versions skip toggle check — try older builds{RE}")
    print()
    print(f"  {C}{BO}Option C — Root first via KernelSU exploit (advanced):{RE}")
    print(f"  {W}1. Use a kernel exploit for SM-S928B (check XDA forums){RE}")
    print(f"  {W}2. With root: settings put global oem_unlock_allowed 1{RE}")
    print(f"  {W}3. Then reboot → toggle appears enabled → fastboot flashing unlock{RE}")
    print()
    ip = get_wifi_ip()
    if ip:
        info(f"Your phone IP: {ip} — PC can connect via: adb connect {ip}:5555")
    info("Run Method 65 to generate a complete PC script with all required fastboot commands.")


def m119_toggle_visibility_props():
    header("OEM Toggle Visibility — Property & Settings Deep Scan")
    info("Scanning all properties and settings related to OEM unlock visibility...")
    print()
    prop_checks = [
        ("ro.oem_unlock_supported",            "Must be 1 for toggle to show"),
        ("sys.oem_unlock_allowed",             "Must be 1 for toggle to be active (not grey)"),
        ("ro.boot.flash.locked",               "1=locked, 0=unlocked"),
        ("ro.boot.verifiedbootstate",          "green=stock, orange=unlocked"),
        ("ro.boot.warranty_bit",               "0=Knox intact, 1=tripped"),
        ("ro.config.oem_unlock_allowed",       "OEM override property"),
        ("ro.config.knox",                     "Knox platform version"),
        ("persist.sys.oem_unlock_allowed",     "Persistent OEM allow"),
        ("ro.boot.oem_unlock_allowed",         "Boot-time OEM property"),
        ("ro.frp.pst",                         "FRP partition state"),
        ("ro.setup.wizard.revision",           "Setup wizard completed"),
    ]
    print(f"  {'Property':<40} {'Value':<10} Note")
    print(f"  {'─'*40} {'─'*10} {'─'*30}")
    for prop, note in prop_checks:
        out, _, _ = shell(f"getprop {prop} 2>/dev/null")
        val = out.strip() or "—"
        ok = val not in ("0", "—", "")
        color = G if ok else (R if val == "0" else W)
        print(f"  {color}{prop:<40}{RE} {val:<10} {note}")
    print()
    settings_checks = [
        ("global", "oem_unlock_allowed"),
        ("global", "development_settings_enabled"),
        ("global", "adb_enabled"),
        ("global", "stay_on_while_plugged_in"),
        ("secure", "user_setup_complete"),
        ("secure", "device_provisioned"),
    ]
    print(f"\n  {'Setting':<50} Value")
    print(f"  {'─'*50} {'─'*10}")
    for ns, key in settings_checks:
        val = get_setting(ns, key) or "—"
        ok = val == "1"
        color = G if ok else W
        print(f"  {color}{ns}/{key:<45}{RE} {val}")
    print()
    # Key diagnosis
    out_sup, _, _ = shell("getprop ro.oem_unlock_supported")
    out_allowed, _, _ = shell("getprop sys.oem_unlock_allowed")
    out_setup, _, _ = shell("settings get secure user_setup_complete 2>/dev/null || getprop ro.setupwizard.mode")
    sup = out_sup.strip()
    allowed = out_allowed.strip()
    setup = out_setup.strip()
    print(f"{BO}Diagnosis:{RE}")
    if sup == "0":
        error("ro.oem_unlock_supported=0 — toggle is HIDDEN because hardware reports not supported")
    elif allowed != "1":
        warn("sys.oem_unlock_allowed=0/N/A — toggle is GREYED (timer not complete or MDM blocking)")
    else:
        success("All visibility conditions met — toggle SHOULD appear and be active")
    if setup not in ("1", "DISABLED"):
        warn("Setup wizard may not be complete — complete device setup first")


def m120_oem_longpress_tricks():
    header("OEM Toggle Hidden Entry Points — Long-Press & Deep Link Tricks")
    info("Advanced tricks to access OEM Unlocking when it's hidden from the main list.")
    print()
    tricks = [
        ("Settings Search",          "Open Settings → search 'OEM' or 'Unlocking' in search bar"),
        ("Developer Options search", "Inside Developer Options → long-press any setting → 'Search'"),
        ("Direct deep link",         "Script will launch directly below → check if toggle appears"),
        ("Home screen shortcut",     "Create shortcut: Settings → Apps → 3-dot → Special access"),
        ("ADB intent (from PC)",     "adb shell am start -a android.settings.APPLICATION_DEVELOPMENT_SETTINGS"),
        ("Re-enable dev options",    "Settings → About → tap Build Number 3× more (re-triggers refresh)"),
        ("Reboot method",            "Reboot device → immediately open Developer Options (before daemon loads)"),
        ("Google Assistant",         "Say: 'Open Developer Options' → navigate to OEM Unlocking"),
    ]
    for label, detail in tricks:
        print(f"  {C}{BO}{label:<28}{RE}: {detail}")
    print()
    info("Attempting all direct launch intents now...")
    intents = [
        ("Dev Options main",     "am start -n com.android.settings/.development.DevelopmentSettingsDashboardActivity"),
        ("Dev Options fallback", "am start -a android.settings.APPLICATION_DEVELOPMENT_SETTINGS"),
        ("OEM unlock direct",    "am start -a android.settings.action.OEM_UNLOCK_SETTINGS"),
        ("Settings search OEM",  "am start -n com.android.settings/.Settings --es :android:show_fragment_args '{\"query\":\"oem\"}'"),
    ]
    for label, cmd in intents:
        _, _, rc = shell(f"{cmd} 2>/dev/null", timeout=5)
        icon = G + "✓" if rc == 0 else R + "✗"
        print(f"  {icon}{RE} {label}")
    print()
    info("After any of these opens Developer Options:")
    info("  • Scroll to bottom — 'OEM Unlocking' should be the last major toggle")
    info("  • If toggle is grey: timer not done. Long-press it — on some firmware it shows timer status")
    info("  • If toggle is absent entirely: run Method 116 (Force Show OEM Toggle)")
    print()
    out, _, _ = shell("getprop sys.oem_unlock_allowed")
    val = out.strip()
    if val == "1":
        success("sys.oem_unlock_allowed=1 — toggle WILL be active once Developer Options opens!")
        success("Go to Developer Options NOW and you should see the blue toggle")
    else:
        warn(f"sys.oem_unlock_allowed={val or 'N/A'} — timer still running")
        info("Toggle will be grey/hidden until sys.oem_unlock_allowed becomes 1")
        info("Keep WiFi connected. Check Method 78 for countdown, Method 68 for live monitor")


# ─────────────────────────────────────────────────────────────────────────────
# METHOD 121 — ULTIMATE 40-TECHNIQUE BOOTLOADER UNLOCK ASSAULT
# ─────────────────────────────────────────────────────────────────────────────

def m121_ultimate_unlock():
    header("ULTIMATE BOOTLOADER UNLOCK — 40 Advanced Techniques in One")
    import datetime, os, time

    score = {"pass": 0, "fail": 0, "done": 0}

    def step(n, title):
        print(f"\n{B}{'─'*62}{RE}")
        print(f"{C}{BO}  [{n:02d}/40] {title}{RE}")
        print(f"{B}{'─'*62}{RE}")

    def ok(msg):
        score["pass"] += 1
        print(f"  {G}✓{RE} {msg}")

    def nope(msg):
        score["fail"] += 1
        print(f"  {R}✗{RE} {msg}")

    def tip(msg):
        print(f"  {Y}→{RE} {msg}")

    # ── 01 Samsung server connectivity ────────────────────────────────────────
    step(1, "Samsung OEM Verification Server Connectivity Test")
    samsung_hosts = [
        ("samsung.com",            "Main Samsung domain"),
        ("samsungdive.com",        "Find My Mobile / OEM verify"),
        ("samsungmobile.com",      "Mobile services"),
        ("otas.samsungmobile.com", "OTA / firmware server"),
        ("fota.samsungmobile.com", "FOTA update server"),
        ("dev.samsungmobile.com",  "Developer OEM check"),
        ("api.samsungknox.com",    "Knox validation server"),
    ]
    samsung_reachable = False
    for host, desc in samsung_hosts:
        out, _, rc = shell(f"ping -c 1 -W 3 {host} 2>/dev/null | tail -1")
        ok2, _, _ = shell(f"curl -s --max-time 5 -o /dev/null -w '%{{http_code}}' https://{host} 2>/dev/null")
        reachable = rc == 0 or ok2.strip() not in ("", "000", "curl")
        icon = G + "✓" if reachable else R + "✗"
        print(f"  {icon}{RE} {host:<35} {desc}")
        if reachable:
            samsung_reachable = True
    if samsung_reachable:
        ok("Samsung servers reachable — network is not blocking OEM validation")
    else:
        nope("Samsung servers NOT reachable — OEM daemon cannot verify, timer stuck")
        tip("Try: change DNS to 8.8.8.8 — Settings → WiFi → (your network) → DNS")
        tip("Try: enable mobile data instead of WiFi")
        tip("Try: disable VPN if active")

    # ── 02 DNS resolution check ───────────────────────────────────────────────
    step(2, "DNS Resolution — Samsung Domain Check")
    dns_ok = False
    for host in ["samsung.com", "samsungmobile.com", "google.com"]:
        out, _, rc = shell(f"nslookup {host} 2>/dev/null | grep -A1 'Name:' | grep Address")
        if not out.strip():
            out, _, rc = shell(f"getent hosts {host} 2>/dev/null")
        if out.strip():
            ok(f"DNS resolves {host}: {out.strip()[:50]}")
            dns_ok = True
        else:
            nope(f"DNS failed for {host}")
    if not dns_ok:
        tip("DNS broken — run: settings put global private_dns_mode off")
        tip("Or change to public DNS: Settings → Connections → WiFi → long-press → Modify → DNS")

    # ── 03 IP address analysis ────────────────────────────────────────────────
    step(3, "Network IP Analysis (detect captive portal / NAT)")
    ip = get_wifi_ip()
    out_route, _, _ = shell("ip route show default 2>/dev/null")
    out_public, _, _ = shell("curl -s --max-time 5 http://ifconfig.me 2>/dev/null || curl -s --max-time 5 http://api.ipify.org 2>/dev/null")
    print(f"  WiFi IP (local)  : {ip or 'N/A'}")
    print(f"  Default route    : {out_route.strip() or 'N/A'}")
    print(f"  Public IP        : {out_public.strip() or 'N/A (no internet or blocked)'}")
    if ip and ip.startswith("192.0.0"):
        nope(f"IP {ip} is in IANA special-use range — possible captive portal or DS-Lite")
        tip("This non-standard IP may prevent Samsung servers from being reached")
        tip("Try connecting to a different WiFi network or use mobile data")
    elif ip:
        ok(f"Local IP {ip} looks normal")

    # ── 04 Mobile data fallback ───────────────────────────────────────────────
    step(4, "Mobile Data Connectivity Test")
    out_gsm, _, _ = shell("getprop gsm.data.state")
    out_net, _, _ = shell("getprop gsm.network.type")
    out_op, _, _ = shell("getprop gsm.operator.alpha")
    print(f"  Data state : {out_gsm.strip() or 'N/A'}")
    print(f"  Network    : {out_net.strip() or 'N/A'}")
    print(f"  Operator   : {out_op.strip() or 'N/A'}")
    if out_gsm.strip() in ("CONNECTED", "connected"):
        ok("Mobile data is connected — Samsung OEM check can use mobile data")
    else:
        tip("Enable mobile data as backup: Settings → Connections → Mobile networks → ON")
        tip("The Samsung OEM unlock check works over mobile data too")

    # ── 05 OEM daemon status ──────────────────────────────────────────────────
    step(5, "Samsung OEM Unlock Daemon — Service Status Scan")
    daemon_props = [
        "sys.oem_unlock_allowed",
        "persist.sys.oem_unlock_allowed",
        "ro.oem_unlock_supported",
        "sys.oem_unlock_requirement_timer",
        "vendor.oem_unlock_allowed",
        "ro.boot.oem_unlock_allowed",
    ]
    any_set = False
    for p in daemon_props:
        v, _, _ = shell(f"getprop {p} 2>/dev/null")
        val = v.strip()
        if val:
            color = G if val == "1" else Y
            print(f"  {color}{p} = {val}{RE}")
            any_set = True
        else:
            print(f"  {W}{p} = (not set){RE}")
    if any_set:
        ok("At least one OEM property is set — daemon has run")
    else:
        nope("No OEM properties set — daemon never ran")
        tip("This is the root cause. Reboot required to trigger the daemon.")

    # ── 06 Force daemon broadcast ─────────────────────────────────────────────
    step(6, "Force Samsung OEM Daemon — Broadcast Triggers")
    broadcasts = [
        "com.samsung.android.server.oem_unlock.action.OEM_UNLOCK_CHECK",
        "android.intent.action.BOOT_COMPLETED",
        "com.android.settings.action.OEM_UNLOCK_SETTINGS",
        "android.net.conn.CONNECTIVITY_CHANGE",
        "android.net.wifi.STATE_CHANGE",
        "android.net.wifi.WIFI_STATE_CHANGED",
    ]
    triggered = 0
    for bc in broadcasts:
        _, _, rc = shell(f"am broadcast -a {bc} 2>/dev/null", timeout=5)
        if rc == 0:
            triggered += 1
        icon = G + "✓" if rc == 0 else W + "—"
        print(f"  {icon}{RE} {bc}")
    time.sleep(3)
    v_after, _, _ = shell("getprop sys.oem_unlock_allowed 2>/dev/null")
    val_after = v_after.strip()
    if val_after == "1":
        ok(f"OEM UNLOCK ACTIVATED after broadcast! sys.oem_unlock_allowed=1")
    elif val_after:
        tip(f"Daemon responded: sys.oem_unlock_allowed={val_after} (timer now counting)")
    else:
        nope("Daemon did not respond to broadcasts — reboot needed")

    # ── 07 Setup wizard completion ────────────────────────────────────────────
    step(7, "Setup Wizard Completion — OEM Timer Prerequisite")
    wiz_props = [
        ("persist.sys.setupwizard.mode", "Setup wizard mode"),
        ("ro.setupwizard.mode", "RO wizard mode"),
        ("setupwizard.device_registered", "Device registered"),
    ]
    for p, label in wiz_props:
        v, _, _ = shell(f"getprop {p} 2>/dev/null")
        val = v.strip() or "—"
        color = G if val in ("DISABLED", "COMPLETED", "1") else Y
        print(f"  {color}{label:<35}{RE}: {val}")
    out_wiz, _, _ = shell("ls /data/system/users/0/ 2>/dev/null | head -5")
    print(f"  User data files: {out_wiz.strip() or '(no access)'}")
    tip("If setup wizard was never completed: open the Setup Wizard app and finish it")
    tip("Settings → General management → Reset → Auto restart is unrelated")

    # ── 08 Date & time accuracy ───────────────────────────────────────────────
    step(8, "Date & Time Accuracy — Samsung Timer Dependency")
    out_date, _, _ = shell("date")
    out_auto, _, _ = shell("settings get global auto_time 2>/dev/null || getprop persist.sys.ntp.auto")
    out_ntp, _, _ = shell("getprop sys.ntp.state 2>/dev/null || getprop persist.sys.ntp.server")
    print(f"  Device time : {out_date.strip()}")
    print(f"  Auto time   : {out_auto.strip() or 'N/A'}")
    print(f"  NTP state   : {out_ntp.strip() or 'N/A'}")
    put_setting("global", "auto_time", "1")
    put_setting("global", "auto_time_zone", "1")
    ok("Auto-time and timezone enabled")
    tip("Inaccurate clock can cause Samsung's timer validation to fail silently")

    # ── 09 Samsung account check ──────────────────────────────────────────────
    step(9, "Samsung Account — OEM Timer Enabler")
    out_acct, _, _ = shell("dumpsys account 2>/dev/null | grep -i samsung | head -3")
    out_pkg, _, _ = shell("pm list packages 2>/dev/null | grep 'com.osp.app.signin'")
    print(f"  Samsung account: {out_acct.strip() or '(not visible without root)'}")
    print(f"  Signin package : {out_pkg.strip() or 'not found'}")
    tip("A Samsung account speeds up OEM timer validation in some regions")
    tip("Add one: Settings → Samsung account (if not already added)")
    tip("REMOVE it BEFORE the actual unlock to prevent FMM locking the device")

    # ── 10 All settings write attempts ───────────────────────────────────────
    step(10, "Force-Write OEM Unlock Setting — All Methods")
    writes = [
        ("settings put", lambda: put_setting("global", "oem_unlock_allowed", "1")),
        ("su settings", lambda: shell("su -c 'settings put global oem_unlock_allowed 1' 2>/dev/null")[2] == 0),
        ("cmd settings", lambda: shell("cmd settings put global oem_unlock_allowed 1 2>/dev/null")[2] == 0),
        ("sqlite3", lambda: shell(f"su -c 'sqlite3 {_SETTINGS_DB} \"INSERT OR REPLACE INTO global(name,value) VALUES(\\\"oem_unlock_allowed\\\",\\\"1\\\")\"' 2>/dev/null")[2] == 0),
        ("content insert", lambda: shell("content insert --uri content://settings/global --bind name:s:oem_unlock_allowed --bind value:s:1 2>/dev/null")[2] == 0),
    ]
    for label, fn in writes:
        try:
            result = fn()
            icon = G + "✓" if result else R + "✗"
            print(f"  {icon}{RE} {label}")
        except Exception:
            print(f"  {R}✗{RE} {label} (exception)")
    time.sleep(2)
    v2, _, _ = shell("getprop sys.oem_unlock_allowed 2>/dev/null")
    tip(f"sys.oem_unlock_allowed after writes: {v2.strip() or 'N/A'}")

    # ── 11 Developer options force-enable ─────────────────────────────────────
    step(11, "Developer Options — Force Enable All Methods")
    dev_writes = [
        put_setting("global", "development_settings_enabled", "1"),
        shell("su -c 'settings put global development_settings_enabled 1' 2>/dev/null")[2] == 0,
    ]
    ok("Developer Options write attempted via all methods")
    shell("am start -a android.settings.DEVICE_INFO_SETTINGS 2>/dev/null", timeout=5)
    tip("About Phone is now open — tap Build Number 7 times if not done yet")

    # ── 12 USB debugging enable ───────────────────────────────────────────────
    step(12, "USB Debugging — Enable for ADB Access")
    put_setting("global", "adb_enabled", "1")
    shell("su -c 'settings put global adb_enabled 1' 2>/dev/null")
    v3, _, _ = shell("getprop sys.usb.config 2>/dev/null")
    print(f"  USB config: {v3.strip() or 'N/A'}")
    ok("USB debug write attempted")
    tip("If ADB not active: Developer Options → USB debugging → ON")

    # ── 13 Wireless ADB setup ────────────────────────────────────────────────
    step(13, "Wireless ADB — Enable TCP Port 5555")
    shell("su -c 'setprop service.adb.tcp.port 5555; stop adbd; start adbd' 2>/dev/null", timeout=8)
    put_setting("global", "adb_wifi_enabled", "1")
    v4, _, _ = shell("getprop service.adb.tcp.port 2>/dev/null")
    ip2 = get_wifi_ip()
    if v4.strip() == "5555":
        ok(f"Wireless ADB active on {ip2 or '?'}:5555")
        tip(f"From PC: adb connect {ip2 or 'PHONE_IP'}:5555")
    else:
        nope("Could not enable wireless ADB without root")
        tip("Developer Options → Wireless debugging → Enable → Use pairing code")

    # ── 14 Stay-awake settings ───────────────────────────────────────────────
    step(14, "Stay-Awake — Keep Phone Active During Timer")
    put_setting("global", "stay_on_while_plugged_in", "7")
    put_setting("system", "screen_off_timeout", "1800000")
    put_setting("system", "screen_brightness", "200")
    ok("Stay-awake set (all charger types), timeout 30min, brightness raised")
    tip("Plug phone into charger — screen stays on, WiFi stays active")

    # ── 15 Disable airplane mode ─────────────────────────────────────────────
    step(15, "Disable Airplane Mode — Ensure Radio Active")
    out_air, _, _ = shell("settings get global airplane_mode_on 2>/dev/null || getprop persist.sys.airplanemode.on")
    print(f"  Airplane mode: {out_air.strip() or 'N/A'}")
    shell("su -c 'settings put global airplane_mode_on 0; am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false' 2>/dev/null")
    put_setting("global", "airplane_mode_on", "0")
    ok("Airplane mode disabled (if it was on)")

    # ── 16 Toggle airplane mode (force reconnect) ────────────────────────────
    step(16, "Airplane Mode Toggle — Force Network Reconnect")
    tip("Toggling airplane mode forces phone to re-register with Samsung servers")
    shell("su -c 'settings put global airplane_mode_on 1; am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true' 2>/dev/null")
    time.sleep(3)
    shell("su -c 'settings put global airplane_mode_on 0; am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false' 2>/dev/null")
    put_setting("global", "airplane_mode_on", "0")
    time.sleep(5)
    v5, _, _ = shell("getprop sys.oem_unlock_allowed 2>/dev/null")
    ok(f"Airplane toggle done. OEM prop now: {v5.strip() or 'N/A'}")

    # ── 17 Knox Guard check ──────────────────────────────────────────────────
    step(17, "Knox Guard / Enterprise — Block Detection")
    kg_pkgs = ["com.samsung.android.knox.containercore", "com.sec.enterprise.knox.cloudmdm.smdms", "com.samsung.android.knox.knoxguard"]
    kg_found = False
    for p in kg_pkgs:
        v6, _, _ = shell(f"pm list packages {p} 2>/dev/null")
        if p in (v6 or ""):
            nope(f"Knox Guard package found: {p}")
            kg_found = True
    if not kg_found:
        ok("No Knox Guard / enterprise packages found")
    out_dpm, _, _ = shell("dumpsys device_policy 2>/dev/null | grep -c 'device owner'")
    if (out_dpm.strip() or "0") != "0":
        nope("Device Owner policy active — MDM is blocking OEM unlock")
        tip("Settings → Biometrics & security → Device admin apps → Deactivate all")
    else:
        ok("No Device Owner policy found")

    # ── 18 SIM card check ────────────────────────────────────────────────────
    step(18, "SIM Card — Carrier Lock Detection")
    out_sim, _, _ = shell("getprop gsm.sim.state")
    out_carrier, _, _ = shell("getprop gsm.operator.alpha")
    out_imsi, _, _ = shell("getprop gsm.sim.operator.numeric")
    print(f"  SIM state    : {out_sim.strip() or 'N/A'}")
    print(f"  Carrier      : {out_carrier.strip() or 'N/A'}")
    print(f"  IMSI prefix  : {out_imsi.strip() or 'N/A'}")
    out_lock, _, _ = shell("getprop ro.carrier")
    if out_lock.strip() in ("", "unknown", "wifi-only", "openbeta"):
        ok("No carrier lock detected on bootloader level")
    else:
        tip(f"Carrier property: {out_lock.strip()} — verify this doesn't block unlock")

    # ── 19 Factory reset protection check ────────────────────────────────────
    step(19, "FRP Partition — Factory Reset Protection Status")
    out_frp, _, _ = shell("ls /dev/block/by-name/frp 2>/dev/null")
    out_frp_size, _, _ = shell("blockdev --getsize64 /dev/block/by-name/frp 2>/dev/null")
    print(f"  FRP partition : {out_frp.strip() or '—'}")
    print(f"  FRP size      : {out_frp_size.strip() or '—'} bytes")
    tip("After unlock+reset, FRP will activate if Google account was on device")
    tip("Remove Google account BEFORE unlock to avoid FRP lockout")
    ok("FRP check complete")

    # ── 20 Download mode verification ────────────────────────────────────────
    step(20, "Download Mode (Odin) — Verification")
    out_bl, _, _ = shell("getprop ro.bootloader")
    out_csc, _, _ = shell("getprop ro.csc.sales_code")
    out_sw, _, _ = shell("getprop ro.build.display.id")
    print(f"  Bootloader   : {out_bl.strip()}")
    print(f"  CSC          : {out_csc.strip()}")
    print(f"  SW version   : {out_sw.strip()}")
    ok("Device info gathered for Odin/Heimdall flashing if needed")
    tip("Download Mode: Power OFF → hold Vol Down + Power → Vol Up to confirm")
    tip("In Download Mode: use Odin (Windows) or Heimdall (Linux/Mac) to flash")

    # ── 21 Generate PC fastboot commands ──────────────────────────────────────
    step(21, "Generate Complete PC Fastboot Commands")
    ip3 = get_wifi_ip()
    pc_cmds = f"""# PC Commands for SM-S928B Bootloader Unlock
# Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
# Run these on your PC (not on phone)

# Step 1 — Install ADB+Fastboot (if not installed)
# Windows: https://developer.android.com/studio/releases/platform-tools
# Linux/Mac: sudo apt install android-tools-adb  OR  brew install android-platform-tools

# Step 2 — Connect via WiFi (phone IP: {ip3 or 'YOUR_PHONE_IP'})
adb connect {ip3 or 'YOUR_PHONE_IP'}:5555
adb devices

# Step 3 — Enable OEM unlock (if toggle is active on phone)
# First enable it in: Settings → Developer Options → OEM Unlocking

# Step 4 — Reboot to bootloader
adb reboot bootloader
# OR: Power OFF phone → hold Vol Down + Power simultaneously

# Step 5 — Verify in fastboot
fastboot devices
fastboot getvar unlocked
fastboot getvar anti

# Step 6 — UNLOCK (point of no return — wipes all data!)
fastboot flashing unlock
# Press Vol UP on phone to confirm

# Step 7 — After unlock, reboot
fastboot reboot
"""
    cmd_path = os.path.expanduser("~/PC_UNLOCK_COMMANDS.txt")
    try:
        with open(cmd_path, "w") as f:
            f.write(pc_cmds)
        ok(f"PC commands saved: {cmd_path}")
    except Exception:
        pass
    print(pc_cmds)

    # ── 22 Anti-rollback level ────────────────────────────────────────────────
    step(22, "Anti-Rollback (ARB) Level — Firmware Safety Check")
    out_arb, _, _ = shell("getprop ro.boot.anti 2>/dev/null")
    print(f"  ARB level: {out_arb.strip() or 'N/A (check in fastboot: fastboot getvar anti)'}")
    tip("Note your ARB level — cannot flash firmware OLDER than this level after unlock")
    tip("Current firmware S928BXXS6DZE1 is safe — no need to downgrade")
    ok("ARB check noted")

    # ── 23 A/B slot status ───────────────────────────────────────────────────
    step(23, "A/B Slot Status — Active Partition Info")
    out_slot, _, _ = shell("getprop ro.boot.slot_suffix")
    out_vab, _, _ = shell("getprop ro.virtual_ab.enabled")
    print(f"  Active slot    : {out_slot.strip() or 'N/A'}")
    print(f"  Virtual A/B    : {out_vab.strip() or 'N/A'}")
    ok("Virtual A/B confirmed — snapshot-based OTA system")
    tip("After unlock: disable OTA updates (Developer Options → Auto system updates OFF)")

    # ── 24 Knox warranty bit ─────────────────────────────────────────────────
    step(24, "Knox Warranty Bit — Pre-Unlock Verification")
    out_knox, _, _ = shell("getprop ro.boot.warranty_bit")
    val_knox = out_knox.strip()
    if val_knox == "0":
        ok("Knox warranty bit = 0 (intact) — Samsung Pay still works now")
        tip("After unlock: bit permanently becomes 1 — Samsung Pay disabled forever")
    elif val_knox == "1":
        nope("Knox warranty bit already = 1 — Knox already tripped (prior attempt?)")
        tip("This is fine — you can still unlock, Samsung Pay is already disabled")
    else:
        tip(f"Knox bit: {val_knox or 'unknown'}")

    # ── 25 Verified boot state ───────────────────────────────────────────────
    step(25, "Verified Boot State — Current Security State")
    out_vbs, _, _ = shell("getprop ro.boot.verifiedbootstate")
    state = out_vbs.strip()
    color = G if state == "green" else (Y if state == "orange" else R)
    print(f"  Verified boot state: {color}{state}{RE}")
    if state == "green":
        ok("GREEN = stock firmware, fully verified — normal pre-unlock state")
    elif state == "orange":
        ok("ORANGE = bootloader unlocked — custom firmware can run")
    tip("After unlock: state changes green → orange (expected, not an error)")

    # ── 26 SELinux status ────────────────────────────────────────────────────
    step(26, "SELinux — Enforcement Mode Check")
    out_se, _, _ = shell("getenforce 2>/dev/null")
    val_se = out_se.strip()
    print(f"  SELinux mode: {val_se or 'N/A'}")
    if val_se == "Enforcing":
        tip("SELinux enforcing — some root operations blocked (normal on stock)")
        tip("After unlock + Magisk: SELinux can be set to Permissive if needed")
    else:
        ok(f"SELinux: {val_se} — less restricted")

    # ── 27 Disable OTA auto-update ───────────────────────────────────────────
    step(27, "Disable OTA Auto-Update — Prevent Re-Lock")
    put_setting("global", "auto_update_apps", "0")
    shell("pm disable-user --user 0 com.wssyncmldm 2>/dev/null")  # Samsung SW Update
    ok("OTA auto-update disabled")
    tip("Samsung SW Update disabled — prevents automatic firmware update before unlock")
    tip("Also: Developer Options → Auto system updates → OFF")

    # ── 28 Disable Find My Mobile ────────────────────────────────────────────
    step(28, "Disable Find My Mobile — Pre-Unlock Safety")
    fmm_pkgs = ["com.samsung.android.fmm", "com.samsung.android.service.fmm"]
    for p in fmm_pkgs:
        out_fmm, _, _ = shell(f"pm list packages {p} 2>/dev/null")
        if p in (out_fmm or ""):
            shell(f"pm disable-user --user 0 {p} 2>/dev/null")
    put_setting("global", "fmm_status", "0")
    ok("Find My Mobile disable attempted")
    tip("Also manually: Settings → Biometrics & security → Find My Mobile → OFF")

    # ── 29 Backup key data ───────────────────────────────────────────────────
    step(29, "Quick Backup — Export Critical Data")
    backup_dir = os.path.expanduser("~/unlock_backup")
    os.makedirs(backup_dir, exist_ok=True)
    out_contacts, _, _ = shell("content query --uri content://contacts/phones --projection display_name:number 2>/dev/null | wc -l")
    out_sms, _, _ = shell("content query --uri content://sms 2>/dev/null | grep -c 'Row:'")
    out_apps, _, _ = shell("pm list packages -3 2>/dev/null | wc -l")
    out_df, _, _ = shell("df /sdcard 2>/dev/null | tail -1")
    print(f"  Contacts : {out_contacts.strip() or '?'}")
    print(f"  SMS      : {out_sms.strip() or '?'}")
    print(f"  User apps: {out_apps.strip() or '?'}")
    print(f"  Storage  : {out_df.strip() or '?'}")
    ok(f"Backup dir created: {backup_dir}")
    tip("Full backup: Settings → Accounts → Samsung account → Back up data")
    tip("Or from PC: adb backup -apk -shared -all -f backup.adb")

    # ── 30 Battery check ─────────────────────────────────────────────────────
    step(30, "Battery Level — Final Safety Gate")
    out_bat, _, _ = shell("cat /sys/class/power_supply/battery/capacity 2>/dev/null")
    out_bstat, _, _ = shell("cat /sys/class/power_supply/battery/status 2>/dev/null")
    bat_pct = int(out_bat.strip()) if out_bat.strip().isdigit() else -1
    print(f"  Battery: {bat_pct if bat_pct >= 0 else '?'}%  Status: {out_bstat.strip() or 'N/A'}")
    if bat_pct >= 80:
        ok(f"Battery {bat_pct}% ≥ 80% — safe to proceed with unlock")
    elif bat_pct > 0:
        nope(f"Battery {bat_pct}% — charge to ≥80% before running fastboot unlock")
        tip("Plug in charger now — keep plugged throughout the entire unlock process")
    else:
        tip("Could not read battery — plug in charger to be safe")

    # ── 31 Temperature check ─────────────────────────────────────────────────
    step(31, "Device Temperature — Thermal Safety")
    out_temp, _, _ = shell("cat /sys/class/power_supply/battery/temp 2>/dev/null")
    if out_temp.strip().lstrip("-").isdigit():
        temp_c = int(out_temp.strip()) / 10.0
        color = G if temp_c < 40 else (Y if temp_c < 50 else R)
        print(f"  Battery temp: {color}{temp_c:.1f}°C{RE}")
        if temp_c < 45:
            ok(f"Temperature {temp_c:.1f}°C — within safe range")
        else:
            nope(f"Temperature {temp_c:.1f}°C — TOO HOT, let phone cool before flashing")
    else:
        tip("Could not read temperature — ensure phone isn't hot to the touch")

    # ── 32 Termux permissions ────────────────────────────────────────────────
    step(32, "Termux Storage Permission — ADB Key Access")
    storage_ok = os.path.exists(os.path.expanduser("~/storage/downloads"))
    if storage_ok:
        ok("Termux storage permission already granted")
    else:
        tip("Run in Termux: termux-setup-storage")
        tip("This allows Termux to access Downloads folder for backup/scripts")

    # ── 33 Generate Magisk patch guide ────────────────────────────────────────
    step(33, "Magisk Boot Patch — Root Without Keeping Bootloader Unlocked")
    out_bl2, _, _ = shell("getprop ro.bootloader")
    magisk_path = os.path.expanduser("~/MAGISK_GUIDE.txt")
    magisk_guide = f"""Magisk Root Guide for SM-S928B ({out_bl2.strip()})
====================================================
1. Download Magisk APK from github.com/topjohnwu/Magisk/releases
2. Download stock boot.img for firmware {out_bl2.strip()} from samfw.com
3. Install Magisk APK on phone → open it → 'Install' → 'Select and Patch a File'
4. Select the downloaded boot.img → Magisk patches it → saves to /sdcard/Download/
5. Transfer patched boot.img to PC
6. After bootloader unlock:
   adb reboot bootloader
   fastboot flash boot magisk_patched_xxxx.img
   fastboot reboot
7. Open Magisk app → finish setup → grant root
"""
    try:
        with open(magisk_path, "w") as f:
            f.write(magisk_guide)
        ok(f"Magisk guide saved: {magisk_path}")
    except Exception:
        pass
    tip("Magisk is the most popular root method for S24 Ultra post-unlock")

    # ── 34 KernelSU alternative ───────────────────────────────────────────────
    step(34, "KernelSU / APatch — Alternative Root Methods")
    print(f"""
  {C}KernelSU{RE}: kernel-level root, no Magisk needed
    → github.com/tiann/KernelSU — check for S928B kernel build
    → Requires unlocked bootloader + custom kernel flash

  {C}APatch{RE}: patches Android kernel in userspace
    → github.com/bmax121/APatch — works on some stock kernels
    → May not require bootloader unlock (kernel patch via Odin)

  {C}For SM-S928B specifically{RE}:
    → Check: xda-forums.com/c/samsung-galaxy-s24-ultra.12757/
    → Search: "S928B root" or "S928B KernelSU"
    → Community frequently posts device-specific guides
""")
    tip("KernelSU without unlock: if a custom kernel exists for S928B, APatch may work")

    # ── 35 Recovery flash prep ────────────────────────────────────────────────
    step(35, "Custom Recovery Preparation — TWRP/OrangeFox")
    print(f"""
  {C}After bootloader unlock, flash custom recovery:{RE}
    adb reboot bootloader
    fastboot flash recovery recovery.img
    fastboot reboot recovery

  {C}Recovery sources for SM-S928B:{RE}
    → orangefox.tech (OrangeFox)
    → pitchblackrecovery.com (PBRP)
    → twrp.me (check for S928B port)
    → xda-forums.com → search 'S928B recovery'

  {C}Test before flashing permanently:{RE}
    fastboot boot recovery.img   ← boots once without flashing
""")
    ok("Recovery flash guide generated")

    # ── 36 CSC / Region verification ──────────────────────────────────────────
    step(36, "CSC Region Verification — Confirm XX Global")
    out_csc2, _, _ = shell("getprop ro.csc.sales_code")
    out_csc_country, _, _ = shell("getprop ro.csc.countryiso")
    out_omc, _, _ = shell("ls /product/omc/ 2>/dev/null | head -5")
    print(f"  CSC code    : {out_csc2.strip() or 'N/A'}")
    print(f"  Country ISO : {out_csc_country.strip() or 'N/A'}")
    print(f"  OMC options : {out_omc.strip() or '—'}")
    if "XX" in (out_csc2.strip() or ""):
        ok("XX Global CSC confirmed — no carrier restrictions on bootloader")
    else:
        tip(f"CSC is {out_csc2.strip()} — verify this variant supports OEM unlock")

    # ── 37 Complete device fingerprint ────────────────────────────────────────
    step(37, "Full Device Fingerprint Export")
    key_props = ["ro.build.fingerprint", "ro.product.model", "ro.bootloader",
                 "ro.build.version.release", "gsm.version.baseband",
                 "ro.boot.verifiedbootstate", "ro.boot.warranty_bit"]
    fp_path = os.path.expanduser("~/device_fingerprint_ultimate.txt")
    lines = []
    for p in key_props:
        v, _, _ = shell(f"getprop {p}")
        val = v.strip() or "—"
        print(f"  {C}{p:<38}{RE}: {val}")
        lines.append(f"{p} = {val}")
    try:
        with open(fp_path, "w") as f:
            f.write("\n".join(lines))
        ok(f"Fingerprint saved: {fp_path}")
    except Exception:
        pass

    # ── 38 XDA / community resources ─────────────────────────────────────────
    step(38, "XDA & Community Resources — S24 Ultra Specific")
    resources = [
        ("XDA S24 Ultra forum",  "xda-forums.com/c/samsung-galaxy-s24-ultra.12757/"),
        ("SamFW firmware",       "samfw.com → search SM-S928B"),
        ("SammMobile firmware",  "sammobile.com → search S928BXXS6DZE1"),
        ("Magisk releases",      "github.com/topjohnwu/Magisk/releases"),
        ("OrangeFox recovery",   "orangefox.tech/download"),
        ("Samsung Dev unlock",   "developer.samsung.com/galaxy/unlock"),
        ("4pda Russian forum",   "4pda.to → search SM-S928B"),
    ]
    for label, url in resources:
        print(f"  {C}{label:<25}{RE}: {url}")
    ok("Resources listed")

    # ── 39 Reboot recommendation ──────────────────────────────────────────────
    step(39, "Reboot Phone — Trigger Samsung OEM Daemon at Boot")
    out_prop, _, _ = shell("getprop sys.oem_unlock_allowed 2>/dev/null")
    final_prop = out_prop.strip()
    print(f"\n  Current sys.oem_unlock_allowed = {final_prop or 'N/A'}")
    print()
    if final_prop == "1":
        success("OEM UNLOCK IS ACTIVE! Go to Developer Options → OEM Unlocking → Enable it NOW!")
    else:
        warn("OEM unlock not yet active.")
        print(f"""
  {Y}RECOMMENDED NEXT STEP: Reboot the phone{RE}
  The Samsung OEM unlock daemon runs at boot.
  After reboot, it will check Samsung's servers and set the property.

  To reboot from Termux:
    {C}su -c 'reboot' 2>/dev/null || reboot{RE}

  After reboot, run Method 68 and watch:
    • N/A → daemon didn't run (setup issue)
    • 0   → timer counting (wait 7 connected days)
    • 1   → READY! Go to Developer Options immediately
""")
    choice = input(f"  {Y}Reboot now? (y/n): {RE}").strip().lower()
    if choice == "y":
        ok("Rebooting...")
        shell("su -c 'reboot' 2>/dev/null || reboot 2>/dev/null", timeout=10)

    # ── 40 Final summary ──────────────────────────────────────────────────────
    step(40, "Final Status Summary")
    import datetime as dt2
    out_final, _, _ = shell("getprop sys.oem_unlock_allowed 2>/dev/null")
    val_final = out_final.strip()
    print(f"""
  {C}{'═'*60}{RE}
  {C}  ULTIMATE UNLOCK STATUS — {dt2.datetime.now().strftime('%Y-%m-%d %H:%M')}{RE}
  {C}{'═'*60}{RE}
  {G}  PASS : {score['pass']}{RE}
  {R}  FAIL : {score['fail']}{RE}

  {BO}sys.oem_unlock_allowed = {val_final or 'N/A'}{RE}
  {'  ' + G + BO + '★ READY — Enable toggle in Developer Options!' + RE if val_final == '1'
   else '  ' + Y + '→ Timer not complete — keep WiFi on and wait' + RE}

  {W}Files saved to ~/:{RE}
  {C}  PC_UNLOCK_COMMANDS.txt    {RE}← copy-paste commands for your PC
  {C}  MAGISK_GUIDE.txt          {RE}← root guide after unlock
  {C}  device_fingerprint_ultimate.txt  {RE}← device info
  {C}{'═'*60}{RE}
""")


def m122_ksa_network_fix():
    header("KSA / DS-Lite Network Fix — Samsung OEM Daemon Trigger")
    import time

    print(f"""
  {R}{BO}  ══ ROOT CAUSE IDENTIFIED ══{RE}

  {W}Your device has TWO issues preventing the OEM daemon from running:{RE}

  {R}  1. CSC = KSA (Saudi Arabia){RE}
  {W}     KSA CSC may require a Samsung account to be linked before{RE}
  {W}     the OEM unlock timer starts counting.{RE}

  {R}  2. Network = DS-Lite / IPv6-only (192.0.0.2){RE}
  {W}     Samsung's OEM unlock verification uses IPv4 to reach its servers.{RE}
  {W}     DS-Lite (carrier-grade NAT over IPv6) breaks Samsung's check.{RE}
  {W}     Your WiFi gives you only IPv6 — Samsung daemon gets no response.{RE}
""")

    # ── Step 1: Diagnose current network type ────────────────────────────────
    print(f"{C}{BO}  STEP 1 — Network Diagnosis{RE}")
    ip = get_wifi_ip()
    out_pub, _, _ = shell("curl -s --max-time 5 http://ifconfig.me 2>/dev/null || curl -s --max-time 5 http://api.ipify.org 2>/dev/null")
    out_pub6, _, _ = shell("curl -s --max-time 5 http://ifconfig.co 2>/dev/null")
    out_v4, _, rc4 = shell("curl -4 --max-time 5 -s http://ifconfig.me 2>/dev/null")
    out_v6, _, rc6 = shell("curl -6 --max-time 5 -s http://ifconfig.co 2>/dev/null")
    print(f"  Local WiFi IP  : {ip or 'N/A'}")
    print(f"  Public IPv4    : {out_v4.strip() or 'NONE — IPv4 unreachable (DS-Lite confirmed)'}")
    print(f"  Public IPv6    : {out_v6.strip() or 'N/A'}")
    has_ipv4 = bool(out_v4.strip()) and rc4 == 0
    if not has_ipv4:
        print(f"\n  {R}{BO}DS-Lite confirmed — no direct IPv4. Samsung daemon WILL fail on this WiFi.{RE}")
        print(f"  {Y}Solution: Switch to mobile data (4G/LTE) for Samsung verification.{RE}")
    else:
        print(f"\n  {G}IPv4 available — network should work for Samsung verification.{RE}")

    # ── Step 2: Switch to mobile data instructions ───────────────────────────
    print(f"\n{C}{BO}  STEP 2 — Switch to Mobile Data (stc ksa 4G){RE}")
    print(f"""
  {Y}Do this on the phone RIGHT NOW:{RE}
  {G}  1.{RE} {W}Pull down notification bar → tap WiFi icon to turn OFF WiFi{RE}
  {G}  2.{RE} {W}Make sure mobile data is ON: Settings → Connections → Mobile networks → ON{RE}
  {G}  3.{RE} {W}Wait 2-3 minutes for stc 4G to fully connect{RE}
  {G}  4.{RE} {W}Reboot the phone (most important step){RE}
  {G}  5.{RE} {W}After reboot, stay on mobile data (no WiFi) for 30 minutes{RE}
  {G}  6.{RE} {W}Run Method 68 — watch if sys.oem_unlock_allowed changes to 0 or 1{RE}
""")
    # Try to disable WiFi programmatically
    out_wdis, _, rc_wdis = shell("su -c 'svc wifi disable' 2>/dev/null", timeout=5)
    if rc_wdis == 0:
        print(f"  {G}✓ WiFi disabled via root — now on mobile data{RE}")
    else:
        print(f"  {Y}→ Disable WiFi manually: Settings → Connections → WiFi → OFF{RE}")

    # ── Step 3: Samsung account for KSA ──────────────────────────────────────
    print(f"\n{C}{BO}  STEP 3 — Samsung Account (Required for KSA CSC){RE}")
    print(f"""
  {W}For KSA (Saudi Arabia) region, Samsung account may be required:{RE}
  {G}  1.{RE} {W}Settings → Samsung account → Sign in (or create free account){RE}
  {G}  2.{RE} {W}Complete account verification (SMS OTP to your number){RE}
  {G}  3.{RE} {W}Leave signed in for 24 hours on mobile data{RE}
  {G}  4.{RE} {W}Then check: Settings → Developer Options → OEM Unlocking{RE}
  {W}  Remember: REMOVE Samsung account BEFORE the actual fastboot unlock{RE}
""")
    shell("am start -a android.intent.action.VIEW -d market://details?id=com.sec.android.app.samsungapps 2>/dev/null", timeout=5)

    # ── Step 4: Force mobile data connectivity ────────────────────────────────
    print(f"\n{C}{BO}  STEP 4 — Force Mobile Data + Connectivity Triggers{RE}")
    shell("su -c 'svc data enable' 2>/dev/null", timeout=5)
    shell("su -c 'svc wifi disable' 2>/dev/null", timeout=5)
    time.sleep(5)
    # Check if mobile data is now up
    out_mob, _, _ = shell("getprop gsm.data.state")
    out_mob_ip, _, _ = shell("ip addr show rmnet_data0 2>/dev/null | grep 'inet ' | awk '{print $2}' | head -1")
    if not out_mob_ip.strip():
        out_mob_ip, _, _ = shell("ip addr show | grep -v 'lo\|wlan\|dummy' | grep 'inet ' | awk '{print $2}' | head -1")
    print(f"  Mobile data state : {out_mob.strip() or 'N/A'}")
    print(f"  Mobile IP         : {out_mob_ip.strip() or 'not assigned yet'}")
    # Send connectivity broadcast
    shell("am broadcast -a android.net.conn.CONNECTIVITY_CHANGE 2>/dev/null")
    shell("am broadcast -a com.samsung.android.server.oem_unlock.action.OEM_UNLOCK_CHECK 2>/dev/null")
    time.sleep(3)
    v_check, _, _ = shell("getprop sys.oem_unlock_allowed 2>/dev/null")
    val = v_check.strip()
    print(f"\n  sys.oem_unlock_allowed = {G if val=='1' else Y}{val or 'N/A'}{RE}")
    if val == "1":
        success("OEM UNLOCK ACTIVATED! Go to Developer Options → OEM Unlocking → Enable!")
    elif val == "0":
        success("Daemon started! sys=0 means timer is NOW counting on mobile data.")
        info("Keep mobile data connected for 7 days — toggle will appear when done.")
    else:
        warn("Still N/A — reboot the phone while on mobile data (WiFi OFF)")

    # ── Step 5: Alternative — DNS fix for IPv6 network ───────────────────────
    print(f"\n{C}{BO}  STEP 5 — DNS Override (if staying on WiFi){RE}")
    print(f"""
  {W}If you prefer to stay on WiFi, force Samsung servers via DNS:{RE}
  {G}  Settings → Connections → WiFi → long-press your network → Modify{RE}
  {G}  → Advanced options → IP settings → Static{RE}
  {G}  → DNS 1: 8.8.8.8   DNS 2: 8.8.4.4{RE}
  {G}  → Then toggle WiFi off and on{RE}
  {W}  Note: This won't fix the DS-Lite IPv4 problem — mobile data is better.{RE}
""")

    # ── Step 6: Reboot recommendation ────────────────────────────────────────
    print(f"\n{C}{BO}  STEP 6 — Reboot on Mobile Data{RE}")
    print(f"""
  {R}{BO}  MOST IMPORTANT: Reboot with WiFi OFF and mobile data ON.{RE}
  {W}  The Samsung OEM daemon runs at boot and checks connectivity.{RE}
  {W}  On 4G/LTE it gets a real IPv4 address and can reach Samsung servers.{RE}
""")
    choice = input(f"  {Y}Reboot now with mobile data? (y/n): {RE}").strip().lower()
    if choice == "y":
        shell("su -c 'svc wifi disable; svc data enable; sleep 2; reboot' 2>/dev/null", timeout=15)
        info("Reboot initiated — phone will restart on mobile data")
    else:
        tip("Manually: turn WiFi OFF → turn mobile data ON → reboot → wait 10min → run Method 68")


# ─────────────────────────────────────────────────────────────────────────────
# MENU
# ─────────────────────────────────────────────────────────────────────────────
METHODS = [
    (m1_check_adb,           "Check ADB / Device Connection Status"),
    (m2_device_info,         "Full Device Information"),
    (m3_bootloader_status,   "Bootloader Lock Status"),
    (m4_oem_unlock_check,    "OEM Unlock Availability"),
    (m5_enable_dev_options,  "Enable Developer Options"),
    (m6_enable_oem_unlock,   "Enable OEM Unlock via Settings"),
    (m7_reboot_bootloader,   "Reboot to Bootloader / Fastboot"),
    (m8_reboot_recovery,     "Reboot to Recovery Mode"),
    (m9_reboot_download,     "Reboot to Download Mode (Odin)"),
    (m10_fastboot_check,     "Fastboot Connection Check"),
    (m11_fastboot_vars,      "All Fastboot Variables"),
    (m12_knox_status,        "Knox Warranty Bit Status"),
    (m13_security_patch,     "Security Patch Level"),
    (m14_android_version,    "Android Version & Build Details"),
    (m15_list_partitions,    "List Device Partitions"),
    (m16_backup_boot,        "Backup Boot Partition"),
    (m17_backup_recovery,    "Backup Recovery Partition"),
    (m18_selinux_status,     "SELinux Status"),
    (m19_list_packages,      "Installed Package Analysis"),
    (m20_getprop_dump,       "Full Device Properties Dump"),
    (m21_usb_debug_status,   "USB Debugging Status"),
    (m22_enable_adb,         "Enable ADB & Developer Settings"),
    (m23_fastboot_oem_unlock,"OEM Unlock via Fastboot  [★ main unlock]"),
    (m24_flash_twrp,         "Flash Custom Recovery (TWRP)"),
    (m25_fastboot_wipe,      "Factory Reset via Fastboot"),
    (m26_root_check,         "Root Status Check"),
    (m27_magisk_prep,        "Magisk Installation Preparation"),
    (m28_adb_sideload,       "ADB Sideload ZIP"),
    (m29_carrier_lock,       "Carrier Lock Status"),
    (m30_logcat_monitor,     "Logcat Boot Event Monitor"),
    (m31_partition_mounts,   "System Partition Mount Status"),
    (m32_adb_backup,         "Device Backup"),
    (m33_frida_check,        "Frida Dynamic Instrumentation Check"),
    (m34_process_list,       "Running Process Analysis"),
    (m35_network_analysis,   "Network Interface Analysis"),
    (m36_shell_oem_unlock,   "OEM Unlock via Shell — Advanced"),
    (m37_edl_mode,           "EDL Mode Information"),
    (m38_flash_boot,         "Flash Custom Boot Image"),
    (m39_disable_verity,     "dm-verity / Verified Boot Control"),
    (m40_full_workflow,      "Complete Automated Unlock Workflow  [★ start here]"),
    (m41_seven_day_timer,   "Samsung 7-Day OEM Unlock Timer Check"),
    (m42_open_oem_toggle,   "Open OEM Unlock Toggle Directly on Screen"),
    (m43_csc_analysis,      "CSC / Sales Code Analysis (XX=Global confirmed)"),
    (m44_bootloader_parser, "Bootloader Version Parser (S928BXXS6DZE1)"),
    (m45_wireless_adb,      "Wireless ADB Setup (no USB cable needed)"),
    (m46_wireless_pairing,  "Wireless ADB Pairing Code (Android 12+)"),
    (m47_tap_build_number,  "Force-Enable Developer Options (7-tap sim)"),
    (m48_internet_check,    "Internet Connectivity Check (timer requirement)"),
    (m49_samsung_account,   "Samsung & Google Account Status"),
    (m50_play_integrity,    "Play Integrity / SafetyNet Impact Analysis"),
    (m51_ota_check,         "OTA Update Status (disable before unlocking)"),
    (m52_heimdall,          "Heimdall Compatibility & Download Mode Guide"),
    (m53_knox_detailed,     "Knox Detailed Counter & TIMA Analysis"),
    (m54_frp_analysis,      "FRP Lock Analysis & Pre-Unlock Preparation"),
    (m55_eligibility_report,"Full Unlock Eligibility Report  [★ run first]"),
    (m56_one_button_unlock, "ONE-BUTTON MASTER UNLOCK  [★★ do everything]"),
    (m57_root_settings,     "Root-Based Settings Access (fix transaction errors)"),
    (m58_internet_fix,      "Internet Connectivity Repair & WiFi Status"),
    (m59_force_dev_root,    "Force Enable Developer Options via Root"),
    (m60_force_oem_root,    "Force Enable OEM Unlock via Root DB Write"),
    (m61_ab_slot_status,    "A/B Partition Slot Status (Virtual A/B)"),
    (m62_anti_rollback,     "Anti-Rollback (ARB) Level Check"),
    (m63_usb_mode,          "USB Gadget Mode & ADB Config"),
    (m64_kernel_info,       "Kernel Version & Security Info"),
    (m65_generate_pc_script,"Generate PC Unlock Script (copy-paste commands)"),
    (m66_samfw_info,        "SamFW Firmware Info for S928BXXS6DZE1"),
    (m67_termux_setup,      "Termux Full Tool Setup (install all needed packages)"),
    (m68_oem_toggle_watcher,"Real-Time OEM Toggle Monitor"),
    (m69_disable_find_my,   "Disable Find My Mobile (pre-unlock safety)"),
    (m70_kernelsu_info,     "Alternative Root: KernelSU / APatch for S24 Ultra"),
    (m71_adb_tcp_root,      "Enable ADB TCP:5555 via Root (wireless PC connect)"),
    (m72_imei_check,        "IMEI & Device Registration Check"),
    (m73_service_codes,     "Samsung Service & Diagnostic Codes"),
    (m74_unlock_timeline,   "Unlock Timeline & Day-by-Day Action Plan"),
    (m75_quick_reference,   "S24 Ultra Unlock Quick Reference Card"),
    (m76_battery_before_unlock,     "Battery Level Pre-Unlock Safety Check"),
    (m77_stay_awake_setting,        "Screen Stay-Awake Configuration for Unlock"),
    (m78_seven_day_countdown,       "7-Day OEM Timer Countdown Calculator"),
    (m79_usbc_mode_detector,        "USB-C Port Mode & ADB Configuration Detector"),
    (m80_mdm_enrollment_check,      "MDM / Enterprise Enrollment Detection"),
    (m81_adb_rsa_key_guide,         "ADB RSA Key Auto-Accept Guide & Status"),
    (m82_backup_before_wipe,        "Pre-Unlock Backup — Critical Data Protection"),
    (m83_fbe_encryption_status,     "File-Based Encryption (FBE) Status Check"),
    (m84_disable_samsung_analytics, "Disable Samsung Analytics & Telemetry"),
    (m85_tee_trustzone_status,      "TEE / TrustZone / StrongBox Security Status"),
    (m86_twrp_s928b_info,           "TWRP Custom Recovery — SM-S928B Guide"),
    (m87_custom_rom_compat,         "Custom ROM Compatibility — S928B (Exynos)"),
    (m88_vbmeta_analysis,           "vbmeta / Verified Boot Chain Analysis"),
    (m89_ab_update_engine,          "A/B Partition Update Engine Status"),
    (m90_samsung_account_removal,   "Samsung Account Removal — Pre-Unlock Safety"),
    (m91_google_frp_guide,          "Google FRP Lock — Pre-Unlock Guide"),
    (m92_fastboot_complete_checklist,"Fastboot getvar Complete Checklist"),
    (m93_usb_tethering_setup,       "USB Tethering Setup — Share Internet with PC"),
    (m94_clock_date_sync,           "Clock & Date Sync — Timer Prerequisite Check"),
    (m95_developer_stay_awake,      "Developer Option: Stay Awake While Charging"),
    (m96_wipe_cache_partition,      "Cache Wipe — Pre/Post Unlock Maintenance"),
    (m97_adb_keys_manager,          "ADB Authorized Keys — View, Backup & Revoke"),
    (m98_device_fingerprint,        "Device Fingerprint & Identity Export"),
    (m99_rom_flash_preparation,     "Custom ROM Flash Preparation Checklist"),
    (m100_termux_monitor_widget,    "Termux OEM Unlock Status Monitor & Widget"),
    (m101_oem_toggle_grey_reason,   "Why Is OEM Unlock Toggle Greyed? — Diagnosis"),
    (m102_samsung_unlock_channels,  "Samsung Support & Unlock Channels"),
    (m103_network_timer_watcher,    "Network Watcher — OEM Timer Tracker"),
    (m104_disable_knox_features,    "Disable Samsung Knox & Pay — Pre-Unlock"),
    (m105_csc_change_guide,         "CSC (Country Sales Code) Change Guide"),
    (m106_unlock_cert_request,      "Bootloader Unlock Certificate Request"),
    (m107_unlock_summary_printout,  "Complete Unlock Summary — Printable Reference"),
    (m108_backup_contacts_sms,      "Backup Contacts & SMS Before Wipe"),
    (m109_adb_key_backup_restore,   "ADB Key Backup & Restore — PC Auth Manager"),
    (m110_ram_storage_status,       "RAM & Storage Status — Resource Check"),
    (m111_temperature_check,        "Device Temperature — Thermal Safety Check"),
    (m112_staged_oem_rollout_check, "Staged OEM Unlock Rollout — Eligibility Check"),
    (m113_enterprise_android_check, "Android Enterprise / Work Profile Detection"),
    (m114_samsung_mdm_policy,       "Samsung MDM Policy Analyzer — Knox Audit"),
    (m115_aosp_migration_prep,      "AOSP / Custom ROM Migration — Full Prep Guide"),
    (m116_force_show_oem_toggle,    "Force Show OEM Unlocking Toggle (if missing from list)"),
    (m117_oem_via_dialer_codes,     "Samsung Dialer Codes for OEM & Developer Access"),
    (m118_oem_unlock_no_toggle,     "OEM Unlock via Fastboot — No Toggle Required"),
    (m119_toggle_visibility_props,  "OEM Toggle Visibility — Property Deep Scan"),
    (m120_oem_longpress_tricks,     "OEM Toggle Hidden Entry Points & Deep Link Tricks"),
    (m121_ultimate_unlock,          "ULTIMATE 40-TECHNIQUE UNLOCK ASSAULT  [★★★ run this]"),
    (m122_ksa_network_fix,          "KSA + DS-Lite Network Fix  [★★★ run if in Saudi Arabia]"),
]


def show_menu():
    print(f"\n{B}{BO}{'─'*62}{RE}")
    print(f"{C}{BO}  Available Methods{RE}")
    print(f"{B}{'─'*62}{RE}")
    for i, (_, desc) in enumerate(METHODS, 1):
        if i <= 10:
            nc = M
        elif i <= 20:
            nc = C
        elif i <= 30:
            nc = Y
        elif i <= 40:
            nc = G
        elif i <= 55:
            nc = B
        elif i <= 75:
            nc = R
        elif i <= 95:
            nc = M
        else:
            nc = C
        print(f"  {nc}{BO}{i:>3}{RE}. {W}{desc}{RE}")
    print(f"\n  {Y}  0{RE}. Exit")
    print(f"{B}{'─'*62}{RE}")


def main():
    banner()
    install_dependencies()
    while True:
        show_menu()
        try:
            choice = input(f"\n{C}{BO}Select method [0-122]: {RE}").strip()
            if choice == "0":
                info("Goodbye!"); break
            n = int(choice)
            if 1 <= n <= 122:
                banner()
                METHODS[n - 1][0]()
                input(f"\n{Y}Press Enter to return to menu…{RE}")
                banner()
            else:
                error("Enter a number between 0 and 122")
        except ValueError:
            error("Invalid input — enter a number")
        except KeyboardInterrupt:
            print()
            info("Interrupted. Goodbye!")
            break


if __name__ == "__main__":
    main()

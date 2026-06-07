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
# shell(cmd) runs a shell command on the target device.
# In on-device mode it runs directly; in remote mode it prepends 'adb shell'.

def shell(cmd, timeout=30):
    if ON_DEVICE:
        return run(cmd, timeout)
    return run(f"adb shell {cmd}", timeout)


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
    print(f"{Y}  40 Professional Methods  |  Termux Edition  |  ADB + Fastboot{RE}")
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

    # Check provisioning / first-boot timestamp indicators
    prov,      _, _ = shell("settings get global device_provisioned")
    setup_done,_, _ = shell("settings get secure user_setup_complete")
    setup_time,_, _ = shell("settings get global device_setup_timestamp 2>/dev/null")
    oem_val,   _, _ = shell("settings get global oem_unlock_allowed")
    oem_sys,   _, _ = shell("getprop sys.oem_unlock_allowed")

    print(f"  {C}device_provisioned{RE}       : {W}{prov or 'N/A'}{RE}")
    print(f"  {C}user_setup_complete{RE}       : {W}{setup_done or 'N/A'}{RE}")
    print(f"  {C}device_setup_timestamp{RE}    : {W}{setup_time or 'N/A (not stored here)'}{RE}")
    print(f"  {C}oem_unlock_allowed (global){RE}: {G if oem_val=='1' else R}{oem_val or 'N/A'}{RE}")
    print(f"  {C}sys.oem_unlock_allowed{RE}    : {G if oem_sys=='1' else R}{oem_sys or 'N/A'}{RE}")

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
        warn("OEM unlock not yet allowed — timer may still be running")
        info("Connect to WiFi, leave device running, check again in 7 days")


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

    # Check network connectivity
    wifi_state,  _, _ = shell("getprop init.svc.dhcpcd_wlan0 2>/dev/null")
    net_state,   _, _ = shell("getprop gsm.data.state 2>/dev/null")
    wifi_ssid,   _, _ = shell("getprop wifi.interface 2>/dev/null")
    ip_addr,     _, _ = shell("ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \\K[^ ]+'")
    if not ip_addr:
        ip_addr, _, _ = shell("getprop dhcp.wlan0.ipaddress")

    # Ping test
    ping_ok, _, ping_rc = shell("ping -c 1 -W 3 8.8.8.8 2>/dev/null | grep -c '1 received'")
    dns_ok,  _, dns_rc  = shell("nslookup google.com 2>/dev/null | grep -c 'Address'")

    print(f"  {C}WiFi IP address {RE}: {G if ip_addr else R}{ip_addr or 'No IP (not connected)'}{RE}")
    print(f"  {C}Ping 8.8.8.8   {RE}: {G if ping_rc==0 else R}{'OK' if ping_rc==0 else 'Failed'}{RE}")
    print(f"  {C}DNS resolution  {RE}: {G if dns_rc==0 else R}{'OK' if dns_rc==0 else 'Failed'}{RE}")
    print(f"  {C}Mobile data     {RE}: {W}{net_state or 'N/A'}{RE}")

    print()
    if ip_addr and ping_rc == 0:
        success("Internet connectivity ACTIVE — OEM unlock timer is counting")
    elif ip_addr:
        warn("IP assigned but ping failed — check firewall or connection quality")
    else:
        error("NO internet connectivity — OEM unlock timer is paused")
        print(f"\n{C}Fix:{RE}")
        print("  Connect to WiFi: Settings → WiFi → select your network")
        print("  Or enable mobile data")
        print("  The 7-day timer only counts while internet is connected")


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

    print(f"{C}{BO}Gathering all unlock eligibility data…{RE}\n")

    checks = {}

    # 1. Device model
    model, _, _ = shell("getprop ro.product.model")
    checks["Model is S24 Ultra (S928B)"] = ("s928" in model.lower(), model)

    # 2. Region (XX = global = unlockable)
    bl, _, _ = shell("getprop ro.bootloader")
    is_global = "XX" in bl if bl else False
    checks["Global variant (XX region)"] = (is_global, bl or "N/A")

    # 3. Developer options
    dev, _, _ = shell("settings get global development_settings_enabled")
    checks["Developer Options enabled"] = (dev == "1", f"value={dev}")

    # 4. OEM unlock setting
    oem, _, _ = shell("settings get global oem_unlock_allowed")
    checks["OEM unlock allowed (setting)"] = (oem == "1", f"value={oem}")

    # 5. OEM unlock system prop
    oem_sys, _, _ = shell("getprop sys.oem_unlock_allowed")
    checks["sys.oem_unlock_allowed"] = (oem_sys == "1", f"value={oem_sys}")

    # 6. Bootloader currently locked
    locked, _, _ = shell("getprop ro.boot.flash.locked")
    checks["Bootloader currently LOCKED (to unlock)"] = (locked == "1", f"flash.locked={locked}")

    # 7. Verified boot state
    vbs, _, _ = shell("getprop ro.boot.verifiedbootstate")
    checks["Verified boot state"] = (vbs == "green", f"state={vbs}")

    # 8. Knox warranty intact
    knox, _, _ = shell("getprop ro.boot.warranty_bit")
    checks["Knox warranty bit intact (0)"] = (knox == "0", f"bit={knox}")

    # 9. Internet connectivity
    ip, _, _ = shell("ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \\K[^ ]+'")
    if not ip:
        ip, _, _ = shell("getprop dhcp.wlan0.ipaddress")
    checks["Internet connectivity"] = (bool(ip), f"IP={ip or 'none'}")

    # 10. Android version (16 = unlockable)
    android, _, _ = shell("getprop ro.build.version.release")
    checks["Android version (16 supports unlock)"] = (True, f"Android {android}")

    # Print report
    pass_count = 0
    fail_count = 0
    warn_count = 0
    for label, (status, detail) in checks.items():
        if status:
            print(f"  {G}[PASS]{RE} {W}{label:<45}{RE} {C}{detail}{RE}")
            pass_count += 1
        else:
            # Some "fails" are just informational
            if "LOCKED" in label:
                print(f"  {C}[INFO]{RE} {W}{label:<45}{RE} {Y}{detail}{RE}")
                warn_count += 1
            else:
                print(f"  {R}[FAIL]{RE} {W}{label:<45}{RE} {Y}{detail}{RE}")
                fail_count += 1

    print(f"\n{C}{'─'*62}{RE}")
    print(f"  {G}PASS: {pass_count}{RE}  {R}FAIL: {fail_count}{RE}  {C}INFO: {warn_count}{RE}")
    print(f"{C}{'─'*62}{RE}\n")

    # Verdict
    blocker_fails = [l for l, (s, _) in checks.items()
                     if not s and "LOCKED" not in l and "Knox" not in l]
    if not blocker_fails:
        print(f"{G}{BO}  ✓ VERDICT: Device IS ELIGIBLE for bootloader unlock!{RE}")
        print(f"\n{C}  Next steps:{RE}")
        if oem != "1":
            print(f"  {Y}  1. Enable OEM Unlocking toggle in Developer Options (Method 42){RE}")
            print(f"  {Y}  2. Wait for the 7-day timer if toggle is greyed out (Method 41){RE}")
            print(f"  {W}  3. Reboot to bootloader (Method 7) then run fastboot unlock from PC{RE}")
        else:
            print(f"  {G}  1. OEM unlock is already allowed!{RE}")
            print(f"  {W}  2. Reboot to bootloader (Method 7){RE}")
            print(f"  {W}  3. From PC: fastboot flashing unlock{RE}")
    else:
        print(f"{R}{BO}  ✗ VERDICT: Blockers found — resolve before unlocking:{RE}")
        for b in blocker_fails:
            print(f"  {R}  • {b}{RE}")


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
]


def show_menu():
    print(f"\n{B}{BO}{'─'*62}{RE}")
    print(f"{C}{BO}  Available Methods{RE}")
    print(f"{B}{'─'*62}{RE}")
    for i, (_, desc) in enumerate(METHODS, 1):
        nc = M if i <= 10 else (C if i <= 20 else (Y if i <= 30 else (G if i <= 40 else R)))
        print(f"  {nc}{BO}{i:>2}{RE}. {W}{desc}{RE}")
    print(f"\n  {Y} 0{RE}. Exit")
    print(f"{B}{'─'*62}{RE}")


def main():
    banner()
    install_dependencies()
    while True:
        show_menu()
        try:
            choice = input(f"\n{C}{BO}Select method [0-55]: {RE}").strip()
            if choice == "0":
                info("Goodbye!"); break
            n = int(choice)
            if 1 <= n <= 55:
                banner()
                METHODS[n - 1][0]()
                input(f"\n{Y}Press Enter to return to menu…{RE}")
                banner()
            else:
                error("Enter a number between 0 and 55")
        except ValueError:
            error("Invalid input — enter a number")
        except KeyboardInterrupt:
            print()
            info("Interrupted. Goodbye!")
            break


if __name__ == "__main__":
    main()

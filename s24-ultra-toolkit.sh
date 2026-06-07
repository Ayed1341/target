#!/data/data/com.termux/files/usr/bin/bash
# ============================================================================
#  Galaxy S24 Ultra - Termux Android Toolkit  (legitimate, on-device tool)
#
#  For a phone YOU own. Everything here genuinely works - no fake/placeholder.
#    * Read-only device info via getprop / dumpsys (no root needed)
#    * Debloat, backups, logs, screenshots, reboots via ADB wireless debugging
#    * Bootloader section = STATUS CHECK + Samsung's OFFICIAL unlock steps only
#
#  HONEST NOTE: No script can "force unlock" a bootloader or make a hidden
#  OEM-unlock toggle appear - that is a security boundary enforced by the
#  bootloader itself. This tool only READS the unlock state and GUIDES you
#  through the official process. US/Snapdragon S24 Ultra models cannot be
#  unlocked by any method.
#
#  USAGE (in Termux):
#    pkg update && pkg install android-tools
#    bash s24-ultra-toolkit.sh
# ============================================================================

set -u

# ----------------------------- colors / ui ---------------------------------
if [ -t 1 ]; then
  R=$'\033[0;31m'; G=$'\033[0;32m'; Y=$'\033[1;33m'; B=$'\033[0;36m'; W=$'\033[1;37m'; N=$'\033[0m'
else
  R=''; G=''; Y=''; B=''; W=''; N=''
fi

TOOLDIR="$HOME/s24-toolkit"
mkdir -p "$TOOLDIR" 2>/dev/null

pause(){ printf "\n%sPress Enter to continue...%s" "$Y" "$N"; read -r _; }
hr(){ printf "%s--------------------------------------------------------------%s\n" "$B" "$N"; }
title(){ clear 2>/dev/null; hr; printf "%s  %s%s\n" "$W" "$1" "$N"; hr; }
ok(){ printf "%s%s%s\n" "$G" "$1" "$N"; }
warn(){ printf "%s%s%s\n" "$Y" "$1" "$N"; }
err(){ printf "%s%s%s\n" "$R" "$1" "$N"; }

# read a system property safely (works in Termux without root)
gp(){ getprop "$1" 2>/dev/null; }

have_adb(){ command -v adb >/dev/null 2>&1; }
adb_ready(){ have_adb && [ "$(adb get-state 2>/dev/null)" = "device" ]; }

require_adb(){
  if ! have_adb; then err "ADB is not installed - use option 21 first."; return 1; fi
  if ! adb_ready; then err "No ADB device connected - use options 22-23 (wireless debugging) first."; return 1; fi
  return 0
}

# --------------------------- 1-10  device info -----------------------------
f1(){ title "1) Device Identity"
  printf " Manufacturer  : %s\n" "$(gp ro.product.manufacturer)"
  printf " Brand         : %s\n" "$(gp ro.product.brand)"
  printf " Model         : %s\n" "$(gp ro.product.model)"
  printf " Market name   : %s\n" "$(gp ro.product.vendor.marketname)"
  printf " Codename      : %s\n" "$(gp ro.product.device)"
  printf " Android ver   : %s\n" "$(gp ro.build.version.release)"
  printf " SDK / API     : %s\n" "$(gp ro.build.version.sdk)"
  printf " One UI build  : %s\n" "$(gp ro.build.display.id)"
  printf " Security patch: %s\n" "$(gp ro.build.version.security_patch)"
  pause; }

f2(){ title "2) Hardware / SoC"
  printf " SoC model     : %s\n" "$(gp ro.soc.model)"
  printf " SoC maker     : %s\n" "$(gp ro.soc.manufacturer)"
  printf " Board         : %s\n" "$(gp ro.product.board)"
  printf " ABI           : %s\n" "$(gp ro.product.cpu.abi)"
  printf " Hardware      : %s\n" "$(gp ro.hardware)"
  printf "\n CPU cores:\n"
  grep -c "^processor" /proc/cpuinfo 2>/dev/null | sed 's/^/   logical CPUs: /'
  pause; }

f3(){ title "3) Memory (RAM)"
  if [ -r /proc/meminfo ]; then
    awk '/MemTotal|MemFree|MemAvailable|SwapTotal|SwapFree/{printf "   %-14s %8.0f MB\n",$1,$2/1024}' /proc/meminfo
  else err "Cannot read /proc/meminfo"; fi
  pause; }

f4(){ title "4) Storage"
  df -h 2>/dev/null | awk 'NR==1 || /\/storage|\/data|\/sdcard|^\/dev/{print "   "$0}'
  pause; }

f5(){ title "5) Battery"
  if adb_ready; then adb shell dumpsys battery 2>/dev/null
  elif command -v termux-battery-status >/dev/null 2>&1; then termux-battery-status
  else warn "Connect ADB (opt 22-23) or install Termux:API for battery details."; fi
  pause; }

f6(){ title "6) Display"
  if require_adb; then
    printf " Resolution : "; adb shell wm size 2>/dev/null | sed 's/Physical size: //'
    printf " Density    : "; adb shell wm density 2>/dev/null | sed 's/Physical density: //'
  fi
  pause; }

f7(){ title "7) Kernel"
  uname -a 2>/dev/null
  printf "\n Kernel ver : %s\n" "$(gp ro.kernel.version)"
  pause; }

f8(){ title "8) Firmware / Build"
  printf " Build ID       : %s\n" "$(gp ro.build.id)"
  printf " Build number   : %s\n" "$(gp ro.build.version.incremental)"
  printf " Bootloader     : %s\n" "$(gp ro.bootloader)"
  printf " Baseband/Modem : %s\n" "$(gp gsm.version.baseband)"
  printf " Build type     : %s\n" "$(gp ro.build.type)"
  printf " Build tags     : %s\n" "$(gp ro.build.tags)"
  pause; }

f9(){ title "9) Network / IP"
  if command -v ip >/dev/null 2>&1; then ip -br addr 2>/dev/null | sed 's/^/   /'
  elif command -v ifconfig >/dev/null 2>&1; then ifconfig 2>/dev/null
  else err "No ip/ifconfig available."; fi
  pause; }

f10(){ title "10) Uptime / Load"
  uptime 2>/dev/null || cat /proc/uptime 2>/dev/null
  pause; }

# ----------------------- 11-16  bootloader / dev ---------------------------
f11(){ title "11) Bootloader / OEM-Unlock STATUS (read-only)"
  printf " sys.oem_unlock_allowed    : %s   (1 = OEM-unlock toggle available)\n" "$(gp sys.oem_unlock_allowed)"
  printf " ro.oem_unlock_supported   : %s\n" "$(gp ro.oem_unlock_supported)"
  printf " ro.boot.flash.locked      : %s   (0 = unlocked, 1 = locked)\n" "$(gp ro.boot.flash.locked)"
  printf " ro.boot.verifiedbootstate : %s   (green=locked, orange=unlocked)\n" "$(gp ro.boot.verifiedbootstate)"
  printf " ro.boot.warranty_bit      : %s   (1 = Knox tripped)\n" "$(gp ro.boot.warranty_bit)"
  printf "\n"
  m="$(gp ro.product.model)"
  case "$m" in
    *U|*U1|*W) warn " Model $m looks like a US/Snapdragon variant - Samsung permanently"
               warn " disables bootloader unlocking on these. It cannot be unlocked." ;;
    "") warn " Model unknown (run inside Termux on the device)." ;;
    *) ok " Model $m may support unlocking IF the OEM-unlock toggle is available." ;;
  esac
  pause; }

f12(){ title "12) Official Bootloader Unlock - Steps"
  cat <<'EOF'
 A script CANNOT unlock a bootloader - it is done in Download mode by the
 bootloader itself. These are the ONLY official steps (they ERASE the phone):

 1. Back up everything. Unlocking factory-resets the device.
 2. Settings > About phone > Software information
       Tap "Build number" 7 times to enable Developer options.
 3. Settings > Developer options
       Turn ON "OEM unlocking" and "USB debugging".
       If "OEM unlocking" is greyed out: stay online and wait up to 7 days,
       then check again. If it never appears, your model does not support
       unlocking and nothing can change that.
 4. Power off. Enter Download mode (Volume Up + Volume Down while connecting
    USB to a PC).
 5. Long-press Volume Up to confirm the unlock prompt. The phone resets and
    reboots with the bootloader unlocked.

 US / Snapdragon S24 Ultra (SM-S928U / U1 / W): bootloader is permanently
 locked by Samsung. No app, script, or trick can unlock it - only
 international Exynos-region units can.
EOF
  pause; }

f13(){ title "13) How to Enable Developer Options"
  cat <<'EOF'
 1. Settings > About phone > Software information.
 2. Tap "Build number" 7 times (enter your PIN if asked).
 3. "Developer options" now appears under Settings (or Settings > System).
 4. Useful toggles there: USB debugging, Wireless debugging, OEM unlocking,
    "Stay awake", animation scales (set to .5x for a snappier feel).
EOF
  pause; }

f14(){ title "14) Knox / Warranty Status"
  printf " ro.boot.warranty_bit : %s\n" "$(gp ro.boot.warranty_bit)"
  printf " ro.warranty_bit      : %s\n" "$(gp ro.warranty_bit)"
  printf " Knox is tripped permanently (1) once the bootloader is unlocked.\n"
  pause; }

f15(){ title "15) Root Status Check"
  if command -v su >/dev/null 2>&1; then warn " 'su' binary found - device may be rooted."
  else ok " No 'su' in PATH - device looks non-rooted (normal)."; fi
  printf " Build tags : %s  (release-keys = stock, test-keys = modified)\n" "$(gp ro.build.tags)"
  pause; }

f16(){ title "16) SELinux Status"
  if command -v getenforce >/dev/null 2>&1; then getenforce 2>/dev/null | sed 's/^/   /'
  else printf "   verifiedbootstate: %s\n" "$(gp ro.boot.verifiedbootstate)"; fi
  pause; }

# --------------------------- 17-25  adb / reboot ---------------------------
f17(){ require_adb || { pause; return; }; warn "Rebooting normally..."; adb reboot 2>/dev/null; pause; }
f18(){ require_adb || { pause; return; }; warn "Rebooting to recovery..."; adb reboot recovery 2>/dev/null; pause; }
f19(){ require_adb || { pause; return; }; warn "Rebooting to Download mode..."; adb reboot download 2>/dev/null || adb reboot bootloader 2>/dev/null; pause; }
f20(){ require_adb || { pause; return; }
  read -r -p "Really power OFF the device? [y/N] " a; [ "$a" = "y" ] || { pause; return; }
  adb shell reboot -p 2>/dev/null; pause; }

f21(){ title "21) Install ADB (android-tools)"
  warn "Installing android-tools (adb + fastboot)..."
  if pkg install -y android-tools; then ok "Done. adb is ready."
  else err "Install failed. Run:  pkg update && pkg install android-tools"; fi
  pause; }

f22(){ title "22) Pair Wireless Debugging"
  cat <<'EOF'
 On the phone:
   Settings > Developer options > Wireless debugging > Pair device with code.
 It shows an IP address:PORT and a 6-digit pairing code.
EOF
  read -r -p " Enter pair IP:PORT : " ip
  read -r -p " Enter pairing code : " code
  [ -n "$ip" ] && [ -n "$code" ] && adb pair "$ip" "$code"
  pause; }

f23(){ title "23) Connect Wireless Debugging"
  echo " Settings > Developer options > Wireless debugging shows IP:PORT"
  echo " (the connect port is usually different from the pairing port)."
  read -r -p " Enter IP:PORT : " ip
  [ -n "$ip" ] && adb connect "$ip"
  pause; }

f24(){ title "24) ADB Devices / State"
  if have_adb; then adb devices -l 2>/dev/null; else err "ADB not installed (option 21)."; fi
  pause; }

f25(){ title "25) Disconnect ADB"
  if have_adb; then adb disconnect 2>/dev/null; ok "Disconnected."; else err "ADB not installed."; fi
  pause; }

# --------------------------- 26-34  packages -------------------------------
f26(){ require_adb || { pause; return; }; title "26) All Installed Packages"
  adb shell pm list packages 2>/dev/null | sed 's/package://' | sort | ${PAGER:-less}
  pause; }
f27(){ require_adb || { pause; return; }; title "27) System Packages"
  adb shell pm list packages -s 2>/dev/null | sed 's/package://' | sort | ${PAGER:-less}
  pause; }
f28(){ require_adb || { pause; return; }; title "28) Disabled Packages"
  adb shell pm list packages -d 2>/dev/null | sed 's/package://' | sort | ${PAGER:-less}
  pause; }
f29(){ require_adb || { pause; return; }; title "29) Search a Package"
  read -r -p " Keyword: " kw; [ -z "$kw" ] && return
  adb shell pm list packages 2>/dev/null | sed 's/package://' | grep -i "$kw" | sort
  pause; }
f30(){ require_adb || { pause; return; }; title "30) Remove a Package (current user)"
  read -r -p " Package name: " pkg; [ -z "$pkg" ] && return
  if adb shell pm uninstall --user 0 "$pkg" 2>/dev/null | grep -q Success; then
    ok "Removed for this user (reversible with option 31)."
  else err "Could not remove (wrong name or protected)."; fi
  pause; }
f31(){ require_adb || { pause; return; }; title "31) Restore a Removed Package"
  read -r -p " Package name: " pkg; [ -z "$pkg" ] && return
  adb shell cmd package install-existing "$pkg" 2>/dev/null && ok "Restored." || err "Failed."
  pause; }
f32(){ require_adb || { pause; return; }; title "32) Disable a Package"
  read -r -p " Package name: " pkg; [ -z "$pkg" ] && return
  adb shell pm disable-user --user 0 "$pkg" 2>/dev/null && ok "Disabled." || err "Failed."
  pause; }
f33(){ require_adb || { pause; return; }; title "33) Enable a Package"
  read -r -p " Package name: " pkg; [ -z "$pkg" ] && return
  adb shell pm enable "$pkg" 2>/dev/null && ok "Enabled." || err "Failed."
  pause; }
f34(){ require_adb || { pause; return; }; title "34) Remove Common Bloat (reversible)"
  echo " Removes these for the current user only (restore with option 31):"
  apps="com.facebook.katana com.facebook.appmanager com.facebook.services com.facebook.system \
com.samsung.android.app.spage com.samsung.android.bixby.agent com.samsung.android.bixby.wakeup \
com.samsung.android.app.tips com.samsung.android.game.gamehome com.microsoft.skydrive \
com.microsoft.office.officehubrow com.linkedin.android com.netflix.partner.activation \
com.samsung.android.scloud com.samsung.android.kidsinstaller com.google.android.apps.tachyon"
  printf "   %s\n" $apps
  read -r -p " Proceed? [y/N] " a; [ "$a" = "y" ] || { pause; return; }
  for p in $apps; do
    adb shell pm uninstall --user 0 "$p" 2>/dev/null | grep -q Success && ok "removed $p"
  done
  pause; }

# --------------------------- 35-40  utilities ------------------------------
f35(){ require_adb || { pause; return; }; title "35) Backup Installed-App List"
  f="$TOOLDIR/apps_$(date +%Y%m%d_%H%M%S).txt"
  adb shell pm list packages 2>/dev/null | sed 's/package://' | sort > "$f"
  ok "Saved $f  ($(wc -l < "$f") apps)"
  pause; }
f36(){ require_adb || { pause; return; }; title "36) Screenshot"
  f="$TOOLDIR/shot_$(date +%Y%m%d_%H%M%S).png"
  adb exec-out screencap -p > "$f" 2>/dev/null && ok "Saved $f" || err "Failed."
  pause; }
f37(){ require_adb || { pause; return; }; title "37) Record Screen (15s)"
  warn "Recording 15 seconds..."
  adb shell screenrecord --time-limit 15 /sdcard/s24rec.mp4 2>/dev/null
  f="$TOOLDIR/rec_$(date +%Y%m%d_%H%M%S).mp4"
  adb pull /sdcard/s24rec.mp4 "$f" >/dev/null 2>&1 && { adb shell rm /sdcard/s24rec.mp4 2>/dev/null; ok "Saved $f"; } || err "Failed."
  pause; }
f38(){ require_adb || { pause; return; }; title "38) Capture Logcat (10s)"
  f="$TOOLDIR/logcat_$(date +%Y%m%d_%H%M%S).txt"
  warn "Capturing..."; timeout 10 adb logcat -d > "$f" 2>/dev/null
  ok "Saved $f"
  pause; }
f39(){ require_adb || { pause; return; }; title "39) Top Processes (CPU/RAM)"
  adb shell top -b -n 1 2>/dev/null | head -n 25
  pause; }
f40(){ require_adb || { pause; return; }; title "40) Battery Usage by App"
  adb shell dumpsys batterystats --charged 2>/dev/null | grep -iE "Estimated power|Uid .* :" | head -n 25
  pause; }

# -------------------------------- menu -------------------------------------
menu(){
  clear 2>/dev/null
  hr
  printf "%s        GALAXY S24 ULTRA - TERMUX TOOLKIT%s\n" "$W" "$N"
  hr
  printf " Device: %s%s%s   adb: %s\n" "$G" "$(gp ro.product.model)" "$N" \
    "$( adb_ready && echo connected || echo 'not connected' )"
  hr
  printf "  INFO        1 Identity   2 Hardware  3 RAM       4 Storage\n"
  printf "              5 Battery    6 Display   7 Kernel    8 Firmware\n"
  printf "              9 Network   10 Uptime\n"
  printf "  BOOTLOADER 11 Unlock status   12 Official unlock guide\n"
  printf "             13 Enable Dev Opts 14 Knox status 15 Root 16 SELinux\n"
  printf "  ADB        17 Reboot 18 Recovery 19 Download 20 Power off\n"
  printf "             21 Install adb 22 Pair 23 Connect 24 Devices 25 Disconnect\n"
  printf "  APPS       26 List all 27 System 28 Disabled 29 Search\n"
  printf "             30 Remove 31 Restore 32 Disable 33 Enable 34 Debloat\n"
  printf "  TOOLS      35 Backup list 36 Screenshot 37 Record 38 Logcat\n"
  printf "             39 Top procs 40 Battery usage\n"
  printf "              0 Exit\n"
  hr
  printf " Choose [0-40]: "
}

while true; do
  menu
  read -r choice
  case "$choice" in
    1) f1;; 2) f2;; 3) f3;; 4) f4;; 5) f5;; 6) f6;; 7) f7;; 8) f8;; 9) f9;; 10) f10;;
    11) f11;; 12) f12;; 13) f13;; 14) f14;; 15) f15;; 16) f16;; 17) f17;; 18) f18;; 19) f19;; 20) f20;;
    21) f21;; 22) f22;; 23) f23;; 24) f24;; 25) f25;; 26) f26;; 27) f27;; 28) f28;; 29) f29;; 30) f30;;
    31) f31;; 32) f32;; 33) f33;; 34) f34;; 35) f35;; 36) f36;; 37) f37;; 38) f38;; 39) f39;; 40) f40;;
    0|q|Q) clear 2>/dev/null; ok "Bye!"; exit 0;;
    *) err "Invalid choice."; sleep 1;;
  esac
done

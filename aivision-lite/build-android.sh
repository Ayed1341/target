#!/usr/bin/env bash
#
# AI Vision Lite — fully automated Android APK build for Ubuntu Linux.
#
# This script reproduces the entire build from a clean checkout:
#   1. Installs the Android SDK command-line tools + required packages.
#   2. Installs Node dependencies.
#   3. Builds the web app (Vite) and syncs it into the Capacitor Android project.
#   4. Produces a signed Debug APK and a signed, R8-shrunk Release APK.
#
# Requirements that must already be on the machine:
#   - JDK 17+ (JDK 21 recommended)         ->  sudo apt-get install -y openjdk-21-jdk
#   - Node.js 20+ (Node 22 recommended)    ->  https://nodejs.org
#   - curl, unzip
#
# Network requirements (these MUST be reachable — they are blocked in the
# Claude Code sandbox, which is why the APK cannot be produced there):
#   - https://dl.google.com         (Android SDK packages + Android Gradle Plugin)
#   - https://maven.google.com      (AndroidX / Material libraries)
#   - https://services.gradle.org   (Gradle distribution)
#   - https://repo1.maven.org       (Maven Central)
#   - https://registry.npmjs.org    (npm packages)
#
# Usage:
#   chmod +x build-android.sh
#   ./build-android.sh
#
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# --------------------------------------------------------------------------
# 1. Android SDK
# --------------------------------------------------------------------------
export ANDROID_HOME="${ANDROID_HOME:-$HOME/Android/Sdk}"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
CMDLINE_TOOLS_VERSION="11076708"   # commandlinetools-linux build number

if [ ! -x "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" ]; then
  echo ">> Installing Android SDK command-line tools into $ANDROID_HOME"
  mkdir -p "$ANDROID_HOME/cmdline-tools"
  TMP_ZIP="$(mktemp --suffix=.zip)"
  curl -L -o "$TMP_ZIP" \
    "https://dl.google.com/android/repository/commandlinetools-linux-${CMDLINE_TOOLS_VERSION}_latest.zip"
  rm -rf "$ANDROID_HOME/cmdline-tools/tmp"
  unzip -q "$TMP_ZIP" -d "$ANDROID_HOME/cmdline-tools/tmp"
  rm -rf "$ANDROID_HOME/cmdline-tools/latest"
  mv "$ANDROID_HOME/cmdline-tools/tmp/cmdline-tools" "$ANDROID_HOME/cmdline-tools/latest"
  rm -rf "$ANDROID_HOME/cmdline-tools/tmp" "$TMP_ZIP"
fi

export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH"

echo ">> Accepting SDK licenses and installing required packages"
yes | sdkmanager --licenses >/dev/null
sdkmanager \
  "platform-tools" \
  "platforms;android-36" \
  "build-tools;36.0.0"

# Point Gradle at the SDK (android/.gitignore excludes this file from VCS).
echo "sdk.dir=$ANDROID_HOME" > "$PROJECT_DIR/android/local.properties"

# --------------------------------------------------------------------------
# 2. Node dependencies + web build + Capacitor sync
# --------------------------------------------------------------------------
echo ">> Installing Node dependencies"
npm ci || npm install

echo ">> Building web app (Vite) -> dist/"
npm run build:web 2>/dev/null || npx vite build

echo ">> Syncing web assets into the Android project"
npx cap sync android

# --------------------------------------------------------------------------
# 3. Gradle builds
# --------------------------------------------------------------------------
cd "$PROJECT_DIR/android"
chmod +x ./gradlew

echo ">> Building Debug APK"
./gradlew assembleDebug --no-daemon

echo ">> Building Release APK (R8 shrink + resource shrink, signed)"
./gradlew assembleRelease --no-daemon

# --------------------------------------------------------------------------
# 4. Report output locations
# --------------------------------------------------------------------------
DEBUG_APK="$PROJECT_DIR/android/app/build/outputs/apk/debug/app-debug.apk"
RELEASE_APK="$PROJECT_DIR/android/app/build/outputs/apk/release/app-release.apk"

echo ""
echo "============================================================"
echo " BUILD COMPLETE"
echo "============================================================"
[ -f "$DEBUG_APK" ]   && echo " Debug APK   : $DEBUG_APK   ($(du -h "$DEBUG_APK"   | cut -f1))"
[ -f "$RELEASE_APK" ] && echo " Release APK : $RELEASE_APK ($(du -h "$RELEASE_APK" | cut -f1))"
echo "============================================================"

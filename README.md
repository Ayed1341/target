# AYED VISION AI LITE

**Author: Ayed Oraybi**

A production-ready, real-time on-device computer-vision Android app. It opens the
camera on launch and runs live analysis — object detection, scene labeling, face &
pose & hand tracking, OCR, and barcode/QR scanning — entirely on the device. No
images leave the phone.

Built for **Samsung Galaxy S24 Ultra** and modern Android (Android 8.0 / API 26 → 16).

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Language | Kotlin |
| UI | Jetpack Compose + Material 3 |
| Architecture | MVVM + Clean Architecture |
| DI | Hilt |
| Async | Coroutines + Flow |
| Persistence | Room |
| Camera | CameraX (Preview + ImageAnalysis) |
| Vision | ML Kit (objects, image labeling, face, pose, text, barcode) + MediaPipe Tasks (hands + gestures) |

All models are **real, pretrained, production** models. ML Kit models are bundled /
served by Google Play services. The MediaPipe gesture model (`gesture_recognizer.task`)
is fetched once from Google's official model storage on first use of **Hands** mode,
then runs fully offline.

---

## Feature set (25)

Real-time object detection · multi-object tracking · object classification ·
bounding-box overlay · confidence scores · in-frame object counting · scene
labeling · face detection · facial landmark/contour detection · hand tracking ·
basic gesture recognition · full-body pose skeleton · text recognition (OCR) ·
QR scanning · barcode scanning · animal detection* · food recognition* · product
recognition* · vehicle detection* · capture & instant analysis · live video-stream
analysis · local detection history (Room) · JSON export/share · dark-mode UI ·
Arabic + English.

> \* Animal / food / product / vehicle "detection" are real category filters applied
> on top of the on-device object detector and image labeler — using only what the
> pretrained models actually output. No fabricated breed/age/weight/height estimates.

---

## Project structure

```
app/src/main/java/com/ayed/visionai/lite/
├── analysis/      # CameraX analyzer + one FrameAnalyzer per mode (ML Kit / MediaPipe)
├── data/          # Room entities, DAO, database, repository impl
├── di/            # Hilt modules
├── domain/        # Models + repository interface
├── ui/            # Compose screens, components, theme, ViewModels
├── util/          # Category mapping + JSON serialization
├── MainActivity.kt
└── VisionApp.kt
```

---

## Build & run

### Option A — Android Studio (recommended)
1. Install **Android Studio Koala (2024.1)** or newer.
2. `File ▸ Open` → select this project folder.
3. Let Gradle sync (downloads dependencies + Gradle 8.9 via the wrapper).
4. Connect an Android 8+ device (or start an emulator) and press **Run** ▶.

### Option B — Command line (debug APK)
```bash
./gradlew :app:assembleDebug
# Output: app/build/outputs/apk/debug/app-debug.apk
```

### Option C — Release APK
```bash
./gradlew :app:assembleRelease
# Output: app/build/outputs/apk/release/app-release.apk
```
Without a keystore, the release build is signed with the debug key so it always
builds. To sign with **your own** key, copy `keystore.properties.template` to
`keystore.properties`, fill in your keystore details, then run the command above.

### Option D — Download a prebuilt APK (CI)
Every push runs `.github/workflows/android.yml`, which builds **debug + release**
APKs and uploads them as downloadable workflow artifacts:
`Actions ▸ latest run ▸ Artifacts ▸ ayed-vision-ai-lite-release`.

---

## Permissions

- `CAMERA` — required for live analysis (requested at runtime).
- `INTERNET` / `ACCESS_NETWORK_STATE` — one-time MediaPipe model download + ML Kit
  model provisioning. The app works offline after the first launch.

---

## Notes on scope & honesty

- Coordinates from every analyzer are unified into one upright image space and
  mapped to the preview with the same center-crop transform CameraX uses, with
  front-camera mirroring — so overlays stay aligned.
- Only capabilities the pretrained models genuinely provide are surfaced. Where a
  requested feature isn't feasible with a real model, the closest real ML capability
  is used (e.g. category filtering over generic detection).

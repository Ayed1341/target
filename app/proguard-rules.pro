# Keep ML Kit and MediaPipe model/runtime classes
-keep class com.google.mlkit.** { *; }
-keep class com.google.android.gms.** { *; }
-keep class com.google.mediapipe.** { *; }
-keep class com.google.protobuf.** { *; }
-dontwarn com.google.mediapipe.**
-dontwarn com.google.protobuf.**

# Keep Room generated classes
-keep class androidx.room.** { *; }

# Keep model classes used for JSON export (reflection-free, but defensive)
-keep class com.ayed.visionai.lite.domain.model.** { *; }

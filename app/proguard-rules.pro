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

# AutoValue / javapoet (pulled in transitively by ML Kit & MediaPipe) reference
# annotation-processing classes that are absent at runtime. They are compile-time
# only, so silence R8's missing-class errors for them.
-dontwarn javax.lang.model.**
-dontwarn javax.annotation.**
-dontwarn autovalue.shaded.**
-dontwarn com.google.auto.value.**

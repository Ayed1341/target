# Proguard rules for Router Manager - عايد عريبي
-keep public class * extends com.getcapacitor.Plugin
-keepclassmembers class * extends com.getcapacitor.Plugin {
    @com.getcapacitor.annotation.CapacitorPlugin *;
    @com.getcapacitor.annotation.Permission *;
}
-keepattributes *Annotation*

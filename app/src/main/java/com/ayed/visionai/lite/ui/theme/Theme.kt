package com.ayed.visionai.lite.ui.theme

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val DarkColors = darkColorScheme(
    primary = NeonCyan,
    onPrimary = DeepSpace,
    secondary = ElectricBlue,
    onSecondary = OnDark,
    tertiary = AccentMagenta,
    background = DeepSpace,
    onBackground = OnDark,
    surface = PanelDark,
    onSurface = OnDark,
    surfaceVariant = SurfaceDark,
    onSurfaceVariant = OnDark,
    primaryContainer = SurfaceDark,
    onPrimaryContainer = NeonCyan
)

private val LightColors = lightColorScheme(
    primary = LightPrimary,
    onPrimary = LightSurface,
    secondary = ElectricBlue,
    background = LightBackground,
    onBackground = OnLight,
    surface = LightSurface,
    onSurface = OnLight
)

/**
 * Material 3 theme. Honors the system dark-mode setting (feature 24) and keeps a
 * consistent futuristic neon identity in both schemes. Dynamic color is disabled
 * intentionally so branding stays stable across devices.
 */
@Composable
fun AyedVisionTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColors else LightColors
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
        }
    }
    MaterialTheme(
        colorScheme = colorScheme,
        typography = AyedTypography,
        content = content
    )
}

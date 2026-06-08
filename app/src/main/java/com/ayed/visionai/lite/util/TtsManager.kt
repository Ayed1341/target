package com.ayed.visionai.lite.util

import android.content.Context
import android.speech.tts.TextToSpeech
import dagger.hilt.android.qualifiers.ApplicationContext
import java.util.Locale
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Thin wrapper around Android's on-device Text-to-Speech engine. Reads detection
 * results aloud in Arabic or English. No network required.
 */
@Singleton
class TtsManager @Inject constructor(
    @ApplicationContext context: Context
) {
    @Volatile private var ready = false
    private val tts: TextToSpeech = TextToSpeech(context.applicationContext) { status ->
        ready = status == TextToSpeech.SUCCESS
    }

    fun speak(text: String, arabic: Boolean) {
        if (!ready || text.isBlank()) return
        val locale = if (arabic) Locale("ar") else Locale.ENGLISH
        if (tts.isLanguageAvailable(locale) >= TextToSpeech.LANG_AVAILABLE) {
            tts.language = locale
        }
        tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "ayed-vision-tts")
    }

    fun stop() {
        if (ready) tts.stop()
    }
}

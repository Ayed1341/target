package com.ayed.visionai.lite.analysis

import com.google.mlkit.common.model.DownloadConditions
import com.google.mlkit.nl.languageid.LanguageIdentification
import com.google.mlkit.nl.translate.TranslateLanguage
import com.google.mlkit.nl.translate.Translation
import com.google.mlkit.nl.translate.TranslatorOptions
import kotlinx.coroutines.tasks.await
import javax.inject.Inject
import javax.inject.Singleton

/**
 * On-device natural-language helper (ML Kit). Identifies the language of OCR text
 * and translates between Arabic and English. Translation models are downloaded
 * once (Wi-Fi) and then run fully offline.
 */
@Singleton
class LanguageProcessor @Inject constructor() {

    private val identifier = LanguageIdentification.getClient()

    /** Returns a BCP-47 language code, or null if undetermined. */
    suspend fun identify(text: String): String? {
        if (text.isBlank()) return null
        val code = identifier.identifyLanguage(text).await()
        return code.takeIf { it != "und" }
    }

    /**
     * Translates Arabic→English or English→Arabic (auto-picked from the source
     * text). Returns null if the language is neither or translation is unavailable.
     */
    suspend fun translateArabicEnglish(text: String): String? {
        if (text.isBlank()) return null
        val source = identify(text) ?: return null
        val (src, tgt) = when (source) {
            "ar" -> TranslateLanguage.ARABIC to TranslateLanguage.ENGLISH
            "en" -> TranslateLanguage.ENGLISH to TranslateLanguage.ARABIC
            else -> return null
        }
        val translator = Translation.getClient(
            TranslatorOptions.Builder()
                .setSourceLanguage(src)
                .setTargetLanguage(tgt)
                .build()
        )
        return try {
            translator.downloadModelIfNeeded(DownloadConditions.Builder().build()).await()
            translator.translate(text).await()
        } catch (e: Exception) {
            null
        } finally {
            translator.close()
        }
    }
}

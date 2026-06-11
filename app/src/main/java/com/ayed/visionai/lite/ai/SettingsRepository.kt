package com.ayed.visionai.lite.ai

import android.content.Context
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Persists the AI assistant configuration in local SharedPreferences. The API key
 * stays on the device and is only ever sent to the provider the user selected.
 */
@Singleton
class SettingsRepository @Inject constructor(
    @ApplicationContext context: Context
) {
    private val prefs = context.getSharedPreferences("ayed_ai_settings", Context.MODE_PRIVATE)

    private val _settings = MutableStateFlow(load())
    val settings: StateFlow<AiSettings> = _settings.asStateFlow()

    private fun load(): AiSettings = AiSettings(
        provider = AiProvider.fromName(prefs.getString(KEY_PROVIDER, null)),
        apiKey = prefs.getString(KEY_API_KEY, "").orEmpty(),
        model = prefs.getString(KEY_MODEL, AiSettings.DEFAULT_GEMINI_MODEL)
            .orEmpty().ifBlank { AiSettings.DEFAULT_GEMINI_MODEL },
        baseUrl = prefs.getString(KEY_BASE_URL, AiSettings.DEFAULT_OPENAI_BASE_URL)
            .orEmpty().ifBlank { AiSettings.DEFAULT_OPENAI_BASE_URL }
    )

    fun current(): AiSettings = _settings.value

    fun save(settings: AiSettings) {
        prefs.edit()
            .putString(KEY_PROVIDER, settings.provider.name)
            .putString(KEY_API_KEY, settings.apiKey.trim())
            .putString(KEY_MODEL, settings.model.trim())
            .putString(KEY_BASE_URL, settings.baseUrl.trim())
            .apply()
        _settings.value = settings
    }

    private companion object {
        const val KEY_PROVIDER = "provider"
        const val KEY_API_KEY = "api_key"
        const val KEY_MODEL = "model"
        const val KEY_BASE_URL = "base_url"
    }
}

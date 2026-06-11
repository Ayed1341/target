package com.ayed.visionai.lite.ai

/** Supported cloud multimodal providers for the optional AI assistant. */
enum class AiProvider {
    /** Google Gemini — has a genuinely free tier (recommended). */
    GEMINI,

    /** Any OpenAI-compatible chat/completions endpoint (OpenAI, Groq, OpenRouter, local). */
    OPENAI;

    companion object {
        fun fromName(name: String?): AiProvider =
            entries.firstOrNull { it.name == name } ?: GEMINI
    }
}

/** User-configured settings for the AI assistant, stored locally on device. */
data class AiSettings(
    val provider: AiProvider = AiProvider.GEMINI,
    val apiKey: String = "",
    val model: String = DEFAULT_GEMINI_MODEL,
    val baseUrl: String = DEFAULT_OPENAI_BASE_URL
) {
    val isConfigured: Boolean get() = apiKey.isNotBlank()

    fun defaultModelForProvider(): String = when (provider) {
        AiProvider.GEMINI -> DEFAULT_GEMINI_MODEL
        AiProvider.OPENAI -> DEFAULT_OPENAI_MODEL
    }

    companion object {
        const val DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"
        const val DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
        const val DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
    }
}

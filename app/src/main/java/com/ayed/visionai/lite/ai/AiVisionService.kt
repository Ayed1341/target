package com.ayed.visionai.lite.ai

import android.graphics.Bitmap
import android.util.Base64
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.min

/**
 * Sends a captured camera frame plus a prompt to a cloud multimodal model and
 * returns the text answer. Supports Google Gemini (free tier) and any
 * OpenAI-compatible vision endpoint. Pure REST via OkHttp + org.json — no SDK.
 */
@Singleton
class AiVisionService @Inject constructor() {

    private val client = OkHttpClient.Builder()
        .connectTimeout(20, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .build()

    private val jsonMediaType = "application/json; charset=utf-8".toMediaType()

    /** Returns the model's answer, or throws [AiException] with a readable message. */
    suspend fun describe(
        bitmap: Bitmap,
        prompt: String,
        settings: AiSettings
    ): String = withContext(Dispatchers.IO) {
        if (!settings.isConfigured) throw AiException("No API key set")
        val base64 = encodeJpeg(bitmap)
        when (settings.provider) {
            AiProvider.GEMINI -> callGemini(base64, prompt, settings)
            AiProvider.OPENAI -> callOpenAi(base64, prompt, settings)
        }
    }

    private fun callGemini(base64: String, prompt: String, settings: AiSettings): String {
        val model = settings.model.ifBlank { AiSettings.DEFAULT_GEMINI_MODEL }
        val url = "https://generativelanguage.googleapis.com/v1beta/models/" +
            "$model:generateContent?key=${settings.apiKey}"

        val body = JSONObject().apply {
            put("contents", JSONArray().put(JSONObject().apply {
                put("parts", JSONArray()
                    .put(JSONObject().put("text", prompt))
                    .put(JSONObject().put("inline_data", JSONObject().apply {
                        put("mime_type", "image/jpeg")
                        put("data", base64)
                    }))
                )
            }))
        }

        val request = Request.Builder()
            .url(url)
            .post(body.toString().toRequestBody(jsonMediaType))
            .build()

        val raw = execute(request)
        val candidates = raw.optJSONArray("candidates")
            ?: throw AiException(extractError(raw) ?: "Empty response")
        if (candidates.length() == 0) throw AiException("No answer returned")
        val parts = candidates.getJSONObject(0)
            .optJSONObject("content")?.optJSONArray("parts")
            ?: throw AiException("Malformed response")
        val sb = StringBuilder()
        for (i in 0 until parts.length()) {
            parts.getJSONObject(i).optString("text").let { if (it.isNotBlank()) sb.append(it) }
        }
        return sb.toString().ifBlank { throw AiException("No text in response") }
    }

    private fun callOpenAi(base64: String, prompt: String, settings: AiSettings): String {
        val base = settings.baseUrl.trim().ifBlank { AiSettings.DEFAULT_OPENAI_BASE_URL }
            .trimEnd('/')
        val model = settings.model.ifBlank { AiSettings.DEFAULT_OPENAI_MODEL }

        val content = JSONArray()
            .put(JSONObject().put("type", "text").put("text", prompt))
            .put(JSONObject().apply {
                put("type", "image_url")
                put("image_url", JSONObject().put("url", "data:image/jpeg;base64,$base64"))
            })
        val body = JSONObject().apply {
            put("model", model)
            put("messages", JSONArray().put(JSONObject().apply {
                put("role", "user")
                put("content", content)
            }))
            put("max_tokens", 700)
        }

        val request = Request.Builder()
            .url("$base/chat/completions")
            .header("Authorization", "Bearer ${settings.apiKey}")
            .post(body.toString().toRequestBody(jsonMediaType))
            .build()

        val raw = execute(request)
        val choices = raw.optJSONArray("choices")
            ?: throw AiException(extractError(raw) ?: "Empty response")
        if (choices.length() == 0) throw AiException("No answer returned")
        return choices.getJSONObject(0)
            .optJSONObject("message")?.optString("content")
            ?.ifBlank { null }
            ?: throw AiException("No text in response")
    }

    private fun execute(request: Request): JSONObject {
        try {
            client.newCall(request).execute().use { response ->
                val text = response.body?.string().orEmpty()
                val json = if (text.isNotBlank()) runCatching { JSONObject(text) }.getOrNull() else null
                if (!response.isSuccessful) {
                    throw AiException(json?.let { extractError(it) } ?: "HTTP ${response.code}")
                }
                return json ?: throw AiException("Invalid response")
            }
        } catch (e: AiException) {
            throw e
        } catch (e: Exception) {
            throw AiException(e.message ?: "Network error")
        }
    }

    private fun extractError(json: JSONObject): String? =
        json.optJSONObject("error")?.optString("message")?.ifBlank { null }

    private fun encodeJpeg(bitmap: Bitmap): String {
        val maxSide = 1024
        val scale = min(1f, maxSide.toFloat() / maxOf(bitmap.width, bitmap.height))
        val scaled = if (scale < 1f) {
            Bitmap.createScaledBitmap(
                bitmap,
                (bitmap.width * scale).toInt().coerceAtLeast(1),
                (bitmap.height * scale).toInt().coerceAtLeast(1),
                true
            )
        } else bitmap
        val out = ByteArrayOutputStream()
        scaled.compress(Bitmap.CompressFormat.JPEG, 85, out)
        return Base64.encodeToString(out.toByteArray(), Base64.NO_WRAP)
    }
}

class AiException(message: String) : Exception(message)

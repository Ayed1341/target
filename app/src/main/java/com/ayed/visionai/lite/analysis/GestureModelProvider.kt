package com.ayed.visionai.lite.analysis

import android.content.Context
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.nio.ByteBuffer
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Supplies the MediaPipe gesture-recognizer model. The official Google-hosted
 * `.task` bundle is fetched once to internal storage on first use; afterwards it
 * loads fully offline. If the device is offline on first run, [loadModelBuffer]
 * returns null and the Hands mode reports that gracefully — no crash, no fake.
 */
@Singleton
class GestureModelProvider @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val modelFile: File
        get() = File(File(context.filesDir, "models").apply { mkdirs() }, MODEL_NAME)

    /** Returns a direct ByteBuffer with the model bytes, or null if unavailable. */
    suspend fun loadModelBuffer(): ByteBuffer? = withContext(Dispatchers.IO) {
        val file = ensureModel() ?: return@withContext null
        val bytes = file.readBytes()
        ByteBuffer.allocateDirect(bytes.size).apply {
            put(bytes)
            rewind()
        }
    }

    private fun ensureModel(): File? {
        val file = modelFile
        if (file.exists() && file.length() > 0) return file
        return try {
            val connection = (URL(MODEL_URL).openConnection() as HttpURLConnection).apply {
                connectTimeout = 15_000
                readTimeout = 30_000
                requestMethod = "GET"
            }
            connection.inputStream.use { input ->
                val tmp = File(file.parentFile, "$MODEL_NAME.tmp")
                tmp.outputStream().use { output -> input.copyTo(output) }
                if (tmp.length() > 0) {
                    tmp.renameTo(file)
                    file
                } else {
                    tmp.delete()
                    null
                }
            }
        } catch (e: Exception) {
            null
        }
    }

    private companion object {
        const val MODEL_NAME = "gesture_recognizer.task"
        const val MODEL_URL =
            "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/" +
                "gesture_recognizer/float16/1/gesture_recognizer.task"
    }
}

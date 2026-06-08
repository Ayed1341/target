package com.ayed.visionai.lite.analysis

import com.ayed.visionai.lite.domain.model.DetectedBox
import com.ayed.visionai.lite.domain.model.DetectionMode
import com.ayed.visionai.lite.domain.model.ObjectCategory
import com.ayed.visionai.lite.domain.model.VisionResult
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import kotlinx.coroutines.tasks.await

/** On-device OCR / text recognition (ML Kit). Feature 13. */
class TextAnalyzer : FrameAnalyzer {

    override val mode = DetectionMode.TEXT

    private val recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)

    override suspend fun analyze(frame: AnalysisFrame): VisionResult {
        val text = recognizer.process(frame.inputImage).await()
        val boxes = text.textBlocks.mapNotNull { block ->
            val rect = block.boundingBox ?: return@mapNotNull null
            DetectedBox(
                left = rect.left.toFloat(),
                top = rect.top.toFloat(),
                right = rect.right.toFloat(),
                bottom = rect.bottom.toFloat(),
                label = block.text.replace('\n', ' ').take(24),
                confidence = 1f,
                category = ObjectCategory.GENERIC
            )
        }
        return VisionResult(
            mode = mode,
            sourceWidth = frame.uprightWidth,
            sourceHeight = frame.uprightHeight,
            isFrontCamera = frame.isFrontCamera,
            boxes = boxes,
            recognizedText = text.text.takeIf { it.isNotBlank() }
        )
    }

    override fun close() = recognizer.close()
}

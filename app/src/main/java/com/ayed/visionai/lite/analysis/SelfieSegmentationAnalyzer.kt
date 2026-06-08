package com.ayed.visionai.lite.analysis

import android.graphics.Bitmap
import android.graphics.Color
import com.ayed.visionai.lite.domain.model.DetectionMode
import com.ayed.visionai.lite.domain.model.SegmentationOverlay
import com.ayed.visionai.lite.domain.model.VisionResult
import com.google.mlkit.vision.segmentation.Segmentation
import com.google.mlkit.vision.segmentation.selfie.SelfieSegmenterOptions
import kotlinx.coroutines.tasks.await
import kotlin.math.roundToInt

/**
 * Real-time selfie segmentation (ML Kit): produces a per-pixel person/background
 * mask that is rendered as a translucent overlay. Advanced feature.
 */
class SelfieSegmentationAnalyzer : FrameAnalyzer {

    override val mode = DetectionMode.SEGMENTATION

    private val segmenter = Segmentation.getClient(
        SelfieSegmenterOptions.Builder()
            .setDetectorMode(SelfieSegmenterOptions.STREAM_MODE)
            .build()
    )

    private val tint = Color.argb(140, 0, 229, 255)

    override suspend fun analyze(frame: AnalysisFrame): VisionResult {
        val mask = segmenter.process(frame.inputImage).await()
        val width = mask.width
        val height = mask.height
        val buffer = mask.buffer
        buffer.rewind()

        val pixels = IntArray(width * height)
        var foreground = 0
        for (i in pixels.indices) {
            val confidence = buffer.float
            if (confidence > 0.5f) {
                pixels[i] = tint
                foreground++
            } else {
                pixels[i] = Color.TRANSPARENT
            }
        }
        val bitmap = Bitmap.createBitmap(pixels, width, height, Bitmap.Config.ARGB_8888)
        val coverage = if (pixels.isNotEmpty()) {
            (foreground * 100f / pixels.size).roundToInt()
        } else 0

        return VisionResult(
            mode = mode,
            sourceWidth = frame.uprightWidth,
            sourceHeight = frame.uprightHeight,
            isFrontCamera = frame.isFrontCamera,
            segmentation = SegmentationOverlay(bitmap, coverage)
        )
    }

    override fun close() = segmenter.close()
}

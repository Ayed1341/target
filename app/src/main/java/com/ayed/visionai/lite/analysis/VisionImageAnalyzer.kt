package com.ayed.visionai.lite.analysis

import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import com.ayed.visionai.lite.domain.model.DetectionMode
import com.ayed.visionai.lite.domain.model.VisionResult
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch
import java.util.concurrent.atomic.AtomicLong

/**
 * The single [ImageAnalysis.Analyzer] wired to CameraX. For each frame it routes
 * to the analyzer matching the currently selected [mode], emits a [VisionResult],
 * and measures throughput (FPS). Backpressure is handled by CameraX's
 * KEEP_ONLY_LATEST strategy: the next frame is delivered only after the current
 * [ImageProxy] is closed, so we close it once analysis completes.
 */
class VisionImageAnalyzer(
    private val scope: CoroutineScope,
    private val registry: AnalyzerRegistry,
    private val onResult: (VisionResult) -> Unit,
    private val onFps: (Int) -> Unit
) : ImageAnalysis.Analyzer {

    @Volatile var mode: DetectionMode = DetectionMode.default
    @Volatile var isFrontCamera: Boolean = false

    private val lastTimestamp = AtomicLong(0L)

    override fun analyze(imageProxy: ImageProxy) {
        val frame = AnalysisFrame.from(imageProxy, isFrontCamera)
        if (frame == null) {
            imageProxy.close()
            return
        }
        scope.launch {
            try {
                val activeMode = mode
                val result = registry.analyzerFor(activeMode).analyze(frame)
                onResult(result)
                reportFps()
            } catch (e: Exception) {
                onResult(
                    VisionResult.empty(mode).copy(statusMessage = e.message)
                )
            } finally {
                imageProxy.close()
            }
        }
    }

    private fun reportFps() {
        val now = System.currentTimeMillis()
        val prev = lastTimestamp.getAndSet(now)
        if (prev > 0L) {
            val delta = now - prev
            if (delta > 0) onFps((1000 / delta).toInt().coerceIn(0, 60))
        }
    }
}

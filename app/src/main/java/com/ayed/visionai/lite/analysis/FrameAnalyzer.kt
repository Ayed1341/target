package com.ayed.visionai.lite.analysis

import com.ayed.visionai.lite.domain.model.DetectionMode
import com.ayed.visionai.lite.domain.model.VisionResult

/** A single-responsibility on-device analyzer bound to one [DetectionMode]. */
interface FrameAnalyzer {
    val mode: DetectionMode
    suspend fun analyze(frame: AnalysisFrame): VisionResult
    fun close()
}

package com.ayed.visionai.lite.analysis

import com.ayed.visionai.lite.domain.model.DetectionMode
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Owns one [FrameAnalyzer] per [DetectionMode]. The hand/gesture analyzer is
 * Hilt-injected (it needs context + model provider); the ML Kit analyzers are
 * lightweight and created here.
 */
@Singleton
class AnalyzerRegistry @Inject constructor(
    handGestureAnalyzer: HandGestureAnalyzer
) {
    private val analyzers: Map<DetectionMode, FrameAnalyzer> = buildMap {
        put(DetectionMode.OBJECTS, ObjectDetectionAnalyzer())
        put(DetectionMode.SCENE, SceneLabelAnalyzer())
        put(DetectionMode.FACE, FaceAnalyzer())
        put(DetectionMode.POSE, PoseAnalyzer())
        put(DetectionMode.HANDS, handGestureAnalyzer)
        put(DetectionMode.TEXT, TextAnalyzer())
        put(DetectionMode.BARCODE, BarcodeAnalyzer())
    }

    fun analyzerFor(mode: DetectionMode): FrameAnalyzer =
        analyzers.getValue(mode)

    fun closeAll() = analyzers.values.forEach { runCatching { it.close() } }
}

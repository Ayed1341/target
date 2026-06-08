package com.ayed.visionai.lite.analysis

import com.ayed.visionai.lite.domain.model.DetectionMode
import com.ayed.visionai.lite.domain.model.SceneLabel
import com.ayed.visionai.lite.domain.model.VisionResult
import com.google.mlkit.vision.label.ImageLabeling
import com.google.mlkit.vision.label.defaults.ImageLabelerOptions
import kotlinx.coroutines.tasks.await

/** Scene / image labeling across 400+ everyday concepts (ML Kit). Feature 7. */
class SceneLabelAnalyzer : FrameAnalyzer {

    override val mode = DetectionMode.SCENE

    private val labeler = ImageLabeling.getClient(
        ImageLabelerOptions.Builder()
            .setConfidenceThreshold(0.5f)
            .build()
    )

    override suspend fun analyze(frame: AnalysisFrame): VisionResult {
        val labels = labeler.process(frame.inputImage).await()
        val scenes = labels
            .sortedByDescending { it.confidence }
            .take(6)
            .map { SceneLabel(it.text, it.confidence) }
        return VisionResult(
            mode = mode,
            sourceWidth = frame.uprightWidth,
            sourceHeight = frame.uprightHeight,
            isFrontCamera = frame.isFrontCamera,
            sceneLabels = scenes
        )
    }

    override fun close() = labeler.close()
}

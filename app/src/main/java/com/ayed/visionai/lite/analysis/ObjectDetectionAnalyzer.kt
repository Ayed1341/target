package com.ayed.visionai.lite.analysis

import com.ayed.visionai.lite.domain.model.DetectedBox
import com.ayed.visionai.lite.domain.model.DetectionMode
import com.ayed.visionai.lite.domain.model.VisionResult
import com.ayed.visionai.lite.util.CategoryMapper
import com.google.mlkit.vision.objects.ObjectDetection
import com.google.mlkit.vision.objects.defaults.ObjectDetectorOptions
import kotlinx.coroutines.tasks.await

/**
 * Real-time object detection + multi-object tracking + coarse classification
 * (ML Kit). Covers features: live detection, tracking, classification, bounding
 * boxes, confidence, counting, and the animal/food/vehicle/product filters.
 */
class ObjectDetectionAnalyzer : FrameAnalyzer {

    override val mode = DetectionMode.OBJECTS

    private val detector = ObjectDetection.getClient(
        ObjectDetectorOptions.Builder()
            .setDetectorMode(ObjectDetectorOptions.STREAM_MODE)
            .enableMultipleObjects()
            .enableClassification()
            .build()
    )

    override suspend fun analyze(frame: AnalysisFrame): VisionResult {
        val objects = detector.process(frame.inputImage).await()
        val boxes = objects.map { obj ->
            val rect = obj.boundingBox
            val topLabel = obj.labels.maxByOrNull { it.confidence }
            val labelText = topLabel?.text?.takeIf { it.isNotBlank() } ?: "Object"
            DetectedBox(
                left = rect.left.toFloat(),
                top = rect.top.toFloat(),
                right = rect.right.toFloat(),
                bottom = rect.bottom.toFloat(),
                label = labelText,
                confidence = topLabel?.confidence ?: 0.5f,
                trackingId = obj.trackingId,
                category = CategoryMapper.map(labelText)
            )
        }
        return VisionResult(
            mode = mode,
            sourceWidth = frame.uprightWidth,
            sourceHeight = frame.uprightHeight,
            isFrontCamera = frame.isFrontCamera,
            boxes = boxes
        )
    }

    override fun close() = detector.close()
}

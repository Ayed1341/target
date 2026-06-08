package com.ayed.visionai.lite.analysis

import com.ayed.visionai.lite.domain.model.DetectedBox
import com.ayed.visionai.lite.domain.model.DetectionMode
import com.ayed.visionai.lite.domain.model.LandmarkPoint
import com.ayed.visionai.lite.domain.model.ObjectCategory
import com.ayed.visionai.lite.domain.model.Skeleton
import com.ayed.visionai.lite.domain.model.VisionResult
import com.google.mlkit.vision.face.FaceDetection
import com.google.mlkit.vision.face.FaceDetectorOptions
import kotlinx.coroutines.tasks.await
import kotlin.math.roundToInt

/**
 * Face detection + facial landmark/contour detection + smile/eye classification
 * (ML Kit). Features 8 and 9.
 */
class FaceAnalyzer : FrameAnalyzer {

    override val mode = DetectionMode.FACE

    private val detector = FaceDetection.getClient(
        FaceDetectorOptions.Builder()
            .setPerformanceMode(FaceDetectorOptions.PERFORMANCE_MODE_FAST)
            .setLandmarkMode(FaceDetectorOptions.LANDMARK_MODE_ALL)
            .setContourMode(FaceDetectorOptions.CONTOUR_MODE_ALL)
            .setClassificationMode(FaceDetectorOptions.CLASSIFICATION_MODE_ALL)
            .enableTracking()
            .build()
    )

    override suspend fun analyze(frame: AnalysisFrame): VisionResult {
        val faces = detector.process(frame.inputImage).await()
        val boxes = ArrayList<DetectedBox>(faces.size)
        val skeletons = ArrayList<Skeleton>(faces.size)

        faces.forEach { face ->
            val rect = face.boundingBox
            val smile = face.smilingProbability
            val label = if (smile != null) {
                "Face · smile ${(smile * 100).roundToInt()}%"
            } else {
                "Face"
            }
            boxes.add(
                DetectedBox(
                    left = rect.left.toFloat(),
                    top = rect.top.toFloat(),
                    right = rect.right.toFloat(),
                    bottom = rect.bottom.toFloat(),
                    label = label,
                    confidence = smile ?: 1f,
                    trackingId = face.trackingId,
                    category = ObjectCategory.PERSON
                )
            )

            val points = face.allContours.flatMap { contour ->
                contour.points.map { LandmarkPoint(it.x, it.y) }
            }
            if (points.isNotEmpty()) {
                // Contour points are rendered as a dotted mesh (no fixed edges).
                skeletons.add(Skeleton(points = points, connections = emptyList()))
            }
        }

        return VisionResult(
            mode = mode,
            sourceWidth = frame.uprightWidth,
            sourceHeight = frame.uprightHeight,
            isFrontCamera = frame.isFrontCamera,
            boxes = boxes,
            skeletons = skeletons
        )
    }

    override fun close() = detector.close()
}

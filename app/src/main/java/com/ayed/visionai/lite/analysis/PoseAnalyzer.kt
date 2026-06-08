package com.ayed.visionai.lite.analysis

import com.ayed.visionai.lite.domain.model.DetectionMode
import com.ayed.visionai.lite.domain.model.LandmarkPoint
import com.ayed.visionai.lite.domain.model.Skeleton
import com.ayed.visionai.lite.domain.model.VisionResult
import com.google.mlkit.vision.pose.PoseDetection
import com.google.mlkit.vision.pose.PoseLandmark
import com.google.mlkit.vision.pose.defaults.PoseDetectorOptions
import kotlinx.coroutines.tasks.await

/** Full-body pose estimation / skeleton (ML Kit Pose). Feature 12. */
class PoseAnalyzer : FrameAnalyzer {

    override val mode = DetectionMode.POSE

    private val detector = PoseDetection.getClient(
        PoseDetectorOptions.Builder()
            .setDetectorMode(PoseDetectorOptions.STREAM_MODE)
            .build()
    )

    override suspend fun analyze(frame: AnalysisFrame): VisionResult {
        val pose = detector.process(frame.inputImage).await()
        val landmarks = pose.allPoseLandmarks
        if (landmarks.isEmpty()) {
            return VisionResult(
                mode = mode,
                sourceWidth = frame.uprightWidth,
                sourceHeight = frame.uprightHeight,
                isFrontCamera = frame.isFrontCamera
            )
        }

        // Index landmarks by their type so the connection table resolves cleanly.
        val typeToIndex = HashMap<Int, Int>(landmarks.size)
        val points = ArrayList<LandmarkPoint>(landmarks.size)
        landmarks.forEachIndexed { i, lm ->
            typeToIndex[lm.landmarkType] = i
            points.add(LandmarkPoint(lm.position.x, lm.position.y, lm.inFrameLikelihood))
        }

        val connections = CONNECTION_TYPES.mapNotNull { (a, b) ->
            val ia = typeToIndex[a]
            val ib = typeToIndex[b]
            if (ia != null && ib != null) ia to ib else null
        }

        return VisionResult(
            mode = mode,
            sourceWidth = frame.uprightWidth,
            sourceHeight = frame.uprightHeight,
            isFrontCamera = frame.isFrontCamera,
            skeletons = listOf(Skeleton(points, connections))
        )
    }

    override fun close() = detector.close()

    private companion object {
        val CONNECTION_TYPES = listOf(
            PoseLandmark.LEFT_SHOULDER to PoseLandmark.RIGHT_SHOULDER,
            PoseLandmark.LEFT_SHOULDER to PoseLandmark.LEFT_ELBOW,
            PoseLandmark.LEFT_ELBOW to PoseLandmark.LEFT_WRIST,
            PoseLandmark.RIGHT_SHOULDER to PoseLandmark.RIGHT_ELBOW,
            PoseLandmark.RIGHT_ELBOW to PoseLandmark.RIGHT_WRIST,
            PoseLandmark.LEFT_SHOULDER to PoseLandmark.LEFT_HIP,
            PoseLandmark.RIGHT_SHOULDER to PoseLandmark.RIGHT_HIP,
            PoseLandmark.LEFT_HIP to PoseLandmark.RIGHT_HIP,
            PoseLandmark.LEFT_HIP to PoseLandmark.LEFT_KNEE,
            PoseLandmark.LEFT_KNEE to PoseLandmark.LEFT_ANKLE,
            PoseLandmark.RIGHT_HIP to PoseLandmark.RIGHT_KNEE,
            PoseLandmark.RIGHT_KNEE to PoseLandmark.RIGHT_ANKLE,
            PoseLandmark.LEFT_ANKLE to PoseLandmark.LEFT_FOOT_INDEX,
            PoseLandmark.RIGHT_ANKLE to PoseLandmark.RIGHT_FOOT_INDEX
        )
    }
}

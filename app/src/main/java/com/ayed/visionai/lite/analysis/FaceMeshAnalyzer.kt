package com.ayed.visionai.lite.analysis

import com.ayed.visionai.lite.domain.model.DetectionMode
import com.ayed.visionai.lite.domain.model.LandmarkPoint
import com.ayed.visionai.lite.domain.model.Skeleton
import com.ayed.visionai.lite.domain.model.VisionResult
import com.google.mlkit.vision.facemesh.FaceMeshDetection
import com.google.mlkit.vision.facemesh.FaceMeshDetectorOptions
import kotlinx.coroutines.tasks.await

/**
 * High-density face mesh (ML Kit): up to 468 3D landmarks per face, rendered as a
 * point cloud. Advanced feature beyond basic face landmark detection.
 */
class FaceMeshAnalyzer : FrameAnalyzer {

    override val mode = DetectionMode.FACE_MESH

    private val detector = FaceMeshDetection.getClient(
        FaceMeshDetectorOptions.Builder()
            .setUseCase(FaceMeshDetectorOptions.FACE_MESH)
            .build()
    )

    override suspend fun analyze(frame: AnalysisFrame): VisionResult {
        val meshes = detector.process(frame.inputImage).await()
        val skeletons = meshes.map { mesh ->
            val points = mesh.allPoints.map { p ->
                LandmarkPoint(p.position.x, p.position.y)
            }
            Skeleton(points = points, connections = emptyList())
        }
        return VisionResult(
            mode = mode,
            sourceWidth = frame.uprightWidth,
            sourceHeight = frame.uprightHeight,
            isFrontCamera = frame.isFrontCamera,
            skeletons = skeletons
        )
    }

    override fun close() = detector.close()
}

package com.ayed.visionai.lite.domain.model

import androidx.compose.runtime.Immutable

/**
 * Semantic category derived from a label. Powers feature filters such as
 * animal / food / vehicle / product detection on top of the generic detector.
 */
enum class ObjectCategory {
    ANIMAL, FOOD, VEHICLE, PRODUCT, PERSON, PLANT, GENERIC
}

/** A single detected box (object, face, etc.) in upright image coordinates. */
@Immutable
data class DetectedBox(
    val left: Float,
    val top: Float,
    val right: Float,
    val bottom: Float,
    val label: String,
    val confidence: Float,
    val trackingId: Int? = null,
    val category: ObjectCategory = ObjectCategory.GENERIC
)

/** A normalized 2D point in upright image coordinates. */
@Immutable
data class LandmarkPoint(
    val x: Float,
    val y: Float,
    val inFrameLikelihood: Float = 1f
)

/** A connected skeleton/mesh made of points and the edges between them. */
@Immutable
data class Skeleton(
    val points: List<LandmarkPoint>,
    val connections: List<Pair<Int, Int>>
)

/** A scene/image label with confidence. */
@Immutable
data class SceneLabel(
    val text: String,
    val confidence: Float
)

/** A recognized barcode / QR code. */
@Immutable
data class BarcodeResult(
    val rawValue: String,
    val format: String,
    val box: DetectedBox
)

/**
 * The full per-frame analysis output that the UI overlay renders. Coordinates
 * are expressed in the upright (rotation-applied) source image space described
 * by [sourceWidth] x [sourceHeight].
 */
@Immutable
data class VisionResult(
    val mode: DetectionMode,
    val sourceWidth: Int,
    val sourceHeight: Int,
    val isFrontCamera: Boolean,
    val boxes: List<DetectedBox> = emptyList(),
    val skeletons: List<Skeleton> = emptyList(),
    val sceneLabels: List<SceneLabel> = emptyList(),
    val barcodes: List<BarcodeResult> = emptyList(),
    val recognizedText: String? = null,
    val gesture: String? = null,
    val statusMessage: String? = null
) {
    val objectCount: Int get() = boxes.size

    companion object {
        fun empty(mode: DetectionMode) = VisionResult(
            mode = mode,
            sourceWidth = 0,
            sourceHeight = 0,
            isFrontCamera = false
        )
    }
}

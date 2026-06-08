package com.ayed.visionai.lite.analysis

import android.graphics.Bitmap
import android.graphics.Matrix
import android.media.Image
import androidx.camera.core.ImageProxy
import com.google.mlkit.vision.common.InputImage

/**
 * A single camera frame ready for analysis. Exposes the same frame both as an
 * ML Kit [InputImage] (zero-copy from the YUV media image) and as an upright
 * [Bitmap] for MediaPipe — created lazily so we only pay for what each analyzer
 * actually uses.
 *
 * All analyzer outputs are expressed in the upright coordinate space described
 * by [uprightWidth] x [uprightHeight], i.e. after [rotationDegrees] is applied.
 */
class AnalysisFrame private constructor(
    private val mediaImage: Image,
    val rotationDegrees: Int,
    val isFrontCamera: Boolean,
    private val rawBitmap: Bitmap
) {
    val uprightWidth: Int =
        if (rotationDegrees == 90 || rotationDegrees == 270) mediaImage.height else mediaImage.width
    val uprightHeight: Int =
        if (rotationDegrees == 90 || rotationDegrees == 270) mediaImage.width else mediaImage.height

    val inputImage: InputImage by lazy {
        InputImage.fromMediaImage(mediaImage, rotationDegrees)
    }

    /** An upright RGB bitmap (rotation applied) for MediaPipe Tasks. */
    val uprightBitmap: Bitmap by lazy {
        if (rotationDegrees == 0) {
            rawBitmap
        } else {
            val matrix = Matrix().apply { postRotate(rotationDegrees.toFloat()) }
            Bitmap.createBitmap(rawBitmap, 0, 0, rawBitmap.width, rawBitmap.height, matrix, true)
        }
    }

    companion object {
        /** Builds a frame from a CameraX [ImageProxy]. Returns null if the proxy has no image. */
        fun from(imageProxy: ImageProxy, isFrontCamera: Boolean): AnalysisFrame? {
            val media = imageProxy.image ?: return null
            val bitmap = imageProxy.toBitmap()
            return AnalysisFrame(
                mediaImage = media,
                rotationDegrees = imageProxy.imageInfo.rotationDegrees,
                isFrontCamera = isFrontCamera,
                rawBitmap = bitmap
            )
        }
    }
}

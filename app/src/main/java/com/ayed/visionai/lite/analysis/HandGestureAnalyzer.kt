package com.ayed.visionai.lite.analysis

import android.content.Context
import com.ayed.visionai.lite.domain.model.DetectionMode
import com.ayed.visionai.lite.domain.model.LandmarkPoint
import com.ayed.visionai.lite.domain.model.Skeleton
import com.ayed.visionai.lite.domain.model.VisionResult
import com.google.mediapipe.framework.image.BitmapImageBuilder
import com.google.mediapipe.tasks.core.BaseOptions
import com.google.mediapipe.tasks.vision.core.RunningMode
import com.google.mediapipe.tasks.vision.gesturerecognizer.GestureRecognizer
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * Hand tracking (21-point skeleton) + basic gesture recognition via MediaPipe
 * Tasks GestureRecognizer. Features 10 and 11. The model is fetched once by
 * [GestureModelProvider]; until then this mode reports a status message.
 */
class HandGestureAnalyzer @Inject constructor(
    @ApplicationContext private val context: Context,
    private val modelProvider: GestureModelProvider
) : FrameAnalyzer {

    override val mode = DetectionMode.HANDS

    private val initMutex = Mutex()
    @Volatile private var recognizer: GestureRecognizer? = null
    @Volatile private var triedInit = false
    @Volatile private var unavailable = false

    private suspend fun ensureRecognizer(): GestureRecognizer? {
        recognizer?.let { return it }
        if (unavailable) return null
        return initMutex.withLock {
            recognizer?.let { return it }
            if (triedInit && unavailable) return null
            triedInit = true
            val buffer = modelProvider.loadModelBuffer()
            if (buffer == null) {
                unavailable = true
                return null
            }
            val options = GestureRecognizer.GestureRecognizerOptions.builder()
                .setBaseOptions(BaseOptions.builder().setModelAssetBuffer(buffer).build())
                .setRunningMode(RunningMode.IMAGE)
                .setNumHands(2)
                .build()
            GestureRecognizer.createFromOptions(context, options).also { recognizer = it }
        }
    }

    override suspend fun analyze(frame: AnalysisFrame): VisionResult {
        val client = ensureRecognizer()
            ?: return VisionResult(
                mode = mode,
                sourceWidth = frame.uprightWidth,
                sourceHeight = frame.uprightHeight,
                isFrontCamera = frame.isFrontCamera,
                statusMessage = if (unavailable) STATUS_UNAVAILABLE else STATUS_PREPARING
            )

        val width = frame.uprightWidth.toFloat()
        val height = frame.uprightHeight.toFloat()

        val result = withContext(Dispatchers.Default) {
            val mpImage = BitmapImageBuilder(frame.uprightBitmap).build()
            client.recognize(mpImage)
        }

        val skeletons = result.landmarks().map { hand ->
            val points = hand.map { lm -> LandmarkPoint(lm.x() * width, lm.y() * height) }
            Skeleton(points = points, connections = HAND_CONNECTIONS)
        }

        val gesture = result.gestures()
            .firstOrNull()
            ?.maxByOrNull { it.score() }
            ?.categoryName()
            ?.takeIf { it.isNotBlank() && it != "None" }

        return VisionResult(
            mode = mode,
            sourceWidth = frame.uprightWidth,
            sourceHeight = frame.uprightHeight,
            isFrontCamera = frame.isFrontCamera,
            skeletons = skeletons,
            gesture = gesture
        )
    }

    override fun close() {
        recognizer?.close()
        recognizer = null
    }

    companion object {
        const val STATUS_PREPARING = "PREPARING"
        const val STATUS_UNAVAILABLE = "UNAVAILABLE"

        /** Standard MediaPipe hand topology over the 21 landmarks. */
        val HAND_CONNECTIONS = listOf(
            0 to 1, 1 to 2, 2 to 3, 3 to 4,        // thumb
            0 to 5, 5 to 6, 6 to 7, 7 to 8,        // index
            5 to 9, 9 to 10, 10 to 11, 11 to 12,   // middle
            9 to 13, 13 to 14, 14 to 15, 15 to 16, // ring
            13 to 17, 17 to 18, 18 to 19, 19 to 20,// pinky
            0 to 17                                // palm base
        )
    }
}

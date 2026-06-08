package com.ayed.visionai.lite.domain.model

import androidx.annotation.StringRes
import com.ayed.visionai.lite.R

/**
 * The live analysis modes the user can switch between. Each maps to a single
 * on-device analyzer to keep real-time performance high on mobile GPUs.
 */
enum class DetectionMode(@StringRes val labelRes: Int) {
    OBJECTS(R.string.mode_objects),
    SCENE(R.string.mode_scene),
    FACE(R.string.mode_face),
    POSE(R.string.mode_pose),
    HANDS(R.string.mode_hands),
    TEXT(R.string.mode_text),
    BARCODE(R.string.mode_barcode);

    companion object {
        val default: DetectionMode = OBJECTS
    }
}

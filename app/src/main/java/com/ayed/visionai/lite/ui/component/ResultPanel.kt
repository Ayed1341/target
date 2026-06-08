package com.ayed.visionai.lite.ui.component

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.res.stringResource
import com.ayed.visionai.lite.R
import com.ayed.visionai.lite.analysis.HandGestureAnalyzer
import com.ayed.visionai.lite.domain.model.DetectionMode
import com.ayed.visionai.lite.domain.model.VisionResult
import kotlin.math.roundToInt

/**
 * The translucent dashboard card under the preview. Shows mode-specific,
 * real analysis output (counts, scene labels, recognized text, gesture, codes).
 */
@Composable
fun ResultPanel(
    result: VisionResult,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()
    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(20.dp))
            .background(Color(0xCC121821))
            .verticalScroll(scrollState)
            .padding(16.dp)
    ) {
        when (result.mode) {
            DetectionMode.OBJECTS -> {
                StatLine(stringResource(R.string.objects_in_frame, result.objectCount))
                result.boxes.distinctBy { it.label }.take(5).forEach { box ->
                    DetailLine(box.label, (box.confidence * 100).roundToInt())
                }
            }

            DetectionMode.SCENE -> {
                if (result.sceneLabels.isEmpty()) {
                    StatLine("—")
                } else {
                    result.sceneLabels.forEach { label ->
                        DetailLine(label.text, (label.confidence * 100).roundToInt())
                    }
                }
            }

            DetectionMode.FACE -> {
                StatLine(stringResource(R.string.objects_in_frame, result.boxes.size))
                result.boxes.forEach { box -> StatLine(box.label) }
            }

            DetectionMode.POSE -> {
                val count = result.skeletons.firstOrNull()?.points?.size ?: 0
                StatLine("Body landmarks: $count")
            }

            DetectionMode.HANDS -> {
                when (result.statusMessage) {
                    HandGestureAnalyzer.STATUS_PREPARING ->
                        StatLine(stringResource(R.string.hand_model_downloading))
                    HandGestureAnalyzer.STATUS_UNAVAILABLE ->
                        StatLine(stringResource(R.string.hand_model_unavailable))
                    else -> {
                        StatLine("Hands: ${result.skeletons.size}")
                        result.gesture?.let {
                            StatLine(stringResource(R.string.gesture_label, it))
                        }
                    }
                }
            }

            DetectionMode.TEXT -> {
                val text = result.recognizedText?.takeIf { it.isNotBlank() } ?: "—"
                StatLine(text)
            }

            DetectionMode.BARCODE -> {
                if (result.barcodes.isEmpty()) {
                    StatLine("—")
                } else {
                    result.barcodes.forEach { code ->
                        DetailLine(code.rawValue, label = code.format)
                    }
                }
            }
        }
    }
}

@Composable
private fun StatLine(text: String) {
    Text(
        text = text,
        style = MaterialTheme.typography.titleMedium,
        color = MaterialTheme.colorScheme.onSurface,
        modifier = Modifier.padding(vertical = 2.dp)
    )
}

@Composable
private fun DetailLine(label: String, confidence: Int) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 2.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurface
        )
        Text(
            text = "$confidence%",
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.primary,
            fontWeight = FontWeight.Bold
        )
    }
}

@Composable
private fun DetailLine(value: String, label: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 2.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(
            text = value,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurface
        )
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.primary
        )
    }
}

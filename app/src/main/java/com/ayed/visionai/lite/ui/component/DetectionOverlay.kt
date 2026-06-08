package com.ayed.visionai.lite.ui.component

import androidx.compose.foundation.Canvas
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.withTransform
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.text.TextMeasurer
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.drawText
import androidx.compose.ui.text.rememberTextMeasurer
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.ayed.visionai.lite.domain.model.ObjectCategory
import com.ayed.visionai.lite.domain.model.VisionResult
import kotlin.math.max
import kotlin.math.roundToInt

private val BoxColor = Color(0xFF00E5FF)
private val SkeletonColor = Color(0xFF00E5FF)
private val PointColor = Color(0xFFFF4081)
private val LabelBg = Color(0xCC0A0E14)

/**
 * Renders bounding boxes, skeletons/landmarks and labels on top of the live
 * camera preview. Maps upright source-image coordinates onto the canvas using
 * the same center-crop (FILL_CENTER) transform CameraX's PreviewView applies,
 * and mirrors horizontally for the front camera so overlays stay aligned.
 */
@Composable
fun DetectionOverlay(
    result: VisionResult,
    modifier: Modifier = Modifier
) {
    val textMeasurer = rememberTextMeasurer()
    Canvas(modifier = modifier) {
        val srcW = result.sourceWidth.toFloat()
        val srcH = result.sourceHeight.toFloat()
        if (srcW <= 0f || srcH <= 0f) return@Canvas

        val scale = max(size.width / srcW, size.height / srcH)
        val dx = (size.width - srcW * scale) / 2f
        val dy = (size.height - srcH * scale) / 2f
        val front = result.isFrontCamera

        fun mapX(x: Float): Float {
            val px = x * scale + dx
            return if (front) size.width - px else px
        }
        fun mapY(y: Float): Float = y * scale + dy

        // Selfie segmentation mask (drawn beneath everything else)
        result.segmentation?.let { seg ->
            val image = seg.maskBitmap.asImageBitmap()
            val dstW = (srcW * scale).toInt()
            val dstH = (srcH * scale).toInt()
            withTransform({
                if (front) scale(-1f, 1f)
            }) {
                drawImage(
                    image = image,
                    srcOffset = IntOffset.Zero,
                    srcSize = IntSize(seg.maskBitmap.width, seg.maskBitmap.height),
                    dstOffset = IntOffset(dx.toInt(), dy.toInt()),
                    dstSize = IntSize(dstW, dstH),
                    alpha = 0.55f
                )
            }
        }

        // Skeletons (pose / hands / face mesh)
        result.skeletons.forEach { skeleton ->
            skeleton.connections.forEach { (a, b) ->
                val pa = skeleton.points.getOrNull(a)
                val pb = skeleton.points.getOrNull(b)
                if (pa != null && pb != null) {
                    drawLine(
                        color = SkeletonColor,
                        start = Offset(mapX(pa.x), mapY(pa.y)),
                        end = Offset(mapX(pb.x), mapY(pb.y)),
                        strokeWidth = 4f
                    )
                }
            }
            skeleton.points.forEach { p ->
                if (p.inFrameLikelihood >= 0.3f) {
                    drawCircle(
                        color = PointColor,
                        radius = if (skeleton.connections.isEmpty()) 2.5f else 6f,
                        center = Offset(mapX(p.x), mapY(p.y))
                    )
                }
            }
        }

        // Bounding boxes + labels
        result.boxes.forEach { box ->
            val l = mapX(if (front) box.right else box.left)
            val t = mapY(box.top)
            val r = mapX(if (front) box.left else box.right)
            val bm = mapY(box.bottom)
            val left = minOf(l, r)
            val top = minOf(t, bm)
            val width = kotlin.math.abs(r - l)
            val height = kotlin.math.abs(bm - t)

            val color = colorFor(box.category)
            drawRoundedBox(left, top, width, height, color)

            val confidencePct = (box.confidence * 100).roundToInt()
            val label = if (box.confidence in 0.01f..0.999f) {
                "${box.label}  $confidencePct%"
            } else {
                box.label
            }
            drawLabel(textMeasurer, label, left, top, color)
        }
    }
}

private fun DrawScope.drawRoundedBox(
    left: Float, top: Float, width: Float, height: Float, color: Color
) {
    drawRect(
        color = color,
        topLeft = Offset(left, top),
        size = Size(width, height),
        style = Stroke(width = 4f)
    )
}

private fun DrawScope.drawLabel(
    measurer: TextMeasurer, text: String, left: Float, top: Float, color: Color
) {
    val style = TextStyle(color = Color.White, fontSize = 12.sp)
    val layout = measurer.measure(text, style)
    val padding = 6f
    val bgTop = (top - layout.size.height - padding * 2).coerceAtLeast(0f)
    drawRect(
        color = LabelBg,
        topLeft = Offset(left, bgTop),
        size = Size(layout.size.width + padding * 2, layout.size.height + padding * 2)
    )
    drawRect(
        color = color,
        topLeft = Offset(left, bgTop),
        size = Size(4f, layout.size.height + padding * 2)
    )
    drawText(layout, topLeft = Offset(left + padding + 2f, bgTop + padding))
}

private fun colorFor(category: ObjectCategory): Color = when (category) {
    ObjectCategory.ANIMAL -> Color(0xFFFFB300)
    ObjectCategory.FOOD -> Color(0xFF69F0AE)
    ObjectCategory.VEHICLE -> Color(0xFF40C4FF)
    ObjectCategory.PRODUCT -> Color(0xFFB388FF)
    ObjectCategory.PERSON -> Color(0xFFFF8A80)
    ObjectCategory.PLANT -> Color(0xFF76FF03)
    ObjectCategory.GENERIC -> BoxColor
}

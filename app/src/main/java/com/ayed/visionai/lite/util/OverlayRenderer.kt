package com.ayed.visionai.lite.util

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Rect
import com.ayed.visionai.lite.domain.model.VisionResult
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.roundToInt

/**
 * Draws the analysis overlay (boxes, skeletons, segmentation mask, header) onto a
 * captured frame so the saved snapshot matches what the user saw on screen. Uses
 * the same center-crop mapping and front-camera mirroring as the live overlay.
 */
object OverlayRenderer {

    fun render(source: Bitmap, result: VisionResult): Bitmap {
        val output = source.copy(Bitmap.Config.ARGB_8888, true)
        val canvas = Canvas(output)
        val bw = output.width.toFloat()
        val bh = output.height.toFloat()
        val sw = result.sourceWidth.toFloat()
        val sh = result.sourceHeight.toFloat()

        if (sw > 0f && sh > 0f) {
            val scale = max(bw / sw, bh / sh)
            val dx = (bw - sw * scale) / 2f
            val dy = (bh - sh * scale) / 2f
            val front = result.isFrontCamera
            fun mapX(x: Float) = (x * scale + dx).let { if (front) bw - it else it }
            fun mapY(y: Float) = y * scale + dy

            result.segmentation?.let { seg ->
                val maskPaint = Paint().apply { alpha = 140 }
                canvas.drawBitmap(
                    seg.maskBitmap,
                    Rect(0, 0, seg.maskBitmap.width, seg.maskBitmap.height),
                    android.graphics.RectF(0f, 0f, bw, bh),
                    maskPaint
                )
            }

            val linePaint = Paint().apply {
                color = Color.parseColor("#00E5FF")
                strokeWidth = 5f
                isAntiAlias = true
            }
            val pointPaint = Paint().apply {
                color = Color.parseColor("#FF4081")
                isAntiAlias = true
            }
            result.skeletons.forEach { skeleton ->
                skeleton.connections.forEach { (a, b) ->
                    val pa = skeleton.points.getOrNull(a)
                    val pb = skeleton.points.getOrNull(b)
                    if (pa != null && pb != null) {
                        canvas.drawLine(mapX(pa.x), mapY(pa.y), mapX(pb.x), mapY(pb.y), linePaint)
                    }
                }
                val radius = if (skeleton.connections.isEmpty()) 3f else 7f
                skeleton.points.forEach { canvas.drawPoint(mapX(it.x), mapY(it.y), pointPaint.apply { strokeWidth = radius * 2 }) }
            }

            val boxPaint = Paint().apply {
                color = Color.parseColor("#00E5FF")
                style = Paint.Style.STROKE
                strokeWidth = 5f
                isAntiAlias = true
            }
            val textPaint = Paint().apply {
                color = Color.WHITE
                textSize = 34f
                isAntiAlias = true
            }
            val textBg = Paint().apply { color = Color.parseColor("#CC0A0E14") }
            result.boxes.forEach { box ->
                val l = mapX(if (front) box.right else box.left)
                val t = mapY(box.top)
                val r = mapX(if (front) box.left else box.right)
                val bm = mapY(box.bottom)
                val left = minOf(l, r)
                val top = minOf(t, bm)
                canvas.drawRect(left, top, left + abs(r - l), top + abs(bm - t), boxPaint)
                val label = if (box.confidence in 0.01f..0.999f) {
                    "${box.label} ${(box.confidence * 100).roundToInt()}%"
                } else box.label
                val tw = textPaint.measureText(label)
                canvas.drawRect(left, top - 44f, left + tw + 12f, top, textBg)
                canvas.drawText(label, left + 6f, top - 12f, textPaint)
            }
        }

        // Header watermark
        val header = Paint().apply {
            color = Color.parseColor("#00E5FF")
            textSize = 40f
            isAntiAlias = true
            isFakeBoldText = true
        }
        canvas.drawText("AYED VISION AI LITE", 24f, 56f, header)
        return output
    }
}

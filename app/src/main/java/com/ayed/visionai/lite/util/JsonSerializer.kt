package com.ayed.visionai.lite.util

import com.ayed.visionai.lite.data.local.DetectionEntity
import com.ayed.visionai.lite.domain.model.VisionResult
import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Converts vision results and history records to JSON. Uses the platform
 * [org.json] library so there is no extra serialization dependency.
 */
object JsonSerializer {

    private val isoFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSSZ", Locale.US)

    /** Per-frame result -> JSON object (used for capture + DB storage). */
    fun toJson(result: VisionResult, timestamp: Long = System.currentTimeMillis()): JSONObject {
        val root = JSONObject()
        root.put("app", "Ayed Vision AI Lite")
        root.put("author", "Ayed Oraybi")
        root.put("timestamp", isoFormat.format(Date(timestamp)))
        root.put("mode", result.mode.name)
        root.put("sourceWidth", result.sourceWidth)
        root.put("sourceHeight", result.sourceHeight)
        root.put("frontCamera", result.isFrontCamera)
        root.put("objectCount", result.objectCount)

        val boxes = JSONArray()
        result.boxes.forEach { b ->
            boxes.put(JSONObject().apply {
                put("label", b.label)
                put("category", b.category.name)
                put("confidence", round2(b.confidence))
                b.trackingId?.let { put("trackingId", it) }
                put("box", JSONObject().apply {
                    put("left", round2(b.left))
                    put("top", round2(b.top))
                    put("right", round2(b.right))
                    put("bottom", round2(b.bottom))
                })
            })
        }
        root.put("objects", boxes)

        val scenes = JSONArray()
        result.sceneLabels.forEach { s ->
            scenes.put(JSONObject().apply {
                put("label", s.text)
                put("confidence", round2(s.confidence))
            })
        }
        root.put("sceneLabels", scenes)

        val codes = JSONArray()
        result.barcodes.forEach { c ->
            codes.put(JSONObject().apply {
                put("value", c.rawValue)
                put("format", c.format)
            })
        }
        root.put("barcodes", codes)

        result.recognizedText?.let { root.put("recognizedText", it) }
        result.gesture?.let { root.put("gesture", it) }
        root.put("skeletons", result.skeletons.size)
        return root
    }

    fun summaryOf(result: VisionResult): Triple<Int, String, Float> {
        val top = result.boxes.maxByOrNull { it.confidence }
        val sceneTop = result.sceneLabels.maxByOrNull { it.confidence }
        return when {
            top != null -> Triple(result.objectCount, top.label, top.confidence)
            sceneTop != null -> Triple(result.sceneLabels.size, sceneTop.text, sceneTop.confidence)
            result.barcodes.isNotEmpty() ->
                Triple(result.barcodes.size, result.barcodes.first().rawValue, 1f)
            !result.recognizedText.isNullOrBlank() ->
                Triple(1, result.recognizedText.take(40), 1f)
            result.gesture != null -> Triple(1, result.gesture, 1f)
            else -> Triple(0, result.mode.name, 0f)
        }
    }

    /** Whole history -> pretty JSON document for file export. */
    fun exportHistory(records: List<DetectionEntity>): String {
        val root = JSONObject()
        root.put("app", "Ayed Vision AI Lite")
        root.put("author", "Ayed Oraybi")
        root.put("exportedAt", isoFormat.format(Date()))
        root.put("count", records.size)
        val arr = JSONArray()
        records.forEach { r ->
            arr.put(JSONObject().apply {
                put("id", r.id)
                put("timestamp", isoFormat.format(Date(r.timestamp)))
                put("mode", r.mode)
                put("objectCount", r.objectCount)
                put("topLabel", r.topLabel)
                put("topConfidence", round2(r.topConfidence))
                put("details", JSONObject(r.detailsJson))
            })
        }
        root.put("detections", arr)
        return root.toString(2)
    }

    private fun round2(v: Float): Double = Math.round(v * 100.0) / 100.0
}

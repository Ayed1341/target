package com.ayed.visionai.lite.analysis

import com.ayed.visionai.lite.domain.model.BarcodeResult
import com.ayed.visionai.lite.domain.model.DetectedBox
import com.ayed.visionai.lite.domain.model.DetectionMode
import com.ayed.visionai.lite.domain.model.ObjectCategory
import com.ayed.visionai.lite.domain.model.VisionResult
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.barcode.common.Barcode
import kotlinx.coroutines.tasks.await

/** QR code + barcode scanning (ML Kit). Features 14 and 15. */
class BarcodeAnalyzer : FrameAnalyzer {

    override val mode = DetectionMode.BARCODE

    private val scanner = BarcodeScanning.getClient()

    override suspend fun analyze(frame: AnalysisFrame): VisionResult {
        val barcodes = scanner.process(frame.inputImage).await()
        val boxes = ArrayList<DetectedBox>(barcodes.size)
        val results = ArrayList<BarcodeResult>(barcodes.size)

        barcodes.forEach { code ->
            val rect = code.boundingBox ?: return@forEach
            val value = code.rawValue ?: code.displayValue ?: return@forEach
            val box = DetectedBox(
                left = rect.left.toFloat(),
                top = rect.top.toFloat(),
                right = rect.right.toFloat(),
                bottom = rect.bottom.toFloat(),
                label = value.take(24),
                confidence = 1f,
                category = ObjectCategory.GENERIC
            )
            boxes.add(box)
            results.add(BarcodeResult(value, formatName(code.format), box))
        }

        return VisionResult(
            mode = mode,
            sourceWidth = frame.uprightWidth,
            sourceHeight = frame.uprightHeight,
            isFrontCamera = frame.isFrontCamera,
            boxes = boxes,
            barcodes = results
        )
    }

    override fun close() = scanner.close()

    private fun formatName(format: Int): String = when (format) {
        Barcode.FORMAT_QR_CODE -> "QR_CODE"
        Barcode.FORMAT_AZTEC -> "AZTEC"
        Barcode.FORMAT_DATA_MATRIX -> "DATA_MATRIX"
        Barcode.FORMAT_PDF417 -> "PDF417"
        Barcode.FORMAT_EAN_13 -> "EAN_13"
        Barcode.FORMAT_EAN_8 -> "EAN_8"
        Barcode.FORMAT_UPC_A -> "UPC_A"
        Barcode.FORMAT_UPC_E -> "UPC_E"
        Barcode.FORMAT_CODE_128 -> "CODE_128"
        Barcode.FORMAT_CODE_39 -> "CODE_39"
        Barcode.FORMAT_CODE_93 -> "CODE_93"
        Barcode.FORMAT_CODABAR -> "CODABAR"
        Barcode.FORMAT_ITF -> "ITF"
        else -> "UNKNOWN"
    }
}

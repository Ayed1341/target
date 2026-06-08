package com.ayed.visionai.lite.data.repository

import android.content.Context
import com.ayed.visionai.lite.data.local.DetectionDao
import com.ayed.visionai.lite.data.local.DetectionEntity
import com.ayed.visionai.lite.domain.model.VisionResult
import com.ayed.visionai.lite.domain.repository.DetectionRepository
import com.ayed.visionai.lite.util.JsonSerializer
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.withContext
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DetectionRepositoryImpl @Inject constructor(
    private val dao: DetectionDao,
    @ApplicationContext private val context: Context
) : DetectionRepository {

    override fun observeHistory(): Flow<List<DetectionEntity>> = dao.observeAll()

    override suspend fun save(result: VisionResult): Long = withContext(Dispatchers.IO) {
        val (count, topLabel, topConf) = JsonSerializer.summaryOf(result)
        val json = JsonSerializer.toJson(result).toString()
        dao.insert(
            DetectionEntity(
                timestamp = System.currentTimeMillis(),
                mode = result.mode.name,
                objectCount = count,
                topLabel = topLabel,
                topConfidence = topConf,
                detailsJson = json
            )
        )
    }

    override suspend fun deleteById(id: Long) = withContext(Dispatchers.IO) {
        dao.deleteById(id)
    }

    override suspend fun clear() = withContext(Dispatchers.IO) {
        dao.clear()
    }

    override suspend fun exportHistoryToFile(): File = withContext(Dispatchers.IO) {
        val records = dao.getAll()
        val json = JsonSerializer.exportHistory(records)
        val dir = File(context.getExternalFilesDir(null), "exports").apply { mkdirs() }
        val stamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(Date())
        val file = File(dir, "ayed_vision_export_$stamp.json")
        file.writeText(json)
        file
    }
}

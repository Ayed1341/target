package com.ayed.visionai.lite.domain.repository

import com.ayed.visionai.lite.data.local.DetectionEntity
import com.ayed.visionai.lite.domain.model.VisionResult
import kotlinx.coroutines.flow.Flow
import java.io.File

interface DetectionRepository {
    fun observeHistory(): Flow<List<DetectionEntity>>
    suspend fun save(result: VisionResult): Long
    suspend fun deleteById(id: Long)
    suspend fun clear()
    /** Writes the full history as a JSON document and returns the file. */
    suspend fun exportHistoryToFile(): File
}

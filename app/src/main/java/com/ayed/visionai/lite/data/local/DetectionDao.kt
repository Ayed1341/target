package com.ayed.visionai.lite.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface DetectionDao {

    @Insert
    suspend fun insert(entity: DetectionEntity): Long

    @Query("SELECT * FROM detections ORDER BY timestamp DESC")
    fun observeAll(): Flow<List<DetectionEntity>>

    @Query("SELECT * FROM detections ORDER BY timestamp DESC")
    suspend fun getAll(): List<DetectionEntity>

    @Query("DELETE FROM detections WHERE id = :id")
    suspend fun deleteById(id: Long)

    @Query("DELETE FROM detections")
    suspend fun clear()
}

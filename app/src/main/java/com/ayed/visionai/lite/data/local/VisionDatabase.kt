package com.ayed.visionai.lite.data.local

import androidx.room.Database
import androidx.room.RoomDatabase

@Database(entities = [DetectionEntity::class], version = 1, exportSchema = false)
abstract class VisionDatabase : RoomDatabase() {
    abstract fun detectionDao(): DetectionDao

    companion object {
        const val NAME = "ayed_vision.db"
    }
}

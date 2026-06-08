package com.ayed.visionai.lite.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

/** A persisted detection snapshot shown in the History screen. */
@Entity(tableName = "detections")
data class DetectionEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val timestamp: Long,
    val mode: String,
    val objectCount: Int,
    val topLabel: String,
    val topConfidence: Float,
    /** Full machine-readable JSON payload for export. */
    val detailsJson: String
)

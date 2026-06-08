package com.ayed.visionai.lite.di

import android.content.Context
import androidx.room.Room
import com.ayed.visionai.lite.data.local.DetectionDao
import com.ayed.visionai.lite.data.local.VisionDatabase
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): VisionDatabase =
        Room.databaseBuilder(context, VisionDatabase::class.java, VisionDatabase.NAME)
            .fallbackToDestructiveMigration()
            .build()

    @Provides
    fun provideDetectionDao(database: VisionDatabase): DetectionDao = database.detectionDao()
}

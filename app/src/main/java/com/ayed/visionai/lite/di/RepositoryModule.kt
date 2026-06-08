package com.ayed.visionai.lite.di

import com.ayed.visionai.lite.data.repository.DetectionRepositoryImpl
import com.ayed.visionai.lite.domain.repository.DetectionRepository
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds
    @Singleton
    abstract fun bindDetectionRepository(
        impl: DetectionRepositoryImpl
    ): DetectionRepository
}

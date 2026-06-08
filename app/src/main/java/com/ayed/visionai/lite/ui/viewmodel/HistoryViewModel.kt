package com.ayed.visionai.lite.ui.viewmodel

import android.content.Context
import android.content.Intent
import androidx.core.content.FileProvider
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ayed.visionai.lite.data.local.DetectionEntity
import com.ayed.visionai.lite.domain.repository.DetectionRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class HistoryViewModel @Inject constructor(
    private val repository: DetectionRepository,
    @ApplicationContext private val appContext: Context
) : ViewModel() {

    val history: StateFlow<List<DetectionEntity>> = repository.observeHistory()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    fun delete(id: Long) {
        viewModelScope.launch { repository.deleteById(id) }
    }

    fun clearAll() {
        viewModelScope.launch { repository.clear() }
    }

    fun exportJson(onExported: (String) -> Unit) {
        viewModelScope.launch {
            val file = repository.exportHistoryToFile()
            val uri = FileProvider.getUriForFile(
                appContext,
                "${appContext.packageName}.fileprovider",
                file
            )
            val share = Intent(Intent.ACTION_SEND).apply {
                type = "application/json"
                putExtra(Intent.EXTRA_STREAM, uri)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            appContext.startActivity(
                Intent.createChooser(share, file.name).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            )
            onExported(file.name)
        }
    }
}

package com.ayed.visionai.lite.ui.viewmodel

import android.content.Context
import android.content.Intent
import androidx.camera.core.CameraSelector
import androidx.core.content.FileProvider
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ayed.visionai.lite.analysis.AnalyzerRegistry
import com.ayed.visionai.lite.analysis.VisionImageAnalyzer
import com.ayed.visionai.lite.domain.model.DetectionMode
import com.ayed.visionai.lite.domain.model.VisionResult
import com.ayed.visionai.lite.domain.repository.DetectionRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class CameraUiState(
    val mode: DetectionMode = DetectionMode.default,
    val lensFacing: Int = CameraSelector.LENS_FACING_BACK,
    val result: VisionResult = VisionResult.empty(DetectionMode.default),
    val fps: Int = 0
)

@HiltViewModel
class CameraViewModel @Inject constructor(
    private val registry: AnalyzerRegistry,
    private val repository: DetectionRepository,
    @ApplicationContext private val appContext: Context
) : ViewModel() {

    private val _uiState = MutableStateFlow(CameraUiState())
    val uiState: StateFlow<CameraUiState> = _uiState.asStateFlow()

    private val _messages = MutableStateFlow<String?>(null)
    val messages: StateFlow<String?> = _messages.asStateFlow()

    /** The CameraX analyzer, scoped to this ViewModel's lifecycle. */
    val imageAnalyzer = VisionImageAnalyzer(
        scope = viewModelScope,
        registry = registry,
        onResult = { result -> _uiState.update { it.copy(result = result) } },
        onFps = { fps -> _uiState.update { it.copy(fps = fps) } }
    ).apply {
        mode = DetectionMode.default
        isFrontCamera = false
    }

    fun setMode(mode: DetectionMode) {
        imageAnalyzer.mode = mode
        _uiState.update { it.copy(mode = mode, result = VisionResult.empty(mode)) }
    }

    fun toggleCamera() {
        val newFacing = if (_uiState.value.lensFacing == CameraSelector.LENS_FACING_BACK) {
            CameraSelector.LENS_FACING_FRONT
        } else {
            CameraSelector.LENS_FACING_BACK
        }
        imageAnalyzer.isFrontCamera = newFacing == CameraSelector.LENS_FACING_FRONT
        _uiState.update { it.copy(lensFacing = newFacing) }
    }

    /** Feature 20: capture the current frame's analysis and persist it. */
    fun captureAndSave(savedMessage: String) {
        val result = _uiState.value.result
        viewModelScope.launch {
            repository.save(result)
            _messages.value = savedMessage
        }
    }

    fun exportJson(exportedMessageTemplate: String) {
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
            _messages.value = exportedMessageTemplate.format(file.name)
        }
    }

    fun consumeMessage() {
        _messages.value = null
    }
    // Analyzers live in the app-scoped AnalyzerRegistry singleton and are reused
    // across configuration changes, so they are intentionally not closed here.
}

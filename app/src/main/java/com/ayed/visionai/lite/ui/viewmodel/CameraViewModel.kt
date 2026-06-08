package com.ayed.visionai.lite.ui.viewmodel

import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import androidx.camera.core.CameraSelector
import androidx.core.content.FileProvider
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ayed.visionai.lite.analysis.AnalyzerRegistry
import com.ayed.visionai.lite.analysis.LanguageProcessor
import com.ayed.visionai.lite.analysis.VisionImageAnalyzer
import com.ayed.visionai.lite.domain.model.DetectionMode
import com.ayed.visionai.lite.domain.model.VisionResult
import com.ayed.visionai.lite.domain.repository.DetectionRepository
import com.ayed.visionai.lite.util.OverlayRenderer
import com.ayed.visionai.lite.util.SnapshotSaver
import com.ayed.visionai.lite.util.TtsManager
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import javax.inject.Inject

data class CameraUiState(
    val mode: DetectionMode = DetectionMode.default,
    val lensFacing: Int = CameraSelector.LENS_FACING_BACK,
    val result: VisionResult = VisionResult.empty(DetectionMode.default),
    val fps: Int = 0,
    val torchEnabled: Boolean = false,
    val translatedText: String? = null
)

@HiltViewModel
class CameraViewModel @Inject constructor(
    private val registry: AnalyzerRegistry,
    private val repository: DetectionRepository,
    private val languageProcessor: LanguageProcessor,
    private val ttsManager: TtsManager,
    private val snapshotSaver: SnapshotSaver,
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
        _uiState.update { it.copy(mode = mode, result = VisionResult.empty(mode), translatedText = null) }
    }

    /** Feature: torch / flashlight toggle (applied by the camera preview). */
    fun toggleTorch() {
        _uiState.update { it.copy(torchEnabled = !it.torchEnabled) }
    }

    /** Feature: on-device translation (Arabic ⇄ English) of recognized text. */
    fun translateCurrentText(unavailableMessage: String) {
        val text = _uiState.value.result.recognizedText ?: return
        viewModelScope.launch {
            val translated = languageProcessor.translateArabicEnglish(text)
            if (translated != null) {
                _uiState.update { it.copy(translatedText = translated) }
            } else {
                _messages.value = unavailableMessage
            }
        }
    }

    /** Feature: read the current result aloud via Text-to-Speech. */
    fun speakCurrent() {
        val result = _uiState.value.result
        val text = result.recognizedText
            ?: result.sceneLabels.joinToString(", ") { it.text }.ifBlank { null }
            ?: result.boxes.joinToString(", ") { it.label }.ifBlank { null }
            ?: return
        val arabic = result.detectedLanguage == "ar"
        ttsManager.speak(text, arabic)
    }

    /** Feature: save an annotated snapshot of the current frame to the gallery. */
    fun saveSnapshot(frame: Bitmap, savedTemplate: String, failedMessage: String) {
        val result = _uiState.value.result
        viewModelScope.launch {
            try {
                val annotated = withContext(Dispatchers.Default) {
                    OverlayRenderer.render(frame, result)
                }
                val name = snapshotSaver.save(annotated)
                _messages.value = savedTemplate.format(name)
            } catch (e: Exception) {
                _messages.value = failedMessage
            }
        }
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

    override fun onCleared() {
        super.onCleared()
        ttsManager.stop()
        // Analyzers live in the app-scoped AnalyzerRegistry singleton and are reused
        // across configuration changes, so they are intentionally not closed here.
    }
}

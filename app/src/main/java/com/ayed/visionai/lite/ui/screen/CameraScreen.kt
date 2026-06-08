package com.ayed.visionai.lite.ui.screen

import android.Manifest
import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.Cameraswitch
import androidx.compose.material.icons.filled.FileDownload
import androidx.compose.material.icons.filled.History
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.ayed.visionai.lite.R
import com.ayed.visionai.lite.domain.model.DetectionMode
import com.ayed.visionai.lite.ui.component.CameraPreview
import com.ayed.visionai.lite.ui.component.DetectionOverlay
import com.ayed.visionai.lite.ui.component.ResultPanel
import com.ayed.visionai.lite.ui.theme.DeepSpace
import com.ayed.visionai.lite.ui.viewmodel.CameraViewModel
import com.google.accompanist.permissions.ExperimentalPermissionsApi
import com.google.accompanist.permissions.isGranted
import com.google.accompanist.permissions.rememberPermissionState
import com.google.accompanist.permissions.shouldShowRationale

@OptIn(ExperimentalPermissionsApi::class)
@Composable
fun CameraScreen(
    onOpenHistory: () -> Unit,
    viewModel: CameraViewModel = hiltViewModel()
) {
    val cameraPermission = rememberPermissionState(Manifest.permission.CAMERA)

    if (!cameraPermission.status.isGranted) {
        PermissionScreen(
            shouldShowRationale = cameraPermission.status.shouldShowRationale,
            onRequest = { cameraPermission.launchPermissionRequest() }
        )
        return
    }

    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val message by viewModel.messages.collectAsStateWithLifecycle()
    val snackbarHostState = remember { SnackbarHostState() }

    val savedMsg = stringResource(R.string.saved_to_history)
    val exportTemplate = stringResource(R.string.exported_to)

    LaunchedEffect(message) {
        message?.let {
            snackbarHostState.showSnackbar(it)
            viewModel.consumeMessage()
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(DeepSpace)
    ) {
        CameraPreview(
            lensFacing = uiState.lensFacing,
            analyzer = viewModel.imageAnalyzer,
            modifier = Modifier.fillMaxSize()
        )
        DetectionOverlay(
            result = uiState.result,
            modifier = Modifier.fillMaxSize()
        )

        TopBar(
            fps = uiState.fps,
            modifier = Modifier
                .align(Alignment.TopCenter)
                .statusBarsPadding()
        )

        Column(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth()
                .navigationBarsPadding()
                .padding(horizontal = 12.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            ResultPanel(result = uiState.result)

            ModeSelector(
                selected = uiState.mode,
                onSelect = viewModel::setMode
            )

            ActionRow(
                onCapture = { viewModel.captureAndSave(savedMsg) },
                onExport = { viewModel.exportJson(exportTemplate) },
                onSwitchCamera = viewModel::toggleCamera,
                onHistory = onOpenHistory
            )
        }

        SnackbarHost(
            hostState = snackbarHostState,
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .navigationBarsPadding()
                .padding(bottom = 180.dp)
        )
    }
}

@Composable
private fun TopBar(fps: Int, modifier: Modifier = Modifier) {
    Surface(
        modifier = modifier.padding(12.dp),
        shape = RoundedCornerShape(16.dp),
        color = Color(0xCC121821)
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Column {
                Text(
                    text = stringResource(R.string.app_name),
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = stringResource(R.string.author),
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            Text(
                text = stringResource(R.string.fps_format, fps),
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.onSurface
            )
        }
    }
}

@Composable
private fun ModeSelector(
    selected: DetectionMode,
    onSelect: (DetectionMode) -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .horizontalScroll(rememberScrollState()),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        DetectionMode.entries.forEach { mode ->
            FilterChip(
                selected = mode == selected,
                onClick = { onSelect(mode) },
                label = { Text(stringResource(mode.labelRes)) },
                colors = FilterChipDefaults.filterChipColors(
                    selectedContainerColor = MaterialTheme.colorScheme.primary,
                    selectedLabelColor = MaterialTheme.colorScheme.onPrimary,
                    containerColor = Color(0xCC121821),
                    labelColor = MaterialTheme.colorScheme.onSurface
                )
            )
        }
    }
}

@Composable
private fun ActionRow(
    onCapture: () -> Unit,
    onExport: () -> Unit,
    onSwitchCamera: () -> Unit,
    onHistory: () -> Unit
) {
    Surface(
        shape = RoundedCornerShape(20.dp),
        color = Color(0xCC121821),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 8.dp, vertical = 6.dp),
            horizontalArrangement = Arrangement.SpaceEvenly,
            verticalAlignment = Alignment.CenterVertically
        ) {
            ActionButton(Icons.Filled.History, R.string.history, onHistory)
            ActionButton(Icons.Filled.CameraAlt, R.string.capture, onCapture)
            ActionButton(Icons.Filled.Cameraswitch, R.string.switch_camera, onSwitchCamera)
            ActionButton(Icons.Filled.FileDownload, R.string.export_json, onExport)
        }
    }
}

@Composable
private fun ActionButton(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    labelRes: Int,
    onClick: () -> Unit
) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        IconButton(onClick = onClick) {
            Icon(
                imageVector = icon,
                contentDescription = stringResource(labelRes),
                tint = MaterialTheme.colorScheme.primary
            )
        }
        Text(
            text = stringResource(labelRes),
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

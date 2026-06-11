package com.ayed.visionai.lite.ui.component

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.VolumeUp
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.ayed.visionai.lite.R
import com.ayed.visionai.lite.ai.AiProvider
import com.ayed.visionai.lite.ai.AiSettings

/** Floating card that shows the AI assistant's answer (or a loading spinner). */
@Composable
fun AiAnswerCard(
    loading: Boolean,
    answer: String?,
    onSpeak: () -> Unit,
    onDismiss: () -> Unit,
    modifier: Modifier = Modifier
) {
    if (!loading && answer == null) return
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        color = Color(0xF21A2230)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = stringResource(R.string.ai_assistant),
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Bold
                )
                Row {
                    if (answer != null) {
                        IconButton(onClick = onSpeak) {
                            Icon(
                                Icons.Filled.VolumeUp,
                                contentDescription = stringResource(R.string.speak),
                                tint = MaterialTheme.colorScheme.primary
                            )
                        }
                    }
                    IconButton(onClick = onDismiss) {
                        Icon(
                            Icons.Filled.Close,
                            contentDescription = stringResource(R.string.back),
                            tint = MaterialTheme.colorScheme.onSurface
                        )
                    }
                }
            }
            if (loading) {
                Row(
                    modifier = Modifier.fillMaxWidth().padding(vertical = 16.dp),
                    horizontalArrangement = Arrangement.Center
                ) {
                    CircularProgressIndicator(color = MaterialTheme.colorScheme.primary)
                }
            } else if (answer != null) {
                SelectionContainer {
                    Text(
                        text = answer,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurface,
                        modifier = Modifier
                            .heightIn(max = 280.dp)
                            .verticalScroll(rememberScrollState())
                    )
                }
            }
        }
    }
}

/** Dialog to configure the cloud AI provider, API key and model. */
@Composable
fun AiSettingsDialog(
    current: AiSettings,
    onDismiss: () -> Unit,
    onSave: (AiSettings) -> Unit
) {
    var provider by remember { mutableStateOf(current.provider) }
    var apiKey by remember { mutableStateOf(current.apiKey) }
    var model by remember { mutableStateOf(current.model) }
    var baseUrl by remember { mutableStateOf(current.baseUrl) }

    AlertDialog(
        onDismissRequest = onDismiss,
        confirmButton = {
            TextButton(onClick = {
                val resolvedModel = model.ifBlank {
                    current.copy(provider = provider).defaultModelForProvider()
                }
                onSave(
                    AiSettings(
                        provider = provider,
                        apiKey = apiKey,
                        model = resolvedModel,
                        baseUrl = baseUrl.ifBlank { AiSettings.DEFAULT_OPENAI_BASE_URL }
                    )
                )
            }) { Text(stringResource(R.string.save)) }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text(stringResource(R.string.cancel)) }
        },
        title = { Text(stringResource(R.string.ai_settings_title)) },
        text = {
            Column {
                Text(
                    text = stringResource(R.string.ai_provider),
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Row(
                    modifier = Modifier.padding(vertical = 8.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    AiProvider.entries.forEach { p ->
                        FilterChip(
                            selected = p == provider,
                            onClick = {
                                provider = p
                                if (model.isBlank()) {
                                    model = current.copy(provider = p).defaultModelForProvider()
                                }
                            },
                            label = {
                                Text(if (p == AiProvider.GEMINI) "Gemini (free)" else "OpenAI-compatible")
                            }
                        )
                    }
                }
                OutlinedTextField(
                    value = apiKey,
                    onValueChange = { apiKey = it },
                    label = { Text(stringResource(R.string.ai_api_key)) },
                    singleLine = true,
                    visualTransformation = PasswordVisualTransformation(),
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = model,
                    onValueChange = { model = it },
                    label = { Text(stringResource(R.string.ai_model)) },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth().padding(top = 8.dp)
                )
                if (provider == AiProvider.OPENAI) {
                    OutlinedTextField(
                        value = baseUrl,
                        onValueChange = { baseUrl = it },
                        label = { Text(stringResource(R.string.ai_base_url)) },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth().padding(top = 8.dp)
                    )
                }
                Text(
                    text = stringResource(R.string.ai_settings_help),
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(top = 12.dp)
                )
            }
        }
    )
}

package com.ayed.visionai.lite

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.ayed.visionai.lite.ui.screen.CameraScreen
import com.ayed.visionai.lite.ui.screen.HistoryScreen
import com.ayed.visionai.lite.ui.theme.AyedVisionTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            AyedVisionTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    VisionNavGraph()
                }
            }
        }
    }
}

private object Routes {
    const val CAMERA = "camera"
    const val HISTORY = "history"
}

@androidx.compose.runtime.Composable
private fun VisionNavGraph() {
    val navController = rememberNavController()
    NavHost(navController = navController, startDestination = Routes.CAMERA) {
        composable(Routes.CAMERA) {
            CameraScreen(onOpenHistory = { navController.navigate(Routes.HISTORY) })
        }
        composable(Routes.HISTORY) {
            HistoryScreen(onBack = { navController.popBackStack() })
        }
    }
}

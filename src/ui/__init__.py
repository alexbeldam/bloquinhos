"""
UI module.

This module handles user interface rendering and interaction.
"""

from ui.assets import AssetLoader
from ui.audio import AudioManager
from ui.effects import (
    Effect,
    EffectManager,
    LevelUpNotification,
    LineClearFlash,
    ScreenShake,
    TetrisCombo,
    hsv_to_rgb,
)
from ui.renderer import GameRenderer
from ui.screen import Screen
from ui.screen_manager import ScreenManager
from ui.screen_factory import ScreenFactory
from ui.screens import (
    GameOverScreen,
    GameScreen,
    LoadingScreen,
    MenuScreen,
    PauseScreen,
    RankingScreen,
    SettingsScreen,
)
from ui.tabs import (
    AudioTab,
    ControlsTab,
    GraphicsTab,
    LocalizationTab,
    NetworkTab,
    SettingsTab,
    SettingsTabRegistry,
)

__all__ = [
    'AssetLoader',
    'AudioManager',
    'Effect',
    'EffectManager',
    'LevelUpNotification',
    'LineClearFlash',
    'ScreenShake',
    'TetrisCombo',
    'GameRenderer',
    'Screen',
    'ScreenManager',
    'ScreenFactory',
    'MenuScreen',
    'GameScreen',
    'GameOverScreen',
    'PauseScreen',
    'RankingScreen',
    'LoadingScreen',
    'SettingsScreen',
    'SettingsTab',
    'SettingsTabRegistry',
    'AudioTab',
    'ControlsTab',
    'GraphicsTab',
    'LocalizationTab',
    'NetworkTab',
]

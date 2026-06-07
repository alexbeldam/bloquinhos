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
    CreditsScreen,
    IdentityEntryScreen,
    GameOverScreen,
    GameScreen,
    LoadingScreen,
    MenuScreen,
    PauseScreen,
    RankingScreen,
    SettingsScreen,
)
from ui.styles import (
    CREDITS_STYLE,
    CreditsStyle,
    GAME_STYLE,
    GameStyle,
    SETTINGS_STYLE,
    SettingsStyle,
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
from ui.transitions import (
    Direction,
    FadeTransition,
    SlideTransition,
    TransitionEffect,
    determine_transition,
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
    'hsv_to_rgb',
    'GameRenderer',
    'Screen',
    'ScreenManager',
    'ScreenFactory',
    'CreditsScreen',
    'IdentityEntryScreen',
    'MenuScreen',
    'GameScreen',
    'GameOverScreen',
    'PauseScreen',
    'RankingScreen',
    'LoadingScreen',
    'SettingsScreen',
    'CREDITS_STYLE',
    'CreditsStyle',
    'GAME_STYLE',
    'GameStyle',
    'SETTINGS_STYLE',
    'SettingsStyle',
    'SettingsTab',
    'SettingsTabRegistry',
    'AudioTab',
    'ControlsTab',
    'GraphicsTab',
    'LocalizationTab',
    'NetworkTab',
    'TransitionEffect',
    'FadeTransition',
    'SlideTransition',
    'Direction',
    'determine_transition',
]

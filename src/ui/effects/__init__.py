"""
Effects package for visual feedback during gameplay.

Provides screen shake, line clear flash, level-up notification,
and tetris combo particle effects.
"""

from ui.effects.base import Effect
from ui.effects.color import hsv_to_rgb
from ui.effects.line_clear_flash import LineClearFlash
from ui.effects.level_up_notification import LevelUpNotification
from ui.effects.manager import EffectManager
from ui.effects.screen_shake import ScreenShake
from ui.effects.tetris_combo import TetrisCombo

__all__ = [
    "Effect",
    "EffectManager",
    "LineClearFlash",
    "LevelUpNotification",
    "ScreenShake",
    "TetrisCombo",
    "hsv_to_rgb",
]
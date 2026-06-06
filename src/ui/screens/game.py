from typing import List, Optional, TYPE_CHECKING
import random

import pygame

from engine import GameController, GameSession, GameState
from settings import SETTINGS
from ui.assets import AssetManager
from ui.effects import (
    EffectManager,
    LevelUpNotification,
    LineClearFlash,
    ScreenShake,
    TetrisCombo,
)
from ui.renderer import GameRenderer
from ui.screen import Screen

if TYPE_CHECKING:
    from ui.audio import AudioManager
    from utils.settings_manager import SettingsManager


class GameScreen(Screen):
    def __init__(
        self,
        game_controller: GameController,
        session: GameSession,
        assets: Optional[AssetManager] = None,
        audio_manager: Optional["AudioManager"] = None,
        settings_manager: Optional["SettingsManager"] = None,
    ) -> None:
        super().__init__(assets, audio_manager)
        self.game_controller = game_controller
        self.session = session
        self.renderer: Optional[GameRenderer] = None
        self.settings_manager = settings_manager
        self.ingame_tracks = self._build_ingame_playlist()
        self.current_track = random.choice(self.ingame_tracks) if self.ingame_tracks else "score1"
        
        if self.audio_manager:
            self.audio_manager.register_events(self.game_controller)
    
    def _build_ingame_playlist(self) -> list:
        base_tracks = ["score1", "score2", "score3", "score4"]
        return base_tracks
    
    def _get_effect_manager(self) -> EffectManager:
        if self.renderer is not None:
            return self.renderer.effect_manager
        return EffectManager()

    def _register_effect_events(self) -> None:
        def on_line_clear(lines: int) -> None:
            if not self._effects_enabled():
                return
            full_rows = list(self.game_controller.last_cleared_rows)
            if full_rows:
                self._get_effect_manager().add_effect(LineClearFlash(full_rows))
            if lines >= 4:
                self._get_effect_manager().add_effect(TetrisCombo())
        
        def on_level_up(new_level: int) -> None:
            if self.audio_manager:
                self.audio_manager.play_sfx("levelup")
            if not self._effects_enabled():
                return
            self._get_effect_manager().add_effect(LevelUpNotification(new_level))
        
        def on_hard_drop() -> None:
            if not self._effects_enabled():
                return
            self._get_effect_manager().add_effect(ScreenShake())
        
        self.game_controller.on_line_clear(on_line_clear)
        self.session.on_level_up(on_level_up)
        self.game_controller.on_hard_drop(on_hard_drop)
    
    def _effects_enabled(self) -> bool:
        if self.settings_manager is None:
            return True
        try:
            return self.settings_manager.get_bool("graphics.animations")
        except (KeyError, TypeError, ValueError):
            return True

    def handle_events(self, events: List[pygame.event.Event]) -> Optional[str]:
        controls = self._get_controls()
        pause_key = controls["pause"]
        left_key = controls["left"]
        right_key = controls["right"]
        soft_drop_key = controls["soft_drop"]
        rotate_key = controls["rotate"]
        hard_drop_key = controls["hard_drop"]
        hold_key = controls["hold"]

        for event in events:
            if event.type == pygame.QUIT:
                return SETTINGS.SCREEN_NAMES.QUIT
            if event.type != pygame.KEYDOWN:
                continue
            
            if event.key == pause_key:
                self.session.pause()
                return SETTINGS.SCREEN_NAMES.PAUSE
            if self.session.state != GameState.RUNNING:
                continue
            if event.key == left_key:
                self.game_controller.move_left()
                if self.audio_manager:
                    self.audio_manager.play_sfx("position")
            elif event.key == right_key:
                self.game_controller.move_right()
                if self.audio_manager:
                    self.audio_manager.play_sfx("position")
            elif event.key == soft_drop_key:
                self.game_controller.move_down()
                if self.audio_manager:
                    self.audio_manager.play_sfx("position")
            elif event.key == rotate_key:
                self.game_controller.rotate()
                if self.audio_manager:
                    self.audio_manager.play_sfx("rotate")
            elif event.key == hard_drop_key:
                self.game_controller.hard_drop()
            elif event.key == hold_key:
                self.game_controller.hold_piece()
                if self.audio_manager:
                    self.audio_manager.play_sfx("hold")
        return None

    def on_enter(self) -> None:
        if not self.audio_manager:
            return

        if self.audio_manager.current_bgm not in self.ingame_tracks:
            self.current_track = random.choice(self.ingame_tracks)
        else:
            self.current_track = self.audio_manager.current_bgm

        self.audio_manager.play_bgm(self.current_track)

    def update(self, delta_time: float) -> Optional[str]:
        if self.session.state == GameState.GAME_OVER:
            return SETTINGS.SCREEN_NAMES.GAME_OVER
        
        if self.session.state == GameState.RUNNING:
            self.game_controller.update(delta_time)
        
        if self.renderer is not None:
            self.renderer.effect_manager.update(delta_time)
        
        return None

    def render(self, surface: pygame.Surface) -> None:
        if self.renderer is None:
            self.renderer = GameRenderer(
                surface,
                self.assets,
                self.game_controller,
                self.session,
                self.settings_manager,
            )
            self._register_effect_events()
        else:
            self.renderer.screen = surface

        self.renderer.render()

    def _get_controls(self) -> dict[str, int]:
        defaults = {
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
            "soft_drop": pygame.K_DOWN,
            "rotate": pygame.K_UP,
            "hard_drop": pygame.K_SPACE,
            "hold": pygame.K_c,
            "pause": pygame.K_ESCAPE,
        }

        if self.settings_manager is None:
            return defaults

        controls = self.settings_manager.get("controls")
        if not isinstance(controls, dict):
            return defaults

        resolved = defaults.copy()
        for key, default_value in defaults.items():
            value = controls.get(key)
            if isinstance(value, int):
                resolved[key] = value
            else:
                resolved[key] = default_value

        return resolved

from typing import List, Optional, TYPE_CHECKING
import random

import pygame

from engine import GameController, GameSession, GameState, GravityController
from settings import SETTINGS
from ui.assets import AssetManager
from ui.renderer import GameRenderer
from ui.screen import Screen

if TYPE_CHECKING:
    from ui.audio import AudioManager
    from utils.settings_manager import SettingsManager


class GameScreen(Screen):
    SANS_GRAVITY_INTERVAL = 0.08
    SANS_SHAKE_PIXELS = 5

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
        self._shake_canvas: Optional[pygame.Surface] = None
        self.settings_manager = settings_manager
        self.sans_mode = False
        
        self.ingame_tracks = ["score1", "score2", "score3"]
        self.current_track = random.choice(self.ingame_tracks)
        
        if self.audio_manager:
            self.audio_manager.register_events(self.game_controller)

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
        return None

    def update(self, delta_time: float) -> Optional[str]:
        if self.session.state == GameState.GAME_OVER:
            return SETTINGS.SCREEN_NAMES.GAME_OVER
        
        if self.session.state == GameState.RUNNING:
            if self.audio_manager:
                if self.sans_mode:
                    self.current_track = "megalovania"
                elif self.audio_manager.current_bgm not in self.ingame_tracks:
                    self.current_track = random.choice(self.ingame_tracks)
                self.audio_manager.play_bgm(self.current_track)
            if self.sans_mode:
                self.game_controller.gravity_interval = self.SANS_GRAVITY_INTERVAL
            self.game_controller.update(delta_time)
        
        return None

    def render(self, surface: pygame.Surface) -> None:
        target_surface = self._get_render_surface(surface)

        if self.renderer is None:
            self.renderer = GameRenderer(
                target_surface,
                self.assets,
                self.game_controller,
                self.session,
                self.settings_manager,
                sans_mode=self.sans_mode,
            )
        else:
            self.renderer.screen = target_surface
            self.renderer.sans_mode = self.sans_mode

        self.renderer.render()
        if self.sans_mode:
            self._blit_shaken(surface, target_surface)

    def set_sans_mode(self, enabled: bool) -> None:
        self.sans_mode = enabled
        if enabled:
            self.current_track = "megalovania"
            self.game_controller.gravity_interval = self.SANS_GRAVITY_INTERVAL
        elif self.current_track == "megalovania":
            self.current_track = random.choice(self.ingame_tracks)
            self.game_controller.gravity_interval = GravityController.calculate_gravity_interval(self.session.level)
        if self.renderer is not None:
            self.renderer.sans_mode = enabled

    def _get_render_surface(self, surface: pygame.Surface) -> pygame.Surface:
        if not self.sans_mode:
            return surface

        if self._shake_canvas is None or self._shake_canvas.get_size() != surface.get_size():
            self._shake_canvas = pygame.Surface(surface.get_size()).convert()

        return self._shake_canvas

    def _blit_shaken(self, surface: pygame.Surface, target_surface: pygame.Surface) -> None:
        surface.fill((10, 14, 22))
        offset = (
            random.randint(-self.SANS_SHAKE_PIXELS, self.SANS_SHAKE_PIXELS),
            random.randint(-self.SANS_SHAKE_PIXELS, self.SANS_SHAKE_PIXELS),
        )
        surface.blit(target_surface, offset)

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

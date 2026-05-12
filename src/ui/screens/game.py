from typing import List, Optional

import pygame

from engine import GameController, GameSession, GameState
from settings import SETTINGS
from ui.assets import AssetManager
from ui.renderer import GameRenderer
from ui.screen import Screen


class GameScreen(Screen):
    def __init__(
        self,
        game_controller: GameController,
        session: GameSession,
        assets: Optional[AssetManager] = None,
    ) -> None:
        super().__init__(assets)
        self.game_controller = game_controller
        self.session = session
        self.renderer: Optional[GameRenderer] = None

    def handle_events(self, events: List[pygame.event.Event]) -> Optional[str]:
        for event in events:
            if event.type == pygame.QUIT:
                return SETTINGS.SCREEN_NAMES.QUIT
            if event.type != pygame.KEYDOWN:
                continue
            
            if event.key == pygame.K_ESCAPE:
                self.session.pause()
                return SETTINGS.SCREEN_NAMES.PAUSE
            if self.session.state != GameState.RUNNING:
                continue
            if event.key == pygame.K_LEFT:
                self.game_controller.move_left()
            elif event.key == pygame.K_RIGHT:
                self.game_controller.move_right()
            elif event.key == pygame.K_DOWN:
                self.game_controller.move_down()
            elif event.key == pygame.K_UP:
                self.game_controller.rotate()
            elif event.key == pygame.K_SPACE:
                self.game_controller.hard_drop()
        return None

    def update(self, delta_time: float) -> Optional[str]:
        if self.session.state == GameState.GAME_OVER:
            return SETTINGS.SCREEN_NAMES.GAME_OVER
        
        if self.session.state == GameState.RUNNING:
            self.game_controller.update(delta_time)
        
        return None

    def render(self, surface: pygame.Surface) -> None:
        if self.renderer is None:
            self.renderer = GameRenderer(
                surface,
                self.assets,
                self.game_controller,
                self.session,
            )

        self.renderer.render()

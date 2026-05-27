from typing import Callable, List, Optional, Sequence, Tuple, TYPE_CHECKING

import pygame

from network import DataSynchronizer
from network.user_data_dao import UserDataDAO
from settings import SETTINGS
from ui.assets import AssetManager
from ui.components import Menu
from ui.screen import Screen
from ui.screens.game import GameScreen
from utils.logger import log

if TYPE_CHECKING:
    from ui.audio import AudioManager


class GameOverScreen(Screen):
    OPTIONS: Sequence[Tuple[str, str]] = (
        ("Jogar Novamente", SETTINGS.SCREEN_NAMES.GAME),
        ("Voltar ao Menu", SETTINGS.SCREEN_NAMES.MENU),
    )

    def __init__(
        self,
        game_screen: GameScreen,
        synchronizer: Optional[DataSynchronizer] = None,
        assets: Optional[AssetManager] = None,
        audio_manager: Optional["AudioManager"] = None,
    ) -> None:
        super().__init__(assets, audio_manager)
        self.game_screen = game_screen
        self.user_data_dao = UserDataDAO()
        self._synchronizer = synchronizer
        self._save_attempted = False
        self.menu = Menu(
            options=self.OPTIONS,
            font_renderer=self._font,
            item_spacing=50,
        )

    def handle_events(self, events: List[pygame.event.Event]) -> Optional[str]:
        for event in events:
            if event.type == pygame.QUIT:
                return SETTINGS.SCREEN_NAMES.QUIT
            
            result = self.menu.handle_navigation(event)
            if result is not None:
                self.game_screen.session.reset()
                self._save_attempted = False
                self.menu.reset_selection()
                return result
        
        return None

    def update(self, delta_time: float) -> Optional[str]:
        if not self._save_attempted:
            self._save_attempted = True
            try:
                name = self.user_data_dao.load_name()
                if name:
                    self.user_data_dao.save(self.game_screen.session, name)
                    self._trigger_sync(name)
            except Exception:
                log.error("Failed to save game over user data", exc_info=True)
        return None

    def _trigger_sync(self, name: str) -> None:
        if self._synchronizer is None:
            return
        try:
            result = self._synchronizer.sync(name)
            log.info("Sync result: %s — %s", result.status.name, result.message)
        except Exception:
            log.error("Sync after game over failed", exc_info=True)

    def render(self, surface: pygame.Surface) -> None:
        self.game_screen.render(surface)
        
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))
        
        center_x = surface.get_width() // 2
        center_y = surface.get_height() // 2
        
        self._draw_text(
            surface,
            "GAME OVER",
            SETTINGS.UI_TYPOGRAPHY.DISPLAY,
            SETTINGS.UI_THEME.RED,
            (center_x, center_y - 60),
        )
        
        self.menu.render(surface, center_x, center_y + 20, self._draw_text)

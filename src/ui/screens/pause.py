from typing import List, Optional, Sequence, Tuple, TYPE_CHECKING

import pygame

from settings import SETTINGS
from ui.assets import AssetManager
from ui.components import Menu
from ui.screen import Screen
from ui.screens.game import GameScreen

if TYPE_CHECKING:
    from ui.audio import AudioManager


class PauseScreen(Screen):
    OPTIONS: Sequence[Tuple[str, str]] = (
        ("Continuar", "__resume__"),
        ("Configurações", SETTINGS.SCREEN_NAMES.SETTINGS),
        ("Menu Principal", SETTINGS.SCREEN_NAMES.MENU),
    )

    def __init__(
        self,
        game_screen: GameScreen,
        assets: Optional[AssetManager] = None,
        audio_manager: Optional["AudioManager"] = None,
    ) -> None:
        super().__init__(assets, audio_manager)
        self.game_screen = game_screen
        self.menu = Menu(
            options=self.OPTIONS,
            font_renderer=self._font,
            selected_color=SETTINGS.UI_THEME.YELLOW,
            unselected_color=SETTINGS.UI_THEME.TEXT_PRIMARY,
            font_size=SETTINGS.UI_TYPOGRAPHY.BODY,
            item_spacing=40,
        )

    def handle_events(self, events: List[pygame.event.Event]) -> Optional[str]:
        for event in events:
            if event.type == pygame.QUIT:
                return SETTINGS.SCREEN_NAMES.QUIT

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game_screen.session.resume()
                return SETTINGS.SCREEN_NAMES.GAME

            result = self.menu.handle_navigation(event)
            if result == "__resume__":
                self.game_screen.session.resume()
                return SETTINGS.SCREEN_NAMES.GAME
            elif result == SETTINGS.SCREEN_NAMES.MENU:
                if self.game_screen.audio_manager:
                    self.game_screen.audio_manager.stop_bgm()
                self.game_screen.session.reset()
                return SETTINGS.SCREEN_NAMES.MENU
            elif result:
                return result

        return None

    def update(self, delta_time: float) -> Optional[str]:
        return None

    def render(self, surface: pygame.Surface) -> None:
        self.game_screen.render(surface)
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        center_x = surface.get_width() // 2
        center_y = surface.get_height() // 2

        self._draw_text(
            surface,
            "PAUSE",
            SETTINGS.UI_TYPOGRAPHY.DISPLAY,
            SETTINGS.UI_THEME.TEXT_PRIMARY,
            (center_x, center_y - 100),
        )

        menu_start_y = center_y - 20
        self.menu.render(surface, center_x, menu_start_y, self._draw_text)

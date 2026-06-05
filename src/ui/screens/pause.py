from typing import List, Optional, Sequence, Tuple, TYPE_CHECKING

import pygame

from settings import SETTINGS
from ui.assets import AssetManager
from ui.components import Menu
from ui.screen import Screen
from ui.screens.game import GameScreen
from utils.localization import tr

if TYPE_CHECKING:
    from ui.audio import AudioManager


class PauseScreen(Screen):
    OPTION_TARGETS: Sequence[str] = (
        "__resume__",
        SETTINGS.SCREEN_NAMES.SETTINGS,
        SETTINGS.SCREEN_NAMES.MENU,
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
            options=self._build_options(),
            font_renderer=self._font,
            selected_color=SETTINGS.UI_THEME.YELLOW,
            unselected_color=SETTINGS.UI_THEME.TEXT_PRIMARY,
            font_size=SETTINGS.UI_TYPOGRAPHY.BODY,
            item_spacing=40,
            on_navigate=self._on_menu_navigate,
            on_select=self._on_menu_select,
        )

    def _build_options(self) -> Sequence[Tuple[str, str]]:
        labels = (
            tr("pause.resume"),
            tr("pause.settings"),
            tr("pause.main_menu"),
        )
        return tuple(zip(labels, self.OPTION_TARGETS, strict=False))

    def _sync_menu_options(self) -> None:
        self.menu.options = self._build_options()

    def _on_menu_navigate(self) -> None:
        """Triggered when menu selection changes."""
        if self.audio_manager:
            self.audio_manager.play_sfx("nav")

    def _on_menu_select(self) -> None:
        """Triggered when menu item is selected."""
        if self.audio_manager:
            self.audio_manager.play_sfx("select")

    def handle_events(self, events: List[pygame.event.Event]) -> Optional[str]:
        self._sync_menu_options()
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
                self.game_screen.session.reset()
                return SETTINGS.SCREEN_NAMES.MENU
            elif result:
                return result

        return None

    def update(self, _delta_time: float) -> Optional[str]:
        return None

    def on_enter(self) -> None:
        """Called when entering pause screen."""
        if self.audio_manager:
            self.audio_manager.play_sfx("open")

    def on_exit(self) -> None:
        """Called when leaving pause screen."""
        pass

    def render(self, surface: pygame.Surface) -> None:
        self.game_screen.render(surface)
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        center_x = surface.get_width() // 2
        center_y = surface.get_height() // 2

        self._draw_text(
            surface,
            tr("pause.title"),
            SETTINGS.UI_TYPOGRAPHY.DISPLAY,
            SETTINGS.UI_THEME.TEXT_PRIMARY,
            (center_x, center_y - 100),
        )

        menu_start_y = center_y - 20
        self.menu.render(surface, center_x, menu_start_y, self._draw_text)

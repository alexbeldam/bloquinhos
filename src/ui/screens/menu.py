from typing import List, Optional, Sequence, Tuple, TYPE_CHECKING

import pygame

from settings import SETTINGS
from ui.assets import AssetManager
from ui.components import Menu
from ui.screen import Screen
from utils.localization import tr

if TYPE_CHECKING:
    from ui.audio import AudioManager


class MenuScreen(Screen):
    OPTION_TARGETS: Sequence[str] = (
        SETTINGS.SCREEN_NAMES.GAME,
        SETTINGS.SCREEN_NAMES.RANKING,
        SETTINGS.SCREEN_NAMES.SETTINGS,
        SETTINGS.SCREEN_NAMES.QUIT,
    )

    def __init__(self, assets: Optional[AssetManager] = None, audio_manager: Optional["AudioManager"] = None) -> None:
        super().__init__(assets, audio_manager)
        self.menu = Menu(
            options=self._build_options(),
            font_renderer=self._font,
            selected_color=SETTINGS.UI_THEME.YELLOW,
            unselected_color=SETTINGS.UI_THEME.PURPLE,
            font_size=SETTINGS.UI_TYPOGRAPHY.TITLE,
            on_navigate=self._on_menu_navigate,
            on_select=self._on_menu_select,
        )

    def _build_options(self) -> Sequence[Tuple[str, str]]:
        labels = (
            tr("menu.play"),
            tr("menu.ranking"),
            tr("menu.settings"),
            tr("menu.quit"),
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

            if self._handle_network_status_event(event):
                continue
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return SETTINGS.SCREEN_NAMES.QUIT
            
            result = self.menu.handle_navigation(event)
            if result is not None:
                return result
        
        return None

    def on_enter(self) -> None:
        if self.audio_manager:
            self.audio_manager.play_bgm("menu")

    def on_exit(self) -> None:
        """Called when leaving the menu screen."""
        pass

    def update(self, _delta_time: float) -> Optional[str]:
        return None

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(SETTINGS.UI_THEME.BG_DARK)
        center_x = surface.get_width() // 2
        center_y = surface.get_height() // 2
        
        logo = self._try_load_image("logo")
        logo_height = 0
        if logo:
            scale_factor = 0.35
            scaled_width = int(logo.get_width() * scale_factor)
            scaled_height = int(logo.get_height() * scale_factor)
            logo_height = scaled_height
        
        title_font = self._font(SETTINGS.UI_TYPOGRAPHY.TITLE)
        title_height = title_font.get_height()
        
        menu_item_spacing = 50
        menu_height = len(self.menu.options) * menu_item_spacing
        
        total_height = logo_height + 30 + title_height + 60 + menu_height
        start_y = center_y - total_height // 2
        
        current_y = start_y
        if logo:
            scaled_logo = pygame.transform.scale(logo, (int(logo.get_width() * 0.35), logo_height))
            logo_rect = scaled_logo.get_rect(center=(center_x, current_y + logo_height // 2))
            surface.blit(scaled_logo, logo_rect)
            current_y += logo_height + 30
        
        self._draw_text(
            surface,
            self._localized_app_name(),
            SETTINGS.UI_TYPOGRAPHY.TITLE,
            SETTINGS.UI_THEME.TEXT_PRIMARY,
            (center_x, current_y),
        )
        current_y += title_height + 60
        
        self.menu.render(surface, center_x, current_y, self._draw_text)
        self._render_network_status(surface)

    @staticmethod
    def _localized_app_name() -> str:
        localized = tr("app.name")
        if not localized or localized == "app.name":
            return SETTINGS.APP_NAME
        return localized

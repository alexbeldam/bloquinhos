from typing import Optional, TYPE_CHECKING

import pygame

from settings import SETTINGS
from ui.components import (
    bottom_action_y,
    draw_option_row,
    draw_row_icon_right,
    draw_tab_background_and_title,
)
from ui.tabs.settings_tab import SettingsTab

if TYPE_CHECKING:
    from ui.assets import AssetManager
    from utils.settings_manager import SettingsManager


class GraphicsTab(SettingsTab):
    CONTENT_PADDING = 30
    OPTION_ROW_HEIGHT = 44
    OPTION_ROW_GAP = 8

    OPTIONS = [
        ("Draw Grid", "graphics.draw_grid"),
        ("Draw Ghost", "graphics.draw_ghost"),
        ("Animations", "graphics.animations"),
    ]

    def __init__(self) -> None:
        super().__init__(
            id="graphics",
            title="Graphics",
            icon_name="video",
            order=20,
            category="graphics",
        )
        self._option_hitboxes: list[tuple[str, pygame.Rect]] = []
        self.hovered_option_path: Optional[str] = None

    def render(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        assets: Optional["AssetManager"],
        settings_manager: Optional["SettingsManager"],
    ) -> None:
        self._option_hitboxes = []

        _, _, options_start_y = draw_tab_background_and_title(
            surface,
            rect,
            self.title,
            assets,
            self.CONTENT_PADDING,
        )
        row_x = rect.x + self.CONTENT_PADDING
        row_width = rect.width - self.CONTENT_PADDING * 2
        row_font = self._font(SETTINGS.UI_TYPOGRAPHY.BODY, assets)

        checkbox_checked = self._try_load_icon("checkbox-marked", assets)
        checkbox_empty = self._try_load_icon("checkbox-blank", assets)

        for index, (label, path) in enumerate(self.OPTIONS):
            row_y = options_start_y + index * (self.OPTION_ROW_HEIGHT + self.OPTION_ROW_GAP)
            row_rect = pygame.Rect(row_x, row_y, row_width, self.OPTION_ROW_HEIGHT)
            self._option_hitboxes.append((path, row_rect))

            is_hovered = path == self.hovered_option_path
            draw_option_row(surface, row_rect, label, row_font, is_hovered=is_hovered)

            checked = False
            if settings_manager is not None:
                try:
                    checked = settings_manager.get_bool(path)
                except (KeyError, TypeError, ValueError):
                    checked = False

            icon = checkbox_checked if checked else checkbox_empty
            draw_row_icon_right(surface, row_rect, icon)
        
        reset_button_y = bottom_action_y(rect, self.CONTENT_PADDING, action_height=42)
        self.render_reset_button(surface, rect, assets, reset_button_y)

    def handle_click(
        self,
        pos: tuple[int, int],
        settings_manager: Optional["SettingsManager"],
    ) -> None:
        if settings_manager is None:
            return

        for path, rect in self._option_hitboxes:
            if rect.collidepoint(pos):
                try:
                    current = settings_manager.get_bool(path)
                    settings_manager.set(path, not current)
                except (KeyError, TypeError, ValueError):
                    pass
                return

    def handle_mouse_motion(self, pos: tuple[int, int]) -> None:
        self.hovered_option_path = None
        for path, rect in self._option_hitboxes:
            if rect.collidepoint(pos):
                self.hovered_option_path = path
                return

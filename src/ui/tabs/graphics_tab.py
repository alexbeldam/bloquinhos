from typing import Optional

import pygame

from settings import SETTINGS
from ui.tabs.settings_tab import SettingsTab


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
    ) -> None:
        self._option_hitboxes = []

        _, _, options_start_y = self._draw_tab_background_and_title(
            surface,
            rect,
            self.title,
            self.CONTENT_PADDING,
        )
        row_x = rect.x + self.CONTENT_PADDING
        row_width = rect.width - self.CONTENT_PADDING * 2
        row_font = self._font(SETTINGS.UI_TYPOGRAPHY.BODY)

        checkbox_checked = self._try_load_icon("checkbox-marked")
        checkbox_empty = self._try_load_icon("checkbox-blank")

        for index, (label, path) in enumerate(self.OPTIONS):
            row_y = options_start_y + index * (self.OPTION_ROW_HEIGHT + self.OPTION_ROW_GAP)
            row_rect = pygame.Rect(row_x, row_y, row_width, self.OPTION_ROW_HEIGHT)
            self._option_hitboxes.append((path, row_rect))

            is_hovered = path == self.hovered_option_path
            self._draw_option_row(
                surface,
                row_rect,
                label,
                row_font,
                text_size=SETTINGS.UI_TYPOGRAPHY.BODY,
                is_hovered=is_hovered,
            )

            checked = False
            if self.settings_manager is not None:
                try:
                    checked = self.settings_manager.get_bool(path)
                except (KeyError, TypeError, ValueError):
                    checked = False

            icon = checkbox_checked if checked else checkbox_empty
            self._draw_row_icon_right(surface, row_rect, icon)
        
        reset_button_y = self._bottom_action_y(rect, self.CONTENT_PADDING, action_height=42)
        self.render_reset_button(surface, rect, reset_button_y)

    def handle_click(
        self,
        pos: tuple[int, int],
    ) -> None:
        if self.settings_manager is None:
            return

        for path, rect in self._option_hitboxes:
            if rect.collidepoint(pos):
                try:
                    current = self.settings_manager.get_bool(path)
                    self.settings_manager.set(path, not current)
                except (KeyError, TypeError, ValueError):
                    pass
                return

    def handle_mouse_motion(self, pos: tuple[int, int]) -> None:
        self.hovered_option_path = None
        for path, rect in self._option_hitboxes:
            if rect.collidepoint(pos):
                self.hovered_option_path = path
                return

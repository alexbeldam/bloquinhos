from typing import Optional

import pygame

from settings import SETTINGS
from ui.styles import SETTINGS_STYLE
from ui.tabs.settings_tab import SettingsTab
from utils.localization import get_available_locales, get_locale


class LocalizationTab(SettingsTab):
    CONTENT_PADDING = 30
    OPTION_ROW_HEIGHT = 44
    OPTION_ROW_GAP = 8

    def __init__(self) -> None:
        super().__init__(
            id="localization",
            icon_name="language",
            order=100,
            category="localization",
            title_key="settings.tabs.localization",
        )
        self._option_hitboxes: list[tuple[str, pygame.Rect]] = []
        self.hovered_option: Optional[str] = None

    def render(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
    ) -> None:
        self._option_hitboxes = []

        _, content_center_x, options_start_y = self._draw_tab_background_and_title(
            surface,
            rect,
            self.get_title(),
            self.CONTENT_PADDING,
        )

        current_locale = get_locale()

        row_x = rect.x + self.CONTENT_PADDING
        row_width = rect.width - self.CONTENT_PADDING * 2
        row_font = self._font(SETTINGS.UI_TYPOGRAPHY.BODY)

        radio_checked = self._try_load_icon("radiobox-marked")
        radio_empty = self._try_load_icon("radiobox-blank")

        available_locales = get_available_locales()
        for index, (locale_code, locale_meta) in enumerate(available_locales):
            row_y = options_start_y + index * (self.OPTION_ROW_HEIGHT + self.OPTION_ROW_GAP)
            row_rect = pygame.Rect(row_x, row_y, row_width, self.OPTION_ROW_HEIGHT)
            self._option_hitboxes.append((locale_code, row_rect))

            is_selected = locale_code == current_locale
            is_hovered = self.hovered_option == locale_code
            
            self._draw_option_row(
                surface,
                row_rect,
                locale_meta.display_name,
                row_font,
                text_size=SETTINGS.UI_TYPOGRAPHY.BODY,
                is_hovered=is_hovered,
                is_selected=is_selected,
                selected_bg=SETTINGS_STYLE.ROW_BG_SELECTED,
            )

            icon = radio_checked if is_selected else radio_empty
            self._draw_row_icon_right(surface, row_rect, icon)

        reset_button_y = self._bottom_action_y(
            rect,
            self.CONTENT_PADDING,
            action_height=42,
        )
        self.render_reset_button(surface, rect, reset_button_y)

    def handle_click(
        self,
        pos: tuple[int, int],
    ) -> None:
        if self.settings_manager is None:
            return

        for locale_code, rect in self._option_hitboxes:
            if rect.collidepoint(pos):
                try:
                    self.settings_manager.set("localization.locale", locale_code)
                except (KeyError, TypeError, ValueError):
                    pass
                return

    def handle_mouse_motion(self, pos: tuple[int, int]) -> None:
        self.hovered_option = None
        for codes, rect in self._option_hitboxes:
            if rect.collidepoint(pos):
                self.hovered_option = codes
                return

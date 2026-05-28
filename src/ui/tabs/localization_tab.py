from typing import Optional

import pygame

from settings import SETTINGS
from ui.styles import SETTINGS_STYLE
from ui.tabs.settings_tab import SettingsTab


class LocalizationTab(SettingsTab):
    CONTENT_PADDING = 30
    OPTION_ROW_HEIGHT = 44
    OPTION_ROW_GAP = 8
    FOOTER_RESERVED_SPACE = 50

    LANGUAGES = [
        ("English", "en", "US"),
        ("Português", "pt", "BR"),
    ]

    def __init__(self) -> None:
        super().__init__(
            id="localization",
            title="Language",
            icon_name="language",
            order=100,
            category="localization",
        )
        self._option_hitboxes: list[tuple[tuple[str, str], pygame.Rect]] = []
        self.hovered_option: Optional[tuple[str, str]] = None

    def render(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
    ) -> None:
        self._option_hitboxes = []

        _, content_center_x, options_start_y = self._draw_tab_background_and_title(
            surface,
            rect,
            self.title,
            self.CONTENT_PADDING,
        )

        current_language = "en"
        current_region = "US"
        if self.settings_manager is not None:
            try:
                current_language = self.settings_manager.get("localization.language")
            except (KeyError, TypeError, ValueError):
                pass
            try:
                current_region = self.settings_manager.get("localization.region")
            except (KeyError, TypeError, ValueError):
                pass

        row_x = rect.x + self.CONTENT_PADDING
        row_width = rect.width - self.CONTENT_PADDING * 2
        row_font = self._font(SETTINGS.UI_TYPOGRAPHY.BODY)

        radio_checked = self._try_load_icon("radiobox-marked")
        radio_empty = self._try_load_icon("radiobox-blank")

        for index, (label, lang_code, region_code) in enumerate(self.LANGUAGES):
            row_y = options_start_y + index * (self.OPTION_ROW_HEIGHT + self.OPTION_ROW_GAP)
            row_rect = pygame.Rect(row_x, row_y, row_width, self.OPTION_ROW_HEIGHT)
            self._option_hitboxes.append(((lang_code, region_code), row_rect))

            is_selected = (lang_code == current_language and region_code == current_region)
            is_hovered = self.hovered_option == (lang_code, region_code)
            
            self._draw_option_row(
                surface,
                row_rect,
                label,
                row_font,
                text_size=SETTINGS.UI_TYPOGRAPHY.BODY,
                is_hovered=is_hovered,
                is_selected=is_selected,
                selected_bg=SETTINGS_STYLE.ROW_BG_SELECTED,
            )

            icon = radio_checked if is_selected else radio_empty
            self._draw_row_icon_right(surface, row_rect, icon)

        disclaimer_y = rect.y + rect.height - self.CONTENT_PADDING - 8
        self._draw_wrapped_text(
            surface,
            "Language preference is saved now and applied in upcoming localization updates",
            SETTINGS.UI_TYPOGRAPHY.SMALL,
            SETTINGS.UI_THEME.TEXT_MUTED,
            row_width,
            line_spacing=2,
            x=content_center_x,
            y=disclaimer_y,
            align="center",
        )
        
        reset_button_y = self._bottom_action_y(
            rect,
            self.CONTENT_PADDING,
            action_height=42,
            reserve_space=self.FOOTER_RESERVED_SPACE,
        )
        self.render_reset_button(surface, rect, reset_button_y)

    def handle_click(
        self,
        pos: tuple[int, int],
    ) -> None:
        if self.settings_manager is None:
            return

        for (lang_code, region_code), rect in self._option_hitboxes:
            if rect.collidepoint(pos):
                try:
                    self.settings_manager.set("localization.language", lang_code)
                    self.settings_manager.set("localization.region", region_code)
                except (KeyError, TypeError, ValueError):
                    pass
                return

    def handle_mouse_motion(self, pos: tuple[int, int]) -> None:
        self.hovered_option = None
        for codes, rect in self._option_hitboxes:
            if rect.collidepoint(pos):
                self.hovered_option = codes
                return

from typing import Optional, TYPE_CHECKING

import pygame

from settings import SETTINGS
from ui.components import (
    bottom_action_y,
    draw_option_row,
    draw_row_icon_right,
    draw_tab_background_and_title,
    draw_wrapped_text,
)
from ui.tabs.settings_tab import SettingsTab

if TYPE_CHECKING:
    from ui.assets import AssetManager
    from utils.settings_manager import SettingsManager


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
        assets: Optional["AssetManager"],
        settings_manager: Optional["SettingsManager"],
    ) -> None:
        self._option_hitboxes = []

        _, content_center_x, options_start_y = draw_tab_background_and_title(
            surface,
            rect,
            self.title,
            assets,
            self.CONTENT_PADDING,
        )

        current_language = "en"
        current_region = "US"
        if settings_manager is not None:
            try:
                current_language = settings_manager.get("localization.language")
            except (KeyError, TypeError, ValueError):
                pass
            try:
                current_region = settings_manager.get("localization.region")
            except (KeyError, TypeError, ValueError):
                pass

        row_x = rect.x + self.CONTENT_PADDING
        row_width = rect.width - self.CONTENT_PADDING * 2
        row_font = self._font(SETTINGS.UI_TYPOGRAPHY.BODY, assets)

        radio_checked = self._try_load_icon("radiobox-marked", assets)
        radio_empty = self._try_load_icon("radiobox-blank", assets)

        for index, (label, lang_code, region_code) in enumerate(self.LANGUAGES):
            row_y = options_start_y + index * (self.OPTION_ROW_HEIGHT + self.OPTION_ROW_GAP)
            row_rect = pygame.Rect(row_x, row_y, row_width, self.OPTION_ROW_HEIGHT)
            self._option_hitboxes.append(((lang_code, region_code), row_rect))

            is_selected = (lang_code == current_language and region_code == current_region)
            is_hovered = self.hovered_option == (lang_code, region_code)
            
            draw_option_row(
                surface,
                row_rect,
                label,
                row_font,
                is_hovered=is_hovered,
                is_selected=is_selected,
                selected_bg=SETTINGS.UI_THEME.SETTINGS_ROW_BG_SELECTED,
            )

            icon = radio_checked if is_selected else radio_empty
            draw_row_icon_right(surface, row_rect, icon)

        disclaimer_y = rect.y + rect.height - self.CONTENT_PADDING - 8
        draw_wrapped_text(
            surface,
            "Language preference is saved now and applied in upcoming localization updates",
            SETTINGS.UI_TYPOGRAPHY.SMALL,
            SETTINGS.UI_THEME.TEXT_MUTED,
            row_width,
            line_spacing=2,
            assets=assets,
            x=content_center_x,
            y=disclaimer_y,
            align="center",
        )
        
        reset_button_y = bottom_action_y(
            rect,
            self.CONTENT_PADDING,
            action_height=42,
            reserve_space=self.FOOTER_RESERVED_SPACE,
        )
        self.render_reset_button(surface, rect, assets, reset_button_y)

    def handle_click(
        self,
        pos: tuple[int, int],
        settings_manager: Optional["SettingsManager"],
    ) -> None:
        if settings_manager is None:
            return

        for (lang_code, region_code), rect in self._option_hitboxes:
            if rect.collidepoint(pos):
                try:
                    settings_manager.set("localization.language", lang_code)
                    settings_manager.set("localization.region", region_code)
                except (KeyError, TypeError, ValueError):
                    pass
                return

    def handle_mouse_motion(self, pos: tuple[int, int]) -> None:
        self.hovered_option = None
        for codes, rect in self._option_hitboxes:
            if rect.collidepoint(pos):
                self.hovered_option = codes
                return

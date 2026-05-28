from abc import ABC, abstractmethod
from typing import Literal, Optional, TYPE_CHECKING

import pygame

from settings import SETTINGS
from ui.styles import SETTINGS_STYLE

if TYPE_CHECKING:
    from ui.assets import AssetManager
    from utils.settings_manager import SettingsManager


class SettingsTab(ABC):
    def __init__(self, id: str, title: str, icon_name: str, order: int, category: str) -> None:
        self.id = id
        self.title = title
        self.icon_name = icon_name
        self.order = order
        self.category = category
        self.assets: Optional["AssetManager"] = None
        self.settings_manager: Optional["SettingsManager"] = None
        self._reset_button_hitbox: Optional[pygame.Rect] = None
        self._reset_button_hovered: bool = False

    @abstractmethod
    def render(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
    ) -> None:
        pass

    @abstractmethod
    def handle_click(
        self,
        pos: tuple[int, int],
    ) -> None:
        pass

    def handle_key(
        self,
        event: pygame.event.Event,
    ) -> None:
        pass

    def render_reset_button(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        y_pos: int,
    ) -> int:
        button_height = 42
        icon_size = 18
        side_padding = 16
        icon_text_gap = 10

        font = self._font(SETTINGS.UI_TYPOGRAPHY.SMALL)
        label = "Reset This Section"
        label_surface = self._render_text_surface(
            label,
            SETTINGS.UI_TYPOGRAPHY.SMALL,
            SETTINGS.UI_THEME.TEXT_PRIMARY,
        )

        icon = self._try_load_icon("back")
        icon_width = icon_size if icon is not None else 0
        group_width = label_surface.get_width() + (icon_text_gap + icon_width if icon_width > 0 else 0)

        max_button_width = max(180, rect.width - 2 * 40)
        button_width = min(max_button_width, max(220, group_width + side_padding * 2))
        button_x = rect.x + (rect.width - button_width) // 2
        button_y = y_pos

        button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        self._reset_button_hitbox = pygame.Rect(
            button_x - rect.x,
            button_y - rect.y,
            button_width,
            button_height
        )

        bg_color = SETTINGS_STYLE.SECTION_RESET_BG_HOVER if self._reset_button_hovered else SETTINGS_STYLE.SECTION_RESET_BG
        border_color = SETTINGS_STYLE.SECTION_RESET_BORDER_HOVER if self._reset_button_hovered else SETTINGS_STYLE.SECTION_RESET_BORDER
        pygame.draw.rect(surface, bg_color, button_rect, border_radius=10)
        pygame.draw.rect(surface, border_color, button_rect, width=1, border_radius=10)

        group_start_x = button_rect.x + (button_rect.width - group_width) // 2
        if icon:
            icon_scaled = pygame.transform.scale(icon, (icon_size, icon_size))
            icon_y = button_rect.centery - icon_size // 2
            surface.blit(icon_scaled, (group_start_x, icon_y))
            text_x = group_start_x + icon_size + icon_text_gap
        else:
            text_x = group_start_x

        text_y = button_rect.centery - label_surface.get_height() // 2
        surface.blit(label_surface, (text_x, text_y))

        return button_y + button_height

    def check_reset_button_click(self, pos: tuple[int, int]) -> bool:
        if self._reset_button_hitbox and self._reset_button_hitbox.collidepoint(pos):
            return True
        return False

    def set_reset_button_hovered(self, pos: tuple[int, int]) -> None:
        self._reset_button_hovered = (
            self._reset_button_hitbox is not None and self._reset_button_hitbox.collidepoint(pos)
        )

    def _font(self, size: int) -> pygame.font.Font:
        if self.assets is not None:
            try:
                return self.assets.get_font(size)
            except (KeyError, FileNotFoundError, pygame.error):
                pass
        return pygame.font.Font(None, size)

    def _try_load_icon(self, icon_name: str) -> Optional[pygame.Surface]:
        if not self.assets:
            return None
        try:
            return self.assets.get_image(icon_name)
        except (KeyError, FileNotFoundError):
            return None

    def _draw_centered_text(
        self,
        surface: pygame.Surface,
        text: str,
        size: int,
        color: tuple[int, int, int],
        center: tuple[int, int],
    ) -> None:
        rendered = self._render_text_surface(text, size, color)
        surface.blit(rendered, rendered.get_rect(center=center))

    def _render_text_surface(
        self,
        text: str,
        size: int,
        color: tuple[int, int, int],
    ) -> pygame.Surface:
        return self._font(size).render(text, SETTINGS.UI_TYPOGRAPHY.ANTIALIAS, color)

    def _draw_tab_background_and_title(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        title: str,
        content_padding: int,
    ) -> tuple[int, int, int]:
        pygame.draw.rect(surface, SETTINGS_STYLE.CONTENT_BG, rect)

        title_y = rect.y + content_padding + 12
        content_center_x = rect.x + rect.width // 2
        
        title_surface = self._render_text_surface(
            title,
            SETTINGS.UI_TYPOGRAPHY.TITLE,
            SETTINGS.UI_THEME.CYAN,
        )
        surface.blit(title_surface, title_surface.get_rect(center=(content_center_x, title_y)))
        
        title_bottom = title_y + title_surface.get_height()
        content_start_y = title_bottom + 36

        return title_y, content_center_x, content_start_y

    def _draw_wrapped_text(
        self,
        surface: pygame.Surface,
        text: str,
        font_size: int,
        color: tuple[int, int, int],
        max_width: int,
        line_spacing: int,
        *,
        x: int,
        y: int,
        align: Literal["left", "center"] = "left",
    ) -> int:
        font = self._font(font_size)
        words = text.split()
        lines: list[str] = []
        current_line: list[str] = []

        for word in words:
            test_line = " ".join(current_line + [word])
            if font.size(test_line)[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        if align == "left":
            current_y = y
            for line in lines:
                rendered = self._render_text_surface(line, font_size, color)
                surface.blit(rendered, (x, current_y))
                current_y += rendered.get_height() + line_spacing
            return current_y

        line_height = font.get_height()
        total_height = len(lines) * (line_height + line_spacing) - line_spacing if lines else 0
        start_y = y - total_height // 2
        for index, line in enumerate(lines):
            rendered = self._render_text_surface(line, font_size, color)
            line_y = start_y + index * (line_height + line_spacing)
            surface.blit(rendered, rendered.get_rect(center=(x, line_y)))
        return start_y + total_height

    def _bottom_action_y(
        self,
        rect: pygame.Rect,
        content_padding: int,
        *,
        action_height: int,
        bottom_gap: int = 16,
        reserve_space: int = 0,
    ) -> int:
        return rect.y + rect.height - content_padding - action_height - bottom_gap - reserve_space

    def _draw_option_row(
        self,
        surface: pygame.Surface,
        row_rect: pygame.Rect,
        label: str,
        font: pygame.font.Font,
        *,
        text_size: int = SETTINGS.UI_TYPOGRAPHY.BODY,
        is_hovered: bool = False,
        is_selected: bool = False,
        label_left_padding: int = 16,
        border_radius: int = 10,
        normal_bg: tuple[int, int, int] = SETTINGS_STYLE.ROW_BG,
        hover_bg: tuple[int, int, int] = SETTINGS_STYLE.ROW_BG_HOVER,
        selected_bg: Optional[tuple[int, int, int]] = SETTINGS_STYLE.ROW_BG_SELECTED,
        text_color: tuple[int, int, int] = SETTINGS.UI_THEME.TEXT_PRIMARY,
    ) -> None:
        if is_selected and selected_bg is not None:
            bg_color = selected_bg
        elif is_hovered:
            bg_color = hover_bg
        else:
            bg_color = normal_bg

        pygame.draw.rect(surface, bg_color, row_rect, border_radius=border_radius)

        label_surface = self._render_text_surface(label, text_size, text_color)
        label_rect = label_surface.get_rect(midleft=(row_rect.left + label_left_padding, row_rect.centery))
        surface.blit(label_surface, label_rect)

    def _draw_row_icon_right(
        self,
        surface: pygame.Surface,
        row_rect: pygame.Rect,
        icon: Optional[pygame.Surface],
        *,
        icon_size: int = 28,
        right_padding: int = 16,
        alpha: Optional[int] = None,
    ) -> None:
        if icon is None:
            return

        icon_scaled = pygame.transform.scale(icon, (icon_size, icon_size))
        if alpha is not None:
            icon_scaled.set_alpha(alpha)
        icon_rect = icon_scaled.get_rect(midright=(row_rect.right - right_padding, row_rect.centery))
        surface.blit(icon_scaled, icon_rect)

    def _draw_row_value_right(
        self,
        surface: pygame.Surface,
        row_rect: pygame.Rect,
        value_text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        *,
        text_size: int = SETTINGS.UI_TYPOGRAPHY.BODY,
        right_padding: int = 16,
    ) -> None:
        value_surface = self._render_text_surface(value_text, text_size, color)
        value_rect = value_surface.get_rect(midright=(row_rect.right - right_padding, row_rect.centery))
        surface.blit(value_surface, value_rect)


class SettingsTabRegistry:
    _instance: Optional["SettingsTabRegistry"] = None

    def __new__(cls) -> "SettingsTabRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tabs = {}
            cls._instance._assets = None
            cls._instance._settings_manager = None
        return cls._instance

    def register(self, tab: SettingsTab) -> None:
        if tab.id in self._tabs:
            from utils.logger import log
            log.warning(f"Settings tab '{tab.id}' already registered, overwriting")

        tab.assets = self._assets
        tab.settings_manager = self._settings_manager
        self._tabs[tab.id] = tab

    def get_all(self) -> list[SettingsTab]:
        sorted_tabs = sorted(
            self._tabs.values(),
            key=lambda t: (t.order, t.title, t.id)
        )
        return sorted_tabs

    def get_by_id(self, tab_id: str) -> Optional[SettingsTab]:
        return self._tabs.get(tab_id)

    def has_tabs(self) -> bool:
        return len(self._tabs) > 0

    def clear(self) -> None:
        self._tabs.clear()

    def distribute_assets(self, assets: Optional["AssetManager"]) -> None:
        self._assets = assets
        for tab in self._tabs.values():
            tab.assets = assets

    def distribute_settings_manager(self, settings_manager: Optional["SettingsManager"]) -> None:
        self._settings_manager = settings_manager
        for tab in self._tabs.values():
            tab.settings_manager = settings_manager

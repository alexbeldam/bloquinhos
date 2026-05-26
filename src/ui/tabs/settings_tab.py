from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

import pygame

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
        self._reset_button_hitbox: Optional[pygame.Rect] = None
        self._reset_button_hovered: bool = False

    @abstractmethod
    def render(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        assets: Optional["AssetManager"],
        settings_manager: Optional["SettingsManager"],
    ) -> None:
        pass

    @abstractmethod
    def handle_click(
        self,
        pos: tuple[int, int],
        settings_manager: Optional["SettingsManager"],
    ) -> None:
        pass

    def handle_key(
        self,
        event: pygame.event.Event,
        settings_manager: Optional["SettingsManager"],
    ) -> None:
        pass

    def render_reset_button(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        assets: Optional["AssetManager"],
        y_pos: int,
    ) -> int:
        from settings import SETTINGS

        button_height = 42
        icon_size = 18
        side_padding = 16
        icon_text_gap = 10

        font = self._font(SETTINGS.UI_TYPOGRAPHY.SMALL, assets)
        label = "Reset This Section"
        label_surface = font.render(label, True, SETTINGS.UI_THEME.TEXT_PRIMARY)

        icon = self._try_load_icon("back", assets)
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

        bg_color = SETTINGS.UI_THEME.SETTINGS_SECTION_RESET_BG_HOVER if self._reset_button_hovered else SETTINGS.UI_THEME.SETTINGS_SECTION_RESET_BG
        border_color = SETTINGS.UI_THEME.SETTINGS_SECTION_RESET_BORDER_HOVER if self._reset_button_hovered else SETTINGS.UI_THEME.SETTINGS_SECTION_RESET_BORDER
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

    def _font(self, size: int, assets: Optional["AssetManager"]) -> pygame.font.Font:
        if assets is not None:
            try:
                return assets.get_font(size)
            except (KeyError, FileNotFoundError, pygame.error):
                pass
        return pygame.font.Font(None, size)

    def _try_load_icon(self, icon_name: str, assets: Optional["AssetManager"]) -> Optional[pygame.Surface]:
        if not assets:
            return None
        try:
            return assets.get_image(icon_name)
        except (KeyError, FileNotFoundError):
            return None


class SettingsTabRegistry:
    _instance: Optional["SettingsTabRegistry"] = None

    def __new__(cls) -> "SettingsTabRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tabs = {}
        return cls._instance

    def register(self, tab: SettingsTab) -> None:
        if tab.id in self._tabs:
            from utils.logger import log
            log.warning(f"Settings tab '{tab.id}' already registered, overwriting")
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

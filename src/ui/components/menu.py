from typing import Callable, List, Optional, Sequence, Tuple

import pygame

from settings import SETTINGS


Color = Tuple[int, int, int]


class Menu:
    def __init__(
        self,
        options: Sequence[Tuple[str, str]],
        font_renderer: Callable[[int], pygame.font.Font],
        selected_color: Optional[Color] = None,
        unselected_color: Optional[Color] = None,
        font_size: Optional[int] = None,
        item_spacing: int = 50,
        selection_prefix: str = "> ",
        unselected_prefix: str = "  ",
        on_navigate: Optional[Callable[[], None]] = None,
        on_select: Optional[Callable[[], None]] = None,
    ) -> None:
        self.options = options
        self._font_renderer = font_renderer
        self.selected_color = selected_color or SETTINGS.UI_THEME.YELLOW
        self.unselected_color = unselected_color or SETTINGS.UI_THEME.TEXT_PRIMARY
        self.font_size = font_size or SETTINGS.UI_TYPOGRAPHY.TITLE
        self.item_spacing = item_spacing
        self.selection_prefix = selection_prefix
        self.unselected_prefix = unselected_prefix
        self.selected_index = 0
        self._on_navigate = on_navigate
        self._on_select = on_select

    def handle_navigation(self, event: pygame.event.Event) -> Optional[str]:
        if event.type != pygame.KEYDOWN:
            return None
        
        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected_index = (self.selected_index - 1) % len(self.options)
            if self._on_navigate:
                self._on_navigate()
            return None
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected_index = (self.selected_index + 1) % len(self.options)
            if self._on_navigate:
                self._on_navigate()
            return None
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            if self._on_select:
                self._on_select()
            return self.options[self.selected_index][1]
        
        return None

    def render(
        self,
        surface: pygame.Surface,
        center_x: int,
        start_y: int,
        text_renderer: Callable[[pygame.Surface, str, int, Color, Tuple[int, int]], None]
    ) -> None:
        for index, (label, _) in enumerate(self.options):
            is_selected = index == self.selected_index
            color = self.selected_color if is_selected else self.unselected_color
            prefix = self.selection_prefix if is_selected else self.unselected_prefix
            
            text_renderer(
                surface,
                f"{prefix}{label}",
                self.font_size,
                color,
                (center_x, start_y + index * self.item_spacing),
            )

    def reset_selection(self) -> None:
        self.selected_index = 0

    def get_selected_value(self) -> str:
        return self.options[self.selected_index][1]

    def get_menu_height(self) -> int:
        return len(self.options) * self.item_spacing

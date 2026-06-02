from typing import Dict, List, Optional, Sequence, Tuple, TYPE_CHECKING

import pygame

from settings import SETTINGS
from ui.assets import AssetManager
from ui.components import Menu
from ui.screen import Screen

if TYPE_CHECKING:
    from ui.audio import AudioManager
    from ui.screens.game import GameScreen


class MenuScreen(Screen):
    OPTIONS: Sequence[Tuple[str, str]] = (
        ("Jogar", SETTINGS.SCREEN_NAMES.GAME),
        ("Ranking", SETTINGS.SCREEN_NAMES.RANKING),
        ("Configurações", SETTINGS.SCREEN_NAMES.SETTINGS),
        ("Sair", SETTINGS.SCREEN_NAMES.QUIT),
    )
    EASTER_EGG_SEQUENCE = "sans"
    EASTER_EGG_TARGETS: Sequence[Tuple[int, int]] = (
        (3, 0),  # Sair
        (0, 3),  # Jogar
        (1, 2),  # Ranking
        (2, 12),  # Configurações
    )

    def __init__(
        self,
        assets: Optional[AssetManager] = None,
        audio_manager: Optional["AudioManager"] = None,
        game_screen: Optional["GameScreen"] = None,
    ) -> None:
        super().__init__(assets, audio_manager)
        self.game_screen = game_screen
        self._easter_egg_progress = 0
        self._easter_egg_letter_rects: Dict[int, pygame.Rect] = {}
        self.menu = Menu(
            options=self.OPTIONS,
            font_renderer=self._font,
            selected_color=SETTINGS.UI_THEME.YELLOW,
            unselected_color=SETTINGS.UI_THEME.PURPLE,
            font_size=SETTINGS.UI_TYPOGRAPHY.TITLE,
        )

    def handle_events(self, events: List[pygame.event.Event]) -> Optional[str]:
        for event in events:
            if event.type == pygame.QUIT:
                return SETTINGS.SCREEN_NAMES.QUIT

            if self._handle_network_status_event(event):
                continue
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return SETTINGS.SCREEN_NAMES.QUIT

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_easter_egg_click(event.pos)
            
            result = self.menu.handle_navigation(event)
            if result is not None:
                if result == SETTINGS.SCREEN_NAMES.GAME and self.game_screen is not None:
                    self.game_screen.set_sans_mode(self._is_easter_egg_unlocked())
                    self._reset_easter_egg()
                return result
        
        return None

    def update(self, delta_time: float) -> Optional[str]:
        if self.audio_manager:
            self.audio_manager.play_bgm("menu")
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
        menu_height = len(self.OPTIONS) * menu_item_spacing
        
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
            SETTINGS.APP_NAME,
            SETTINGS.UI_TYPOGRAPHY.TITLE,
            SETTINGS.UI_THEME.TEXT_PRIMARY,
            (center_x, current_y),
        )
        current_y += title_height + 60
        
        self.menu.render(surface, center_x, current_y, self._draw_text)
        self._cache_easter_egg_letter_rects(center_x, current_y)
        self._render_easter_egg_progress(surface)
        self._render_network_status(surface)

    def _handle_easter_egg_click(self, position: Tuple[int, int]) -> None:
        if self._is_easter_egg_unlocked():
            return

        next_rect = self._easter_egg_letter_rects.get(self._easter_egg_progress)
        if next_rect is not None and next_rect.collidepoint(position):
            self._easter_egg_progress += 1

    def _is_easter_egg_unlocked(self) -> bool:
        return self._easter_egg_progress >= len(self.EASTER_EGG_SEQUENCE)

    def _reset_easter_egg(self) -> None:
        self._easter_egg_progress = 0

    def _cache_easter_egg_letter_rects(self, center_x: int, menu_start_y: int) -> None:
        font = self._font(SETTINGS.UI_TYPOGRAPHY.TITLE)
        self._easter_egg_letter_rects = {}

        for index, (option_index, char_index) in enumerate(self.EASTER_EGG_TARGETS):
            label, _ = self.OPTIONS[option_index]
            prefix = (
                self.menu.selection_prefix
                if option_index == self.menu.selected_index
                else self.menu.unselected_prefix
            )
            rendered_text = f"{prefix}{label}"
            text_width, text_height = font.size(rendered_text)
            text_left = center_x - text_width // 2
            text_y = menu_start_y + option_index * self.menu.item_spacing
            text_top = text_y - text_height // 2
            prefix_width = font.size(prefix)[0]
            before_letter_width = font.size(label[:char_index])[0]
            letter = label[char_index]
            letter_width, letter_height = font.size(letter)

            self._easter_egg_letter_rects[index] = pygame.Rect(
                text_left + prefix_width + before_letter_width,
                text_top,
                letter_width,
                letter_height,
            )

    def _render_easter_egg_progress(self, surface: pygame.Surface) -> None:
        font = self._font(SETTINGS.UI_TYPOGRAPHY.TITLE)

        for index in range(min(self._easter_egg_progress, len(self.EASTER_EGG_TARGETS))):
            option_index, char_index = self.EASTER_EGG_TARGETS[index]
            letter = self.OPTIONS[option_index][0][char_index]
            rect = self._easter_egg_letter_rects.get(index)
            if rect is None:
                continue

            rendered = font.render(letter, SETTINGS.UI_TYPOGRAPHY.ANTIALIAS, SETTINGS.UI_THEME.RED)
            surface.blit(rendered, rect)

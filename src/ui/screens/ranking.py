from typing import List, Optional

import pygame

from settings import SETTINGS
from ui.assets import AssetManager
from ui.screen import Screen


class RankingScreen(Screen):
    def handle_events(self, events: List[pygame.event.Event]) -> Optional[str]:
        for event in events:
            if event.type == pygame.QUIT:
                return SETTINGS.SCREEN_NAMES.QUIT
            if self._handle_network_status_event(event):
                continue
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_ESCAPE,
                pygame.K_RETURN,
                pygame.K_SPACE,
            ):
                return SETTINGS.SCREEN_NAMES.MENU
        return None

    def update(self, delta_time: float) -> Optional[str]:
        if self.audio_manager:
            self.audio_manager.play_bgm("menu")
        return None

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(SETTINGS.UI_THEME.BG_MEDIUM)
        self._draw_text(
            surface,
            "RANKING",
            SETTINGS.UI_TYPOGRAPHY.DISPLAY,
            SETTINGS.UI_THEME.TEXT_PRIMARY,
            (surface.get_width() // 2, 150),
        )
        self._draw_text(
            surface,
            "Em breve",
            SETTINGS.UI_TYPOGRAPHY.LARGE,
            SETTINGS.UI_THEME.PURPLE,
            (surface.get_width() // 2, 270),
        )
        self._render_network_status(surface)

import re
from typing import List, Optional, TYPE_CHECKING

import pygame

from security import IdentityManager
from settings import SETTINGS
from ui.assets import AssetManager
from ui.screen import Screen

if TYPE_CHECKING:
    from network.connection_manager import NetworkManager
    from ui.audio import AudioManager


class IdentityEntryScreen(Screen):
    def __init__(
        self,
        network_manager: "NetworkManager",
        assets: Optional[AssetManager] = None,
        audio_manager: Optional["AudioManager"] = None,
    ) -> None:
        super().__init__(assets, audio_manager)
        self.identity_manager = IdentityManager(network_manager=network_manager)
        self._text = ""
        self._error: Optional[str] = None

    def handle_events(self, events: List[pygame.event.Event]) -> Optional[str]:
        for event in events:
            if event.type == pygame.QUIT:
                return SETTINGS.SCREEN_NAMES.QUIT
            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                return SETTINGS.SCREEN_NAMES.QUIT
            if event.key == pygame.K_BACKSPACE:
                self._text = self._text[:-1]
                self._error = None
                continue
            if event.key == pygame.K_RETURN:
                if self.identity_manager.register_identity(self._text):
                    return SETTINGS.SCREEN_NAMES.MENU
                self._error = "Use 3-15 letters, numbers, or underscore. Name must be unique."
                continue

            if event.unicode and len(self._text) < 15:
                candidate = self._text + event.unicode
                if re.fullmatch(r"[A-Za-z0-9_]{0,15}", candidate):
                    self._text = candidate
                    self._error = None

        return None

    def update(self, delta_time: float) -> Optional[str]:
        return None

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(SETTINGS.UI_THEME.BG_DARK)
        center_x = surface.get_width() // 2
        center_y = surface.get_height() // 2

        self._draw_text(
            surface,
            "Player Name",
            SETTINGS.UI_TYPOGRAPHY.TITLE,
            SETTINGS.UI_THEME.TEXT_PRIMARY,
            (center_x, center_y - 105),
        )
        self._draw_text(
            surface,
            "3-15: letters, numbers, and _",
            SETTINGS.UI_TYPOGRAPHY.SMALL,
            SETTINGS.UI_THEME.TEXT_MUTED,
            (center_x, center_y - 65),
        )

        input_width = min(380, surface.get_width() - 48)
        input_rect = pygame.Rect(0, 0, input_width, 46)
        input_rect.center = (center_x, center_y)
        pygame.draw.rect(surface, SETTINGS.UI_THEME.BG_MEDIUM, input_rect, border_radius=6)
        pygame.draw.rect(surface, SETTINGS.UI_THEME.PURPLE, input_rect, 2, border_radius=6)

        display_text = self._text or "_"
        rendered_input = self._font(SETTINGS.UI_TYPOGRAPHY.BODY).render(
            display_text,
            True,
            SETTINGS.UI_THEME.YELLOW,
        )
        surface.blit(rendered_input, rendered_input.get_rect(center=input_rect.center))

        if self._error:
            self._draw_wrapped_text(
                surface,
                self._error,
                SETTINGS.UI_TYPOGRAPHY.SMALL,
                SETTINGS.UI_THEME.RED,
                (center_x, center_y + 62),
                max_width=max(240, surface.get_width() - 48),
            )

        self._draw_text(
            surface,
            "Enter confirms",
            SETTINGS.UI_TYPOGRAPHY.SMALL,
            SETTINGS.UI_THEME.TEXT_MUTED,
            (center_x, center_y + 105),
        )

from __future__ import annotations

import math

import pygame

from settings import SETTINGS
from ui.effects.base import Effect


class LevelUpNotification(Effect):
    def __init__(self, new_level: int) -> None:
        self._new_level = new_level
        self._duration = 2.0
        self._elapsed = 0.0
        self._completed = False

        self._slide_in = 0.3
        self._pause = 0.4
        self._blink = 0.8
        self._fade_out = 0.5

    def update(self, delta_time: float) -> bool:
        if self._completed:
            return True
        self._elapsed += delta_time
        if self._elapsed >= self._duration:
            self._completed = True
            return True
        return False

    def render(self, surface: pygame.Surface) -> None:
        if self._completed:
            return

        center_x = SETTINGS.GRID.GAME_WIDTH // 2
        center_y = SETTINGS.GRID.GAME_HEIGHT // 2

        alpha = 255
        offset_y = 0

        if self._elapsed < self._slide_in:
            t = self._elapsed / self._slide_in
            offset_y = int((t - 1) * 60)
        elif self._elapsed < self._slide_in + self._pause:
            offset_y = 0
        elif self._elapsed < self._slide_in + self._pause + self._blink:
            blink_t = (self._elapsed - self._slide_in - self._pause) / self._blink
            blink_alpha = int((math.sin(blink_t * math.pi * 6) * 0.5 + 0.5) * 255)
            alpha = min(alpha, blink_alpha)
            offset_y = 0
        else:
            fade_t = (self._elapsed - self._slide_in - self._pause - self._blink) / self._fade_out
            alpha = max(0, int((1.0 - fade_t) * 255))

        if alpha <= 0:
            return

        font = pygame.font.Font(None, SETTINGS.UI_TYPOGRAPHY.TITLE)
        text_surface = font.render(
            "LEVEL UP!",
            SETTINGS.UI_TYPOGRAPHY.ANTIALIAS,
            (255, 255, 255),
        )
        text_surface.set_alpha(alpha)
        text_rect = text_surface.get_rect(center=(center_x, center_y + offset_y))
        surface.blit(text_surface, text_rect)

        level_font = pygame.font.Font(None, SETTINGS.UI_TYPOGRAPHY.DISPLAY)
        level_surface = level_font.render(
            str(self._new_level),
            SETTINGS.UI_TYPOGRAPHY.ANTIALIAS,
            (255, 255, 50),
        )
        level_surface.set_alpha(alpha)
        level_rect = level_surface.get_rect(center=(center_x, center_y + offset_y + 50))
        surface.blit(level_surface, level_rect)
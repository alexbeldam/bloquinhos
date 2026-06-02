from __future__ import annotations

import random
from typing import List

from settings import SETTINGS
from ui.effects.base import Effect
from ui.effects.color import hsv_to_rgb


class _Particle:
    def __init__(self, x: float, y: float, vx: float, vy: float, life: float) -> None:
        self._x = x
        self._y = y
        self._vx = vx
        self._vy = vy
        self._life = life
        self._elapsed = 0.0
        self._gravity = 400.0

    def update(self, delta_time: float) -> None:
        self._elapsed += delta_time
        self._vy += self._gravity * delta_time
        self._x += self._vx * delta_time
        self._y += self._vy * delta_time

    def render(self, surface: "pygame.Surface") -> None:
        import pygame

        if self._elapsed >= self._life:
            return
        t = self._elapsed / self._life
        alpha = max(0, int((1.0 - t) * 255))  # kept for future use
        hue = (self._elapsed * 120) % 360
        color = hsv_to_rgb(hue, 1.0, 1.0)
        radius = max(1, int(4 * (1.0 - t)))
        pos = (int(self._x), int(self._y))
        pygame.draw.circle(surface, color, pos, radius)


class TetrisCombo(Effect):
    def __init__(self) -> None:
        self._duration = 2.0
        self._elapsed = 0.0
        self._completed = False
        self._particles: List[_Particle] = []

        for _ in range(30):
            self._particles.append(_Particle(
                SETTINGS.GRID.GAME_WIDTH // 2,
                SETTINGS.GRID.GAME_HEIGHT // 2,
                random.uniform(-150, 150),
                random.uniform(-200, 50),
                random.uniform(0.3, 0.8),
            ))

    def update(self, delta_time: float) -> bool:
        if self._completed:
            return True
        self._elapsed += delta_time
        for p in self._particles:
            p.update(delta_time)
        if self._elapsed >= self._duration:
            self._completed = True
            return True
        return False

    def _render_rainbow_wave(self, surface: "pygame.Surface") -> None:
        import pygame

        game_width = SETTINGS.GRID.GAME_WIDTH
        game_height = SETTINGS.GRID.GAME_HEIGHT
        progress = self._elapsed / self._duration

        wave_alpha = max(0, int((1.0 - progress) * 80))
        if wave_alpha <= 0:
            return

        wave_surface = pygame.Surface((game_width, game_height), pygame.SRCALPHA)
        band_height = 4
        wave_offset = progress * game_width * 2

        for y in range(0, game_height, band_height):
            hue = (y * 0.8 + wave_offset) % 360
            color = hsv_to_rgb(hue, 1.0, 1.0)
            rect = pygame.Rect(0, y, game_width, band_height)
            pygame.draw.rect(wave_surface, (*color, wave_alpha), rect)

        surface.blit(wave_surface, (0, 0))

    def render(self, surface: "pygame.Surface") -> None:
        import pygame

        if self._completed:
            return

        self._render_rainbow_wave(surface)

        for p in self._particles:
            p.render(surface)

        center_x = SETTINGS.GRID.GAME_WIDTH // 2
        center_y = SETTINGS.GRID.GAME_HEIGHT // 2 - 40

        progress = self._elapsed / self._duration
        scale = 1.0
        alpha = 255

        if progress < 0.15:
            scale = 0.3 + 0.7 * (progress / 0.15)
        elif progress > 0.75:
            fade = (progress - 0.75) / 0.25
            alpha = max(0, int((1.0 - fade) * 255))

        font = pygame.font.Font(None, SETTINGS.UI_TYPOGRAPHY.DISPLAY)
        text_surface = font.render(
            "TETRIS!",
            SETTINGS.UI_TYPOGRAPHY.ANTIALIAS,
            (255, 255, 255),
        )

        scaled_size = (int(text_surface.get_width() * scale),
                       int(text_surface.get_height() * scale))
        if scaled_size[0] > 0 and scaled_size[1] > 0:
            text_surface = pygame.transform.scale(text_surface, scaled_size)
        text_surface.set_alpha(alpha)
        text_rect = text_surface.get_rect(center=(center_x, center_y))
        surface.blit(text_surface, text_rect)
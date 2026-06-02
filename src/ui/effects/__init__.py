from __future__ import annotations

import random
from abc import ABC, abstractmethod
from math import sin
from typing import List, Sequence

import pygame

from settings import SETTINGS


class Effect(ABC):
    @abstractmethod
    def update(self, delta_time: float) -> bool: ...

    @abstractmethod
    def render(self, surface: pygame.Surface) -> None: ...


class LineClearFlash(Effect):
    def __init__(self, line_indices: Sequence[int]) -> None:
        self._line_indices = list(line_indices)
        self._duration = 0.15
        self._elapsed = 0.0
        self._flash_count = 3
        self._completed = False

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

        tile_size = SETTINGS.GRID.TILE_SIZE
        flash_duration = self._duration / self._flash_count
        current_flash = int(self._elapsed / flash_duration)
        on = current_flash % 2 == 0

        if on:
            for line_y in self._line_indices:
                rect = pygame.Rect(
                    0,
                    line_y * tile_size,
                    SETTINGS.GRID.GAME_WIDTH,
                    tile_size,
                )
                pygame.draw.rect(surface, (255, 255, 255), rect)


class LevelUpNotification(Effect):
    def __init__(self, new_level: int) -> None:
        self._new_level = new_level
        self._duration = 1.5
        self._elapsed = 0.0
        self._completed = False

        self._slide_in = 0.3
        self._pause = 0.7
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
        else:
            fade_t = (self._elapsed - self._slide_in - self._pause) / self._fade_out
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

    def _render_rainbow_wave(self, surface: pygame.Surface) -> None:
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
            color = _hsv_to_rgb(hue, 1.0, 1.0)
            rect = pygame.Rect(0, y, game_width, band_height)
            pygame.draw.rect(wave_surface, (*color, wave_alpha), rect)

        surface.blit(wave_surface, (0, 0))

    def render(self, surface: pygame.Surface) -> None:
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

    def render(self, surface: pygame.Surface) -> None:
        if self._elapsed >= self._life:
            return
        t = self._elapsed / self._life
        alpha = max(0, int((1.0 - t) * 255))
        hue = (self._elapsed * 120) % 360
        color = _hsv_to_rgb(hue, 1.0, 1.0)
        radius = max(1, int(4 * (1.0 - t)))
        pos = (int(self._x), int(self._y))
        pygame.draw.circle(surface, color, pos, radius)


class ScreenShake(Effect):
    def __init__(self) -> None:
        self._duration = 0.2
        self._elapsed = 0.0
        self._intensity = 5
        self._completed = False
        self.offset_x = 0
        self.offset_y = 0

    def update(self, delta_time: float) -> bool:
        if self._completed:
            return True
        self._elapsed += delta_time
        if self._elapsed >= self._duration:
            self._completed = True
            self.offset_x = 0
            self.offset_y = 0
            return True

        decay = 1.0 - (self._elapsed / self._duration)
        intensity = self._intensity * decay
        self.offset_x = int(sin(self._elapsed * 60.0) * intensity)
        self.offset_y = int(sin(self._elapsed * 50.0 + 1.0) * intensity)
        return False

    def render(self, surface: pygame.Surface) -> None:
        pass


class EffectManager:
    def __init__(self) -> None:
        self._active_effects: List[Effect] = []

    def add_effect(self, effect: Effect) -> None:
        self._active_effects.append(effect)

    def update(self, delta_time: float) -> None:
        self._active_effects = [
            e for e in self._active_effects
            if not e.update(delta_time)
        ]

    def render(self, surface: pygame.Surface) -> None:
        for effect in self._active_effects:
            effect.render(surface)

    def get_active_effects(self) -> List[Effect]:
        return list(self._active_effects)

    def clear(self) -> None:
        self._active_effects.clear()


def _hsv_to_rgb(h: float, s: float, v: float) -> tuple[int, int, int]:
    h = h % 360
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)


__all__ = [
    "Effect", "EffectManager", "LineClearFlash",
    "LevelUpNotification", "TetrisCombo", "ScreenShake",
]
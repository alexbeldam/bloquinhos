from __future__ import annotations

from typing import Sequence

from settings import SETTINGS
from ui.effects.base import Effect


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

    def render(self, surface: "pygame.Surface") -> None:
        if self._completed:
            return

        import pygame

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
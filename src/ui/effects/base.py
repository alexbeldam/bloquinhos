from __future__ import annotations

from abc import ABC, abstractmethod

import pygame


class Effect(ABC):
    @abstractmethod
    def update(self, delta_time: float) -> bool: ...

    @abstractmethod
    def render(self, surface: pygame.Surface) -> None: ...
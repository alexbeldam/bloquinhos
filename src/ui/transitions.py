from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

import pygame

from settings import SETTINGS


class Direction(Enum):
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"


class TransitionEffect(ABC):
    def __init__(self, duration: float) -> None:
        self.duration = duration
        self._elapsed: float = 0.0
        self._started: bool = False

    @abstractmethod
    def start(self, from_surface: pygame.Surface, to_surface: pygame.Surface) -> None:
        ...

    def update(self, delta_time: float) -> bool:
        if not self._started:
            return False
        self._elapsed += delta_time
        return self.is_complete()

    @abstractmethod
    def render(self, surface: pygame.Surface) -> None:
        ...

    def is_complete(self) -> bool:
        return self._elapsed >= self.duration

    def reset(self) -> None:
        self._elapsed = 0.0
        self._started = False


class FadeTransition(TransitionEffect):
    def __init__(self, duration: float = 0.3) -> None:
        super().__init__(duration)
        self._from_surface: Optional[pygame.Surface] = None
        self._to_surface: Optional[pygame.Surface] = None

    def start(self, from_surface: pygame.Surface, to_surface: pygame.Surface) -> None:
        self._from_surface = from_surface.copy()
        self._to_surface = to_surface.copy()
        self._started = True

    def render(self, surface: pygame.Surface) -> None:
        if self._from_surface is None or self._to_surface is None:
            return

        progress = min(self._elapsed / self.duration, 1.0)
        surface.blit(self._from_surface, (0, 0))
        self._to_surface.set_alpha(int(progress * 255))
        surface.blit(self._to_surface, (0, 0))
        self._to_surface.set_alpha(255)


class SlideTransition(TransitionEffect):
    def __init__(self, direction: Direction = Direction.LEFT, duration: float = 0.4) -> None:
        super().__init__(duration)
        self.direction = direction
        self._from_surface: Optional[pygame.Surface] = None
        self._to_surface: Optional[pygame.Surface] = None

    @staticmethod
    def _ease_in_out(t: float) -> float:
        if t < 0.5:
            return 2.0 * t * t
        return -1.0 + (4.0 - 2.0 * t) * t

    def start(self, from_surface: pygame.Surface, to_surface: pygame.Surface) -> None:
        self._from_surface = from_surface.copy()
        self._to_surface = to_surface.copy()
        self._started = True

    def render(self, surface: pygame.Surface) -> None:
        if self._from_surface is None or self._to_surface is None:
            return

        progress = min(self._elapsed / self.duration, 1.0)
        eased = self._ease_in_out(progress)

        width = surface.get_width()
        height = surface.get_height()

        if self.direction == Direction.LEFT:
            from_x = -int(eased * width)
            to_x = width - int(eased * width)
            from_y = to_y = 0
        elif self.direction == Direction.RIGHT:
            from_x = int(eased * width)
            to_x = -width + int(eased * width)
            from_y = to_y = 0
        elif self.direction == Direction.UP:
            from_y = -int(eased * height)
            to_y = height - int(eased * height)
            from_x = to_x = 0
        else:
            from_y = int(eased * height)
            to_y = -height + int(eased * height)
            from_x = to_x = 0

        surface.blit(self._from_surface, (from_x, from_y))
        surface.blit(self._to_surface, (to_x, to_y))


def determine_transition(from_name: Optional[str], to_name: str) -> Optional[TransitionEffect]:
    names = SETTINGS.SCREEN_NAMES

    if from_name is None or from_name == to_name:
        return None

    duration = SETTINGS.UI.TRANSITION_DURATION

    if from_name == names.LOADING:
        return FadeTransition(duration=duration)

    if {from_name, to_name} == {names.GAME, names.PAUSE}:
        return FadeTransition(duration=min(duration, 0.2))

    if {from_name, to_name} == {names.GAME, names.GAME_OVER}:
        return FadeTransition(duration=duration)

    if {from_name, to_name} == {names.MENU, names.SETTINGS}:
        return FadeTransition(duration=duration)

    if {from_name, to_name} == {names.MENU, names.GAME}:
        return FadeTransition(duration=duration)

    return FadeTransition(duration=duration)


__all__ = [
    "TransitionEffect",
    "FadeTransition",
    "SlideTransition",
    "Direction",
    "determine_transition",
]
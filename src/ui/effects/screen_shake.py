from __future__ import annotations

from math import sin

from ui.effects.base import Effect


class ScreenShake(Effect):
    def __init__(self) -> None:
        self._duration = 0.25
        self._elapsed = 0.0
        self._intensity = 3
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
        intensity = self._intensity * decay * decay
        self.offset_x = int(sin(self._elapsed * 40.0) * intensity)
        self.offset_y = int(sin(self._elapsed * 35.0 + 1.0) * intensity)
        return False

    def render(self, surface: "pygame.Surface") -> None:
        pass
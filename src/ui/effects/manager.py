from __future__ import annotations

from typing import List

from ui.effects.base import Effect


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

    def render(self, surface: "pygame.Surface") -> None:
        for effect in self._active_effects:
            effect.render(surface)

    def get_active_effects(self) -> List[Effect]:
        return list(self._active_effects)

    def clear(self) -> None:
        self._active_effects.clear()
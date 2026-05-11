from typing import Dict, Optional

import pygame

from settings import SETTINGS
from ui.screen import Screen


class ScreenManager:
    def __init__(self, surface: pygame.Surface) -> None:
        self.surface = surface
        self.clock = pygame.time.Clock()
        self._screens: Dict[str, Screen] = {}
        self.current_screen: Optional[Screen] = None
        self._current_name: Optional[str] = None
        self._running = False

    def register_screen(self, name: str, screen: Screen) -> None:
        self._screens[name] = screen

    def switch_to(self, name: str) -> None:
        if name not in self._screens:
            raise KeyError(f"Screen '{name}' is not registered.")

        pygame.event.clear()
        self._current_name = name
        self.current_screen = self._screens[name]

    def run(self) -> None:
        if self.current_screen is None:
            raise RuntimeError("Cannot run ScreenManager without an active screen.")

        self._running = True
        while self._running:
            delta_time = self.clock.tick(SETTINGS.SCREEN.FPS) / 1000.0
            events = pygame.event.get()

            next_screen = self.current_screen.handle_events(events)
            if next_screen == "quit":
                self._running = False
                break
            if next_screen is not None:
                self.switch_to(next_screen)

            if self.current_screen is None:
                continue

            self.current_screen.update(delta_time)
            self.current_screen.render(self.surface)
            pygame.display.flip()

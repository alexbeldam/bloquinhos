from typing import Callable, Dict, Optional
import os

import pygame

from settings import SETTINGS
from ui.screen import Screen
from ui.transitions import TransitionEffect, determine_transition
from utils.logger import log
from utils.localization import tr


class ScreenManager:
    def __init__(self, width: int, height: int, decorated: bool = True, icon: Optional[pygame.Surface] = None) -> None:
        self.clock = pygame.time.Clock()
        self._screens: Dict[str, Screen] = {}
        self.current_screen: Optional[Screen] = None
        self._current_name: Optional[str] = None
        self._previous_name: Optional[str] = None
        self._running = False
        self._transition_guard: Optional[Callable[[str], str]] = None
        self._transition: Optional[TransitionEffect] = None
        self._create_window(width, height, decorated, icon)

    def _create_window(self, width: int, height: int, decorated: bool, icon: Optional[pygame.Surface] = None) -> None:
        self._center_window()
        flags = 0 if decorated else pygame.NOFRAME
        self.surface = pygame.display.set_mode((width, height), flags)
        pygame.display.set_caption(self._localized_app_name())
        
        if icon is not None:
            pygame.display.set_icon(icon)
        
        self.surface.fill(SETTINGS.UI_THEME.BG_DARKER)
        pygame.display.flip()

    def _center_window(self) -> None:
        os.environ['SDL_VIDEO_WINDOW_POS'] = 'center'

    def reconfigure_window(
        self,
        width: int,
        height: int,
        caption: str = "",
        icon: Optional[pygame.Surface] = None,
        decorated: bool = True
    ) -> None:
        log.debug(f"Recreating window with size: {width}x{height}")
        pygame.display.quit()
        pygame.display.init()
        self._create_window(width, height, decorated, icon)
        
        if caption:
            pygame.display.set_caption(caption)

    @staticmethod
    def _localized_app_name() -> str:
        localized = tr("app.name")
        if not localized or localized == "app.name":
            return SETTINGS.APP_NAME
        return localized

    def register_screen(self, name: str, screen: Screen) -> None:
        self._screens[name] = screen

    def set_transition_guard(self, guard: Callable[[str], str]) -> None:
        self._transition_guard = guard

    @property
    def is_transitioning(self) -> bool:
        return self._transition is not None and not self._transition.is_complete()

    def switch_to(self, name: str) -> None:
        name = self._apply_transition_guard(name)
        if name not in self._screens:
            raise KeyError(f"Screen '{name}' is not registered.")

        log.debug(f"Switching to screen: {name}")

        if self._transition is not None:
            self._finish_transition()

        if (
            self.current_screen is not None
            and self._current_name is not None
            and SETTINGS.UI.TRANSITION_ENABLED
        ):
            transition = determine_transition(self._current_name, name)
            if transition is not None:
                from_surface = self.surface.copy()
                pygame.event.clear()
                self._previous_name = self._current_name
                self._current_name = name
                self.current_screen = self._screens[name]
                self.current_screen.render(self.surface)
                to_surface = self.surface.copy()
                transition.start(from_surface, to_surface)
                self._transition = transition
                return

        pygame.event.clear()
        self._previous_name = self._current_name
        self._current_name = name
        self.current_screen = self._screens[name]

    def _finish_transition(self) -> None:
        if self._transition is not None:
            self._transition.render(self.surface)
            pygame.display.flip()
        self._transition = None
        pygame.event.clear()

    @property
    def current_name(self) -> Optional[str]:
        return self._current_name

    @property
    def previous_name(self) -> Optional[str]:
        return self._previous_name

    def _apply_transition_guard(self, name: str) -> str:
        if self._transition_guard is None:
            return name
        guarded_name = self._transition_guard(name)
        if guarded_name != name:
            log.debug(f"Transition guarded: {name} -> {guarded_name}")
        return guarded_name

    def run(self) -> None:
        if self.current_screen is None:
            raise RuntimeError("Cannot run ScreenManager without an active screen.")

        log.info("Game loop started")
        self._running = True
        while self._running:
            delta_time = self.clock.tick(SETTINGS.DISPLAY.FPS) / 1000.0

            if not self.is_transitioning:
                events = pygame.event.get()

                next_screen = self.current_screen.handle_events(events)
                if next_screen == SETTINGS.SCREEN_NAMES.QUIT:
                    self._running = False
                    break
                if next_screen is not None:
                    self.switch_to(next_screen)

                if self.current_screen is None:
                    continue

                next_screen = self.current_screen.update(delta_time)
                if next_screen == SETTINGS.SCREEN_NAMES.QUIT:
                    self._running = False
                    break
                if next_screen is not None:
                    self.switch_to(next_screen)

            if self.is_transitioning and self._transition is not None:
                if self._transition.update(delta_time):
                    self._finish_transition()
                else:
                    self._transition.render(self.surface)
                    pygame.display.flip()
                    continue

            self.current_screen.render(self.surface)
            pygame.display.flip()
        
        log.info("Game loop stopped")
    
    def distribute_assets(self, assets) -> None:
        log.debug(f"Assets distributed to {len(self._screens)} screens")
        for screen in self._screens.values():
            if hasattr(screen, 'assets'):
                screen.assets = assets
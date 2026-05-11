from abc import ABC, abstractmethod
from typing import List, Optional

import pygame


class Screen(ABC):
    @abstractmethod
    def handle_events(self, events: List[pygame.event.Event]) -> Optional[str]:
        """Process input and optionally return the next screen name."""

    @abstractmethod
    def update(self, delta_time: float) -> None:
        """Update screen-specific logic."""

    @abstractmethod
    def render(self, surface: pygame.Surface) -> None:
        """Draw the screen."""

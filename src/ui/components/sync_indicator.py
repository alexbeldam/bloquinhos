import math
from enum import Enum
from typing import Callable, Optional

import pygame

from settings import SETTINGS


class SyncIndicatorStatus(Enum):
    IDLE = "idle"
    SYNCING = "syncing"
    SUCCESS = "success"
    OFFLINE = "offline"
    ERROR = "error"


class SyncIndicator:
    def __init__(self, font_renderer: Callable[[int], pygame.font.Font]) -> None:
        self._font_renderer = font_renderer
        self._status = SyncIndicatorStatus.IDLE
        self._message = ""
        self._animation_time = 0.0
        self._display_duration = 0.0
        self._auto_hide = False

    def set_syncing(self) -> None:
        self._status = SyncIndicatorStatus.SYNCING
        self._message = "Sincronizando..."
        self._animation_time = 0.0
        self._auto_hide = False

    def set_success(self, duration: float = 2.0) -> None:
        self._status = SyncIndicatorStatus.SUCCESS
        self._message = "Sincronizado"
        self._animation_time = 0.0
        self._display_duration = duration
        self._auto_hide = duration > 0

    def set_offline(self, duration: float = 0.0) -> None:
        self._status = SyncIndicatorStatus.OFFLINE
        self._message = "Offline"
        self._animation_time = 0.0
        self._display_duration = duration
        self._auto_hide = duration > 0

    def set_error(self, message: str = "Erro ao sincronizar", duration: float = 3.0) -> None:
        self._status = SyncIndicatorStatus.ERROR
        self._message = message
        self._animation_time = 0.0
        self._display_duration = duration
        self._auto_hide = duration > 0

    def set_idle(self) -> None:
        self._status = SyncIndicatorStatus.IDLE

    def is_visible(self) -> bool:
        return self._status != SyncIndicatorStatus.IDLE

    def update(self, delta_time: float) -> None:
        if not self.is_visible():
            return

        self._animation_time += delta_time

        if self._auto_hide and self._animation_time >= self._display_duration:
            self.set_idle()

    def render(
        self,
        surface: pygame.Surface,
        position: tuple[int, int],
        width: int = 260,
    ) -> None:
        if not self.is_visible():
            return

        x, y = position

        box_height = 50
        box_rect = pygame.Rect(x - width // 2, y - box_height // 2, width, box_height)
        pygame.draw.rect(
            surface,
            SETTINGS.UI_THEME.BG_DARK,
            box_rect,
            border_radius=8,
        )

        border_color = self._get_border_color()
        pygame.draw.rect(
            surface,
            border_color,
            box_rect,
            2,
            border_radius=8,
        )

        icon_color = self._get_icon_color()
        self._draw_icon(surface, x - 75, y, icon_color)

        font = self._font_renderer(SETTINGS.UI_TYPOGRAPHY.SMALL)
        message_surface = font.render(self._message, True, self._get_text_color())
        message_rect = message_surface.get_rect(center=(x + 30, y))
        surface.blit(message_surface, message_rect)

    def _draw_icon(self, surface: pygame.Surface, x: int, y: int, color: tuple) -> None:
        if self._status == SyncIndicatorStatus.SYNCING:
            self._draw_spinner(surface, x, y, color)
        elif self._status == SyncIndicatorStatus.SUCCESS:
            self._draw_checkmark(surface, x, y, color)
        elif self._status == SyncIndicatorStatus.OFFLINE:
            self._draw_offline_icon(surface, x, y, color)
        elif self._status == SyncIndicatorStatus.ERROR:
            self._draw_error_icon(surface, x, y, color)

    def _draw_spinner(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        color: tuple,
        radius: int = 8,
    ) -> None:
        angle = (self._animation_time * 360) % 360
        angle_rad = math.radians(angle)

        dot_x = x + radius * math.cos(angle_rad)
        dot_y = y + radius * math.sin(angle_rad)
        pygame.draw.circle(surface, color, (int(dot_x), int(dot_y)), 3)

        light_color = tuple(min(c + 50, 255) for c in color)
        pygame.draw.circle(surface, light_color, (x, y), radius, 2)

    def _draw_checkmark(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        color: tuple,
    ) -> None:
        points = [
            (x - 5, y),
            (x - 1, y + 5),
            (x + 6, y - 4),
        ]
        pygame.draw.lines(surface, color, True, points, 3)

    def _draw_offline_icon(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        color: tuple,
    ) -> None:
        pygame.draw.polygon(
            surface,
            color,
            [
                (x - 5, y + 3),
                (x, y - 5),
                (x + 5, y + 3),
            ],
        )
        pygame.draw.line(surface, color, (x - 8, y + 6), (x + 8, y - 6), 2)

    def _draw_error_icon(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        color: tuple,
    ) -> None:
        pygame.draw.line(surface, color, (x - 5, y - 5), (x + 5, y + 5), 2)
        pygame.draw.line(surface, color, (x + 5, y - 5), (x - 5, y + 5), 2)

    def _get_border_color(self) -> tuple:
        match self._status:
            case SyncIndicatorStatus.SYNCING:
                return SETTINGS.UI_THEME.CYAN
            case SyncIndicatorStatus.SUCCESS:
                return SETTINGS.UI_THEME.GREEN
            case SyncIndicatorStatus.OFFLINE:
                return SETTINGS.UI_THEME.YELLOW
            case SyncIndicatorStatus.ERROR:
                return SETTINGS.UI_THEME.RED
            case _:
                return SETTINGS.UI_THEME.TEXT_MUTED

    def _get_icon_color(self) -> tuple:
        return self._get_border_color()

    def _get_text_color(self) -> tuple:
        match self._status:
            case SyncIndicatorStatus.SYNCING:
                return SETTINGS.UI_THEME.CYAN
            case SyncIndicatorStatus.SUCCESS:
                return SETTINGS.UI_THEME.GREEN
            case SyncIndicatorStatus.OFFLINE:
                return SETTINGS.UI_THEME.YELLOW
            case SyncIndicatorStatus.ERROR:
                return SETTINGS.UI_THEME.RED
            case _:
                return SETTINGS.UI_THEME.TEXT_PRIMARY
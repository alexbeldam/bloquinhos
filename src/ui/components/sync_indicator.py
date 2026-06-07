import math
from enum import Enum
from typing import Callable, Optional, TYPE_CHECKING

import pygame

from settings import SETTINGS
from utils.localization import tr

if TYPE_CHECKING:
    from ui.assets import AssetManager


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
        self._message = tr("sync.syncing")
        self._animation_time = 0.0
        self._auto_hide = False

    def set_success(self, duration: float = 2.0) -> None:
        self._status = SyncIndicatorStatus.SUCCESS
        self._message = tr("sync.success")
        self._animation_time = 0.0
        self._display_duration = duration
        self._auto_hide = duration > 0

    def set_offline(self, duration: float = 0.0) -> None:
        self._status = SyncIndicatorStatus.OFFLINE
        self._message = tr("sync.offline")
        self._animation_time = 0.0
        self._display_duration = duration
        self._auto_hide = duration > 0

    def set_error(self, message: str = "", duration: float = 3.0) -> None:
        self._status = SyncIndicatorStatus.ERROR
        self._message = message or tr("sync.error")
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
        assets: Optional["AssetManager"] = None
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

        self._draw_icon(surface, x - 75, y, assets)

        font = self._font_renderer(SETTINGS.UI_TYPOGRAPHY.SMALL)
        message_surface = font.render(self._message, True, self._get_text_color())
        message_rect = message_surface.get_rect(center=(x + 30, y))
        surface.blit(message_surface, message_rect)

    def _try_load_icon(self, icon_name: str, assets: "AssetManager") -> Optional[pygame.Surface]:
        try:
            return assets.get_image(icon_name)
        except (KeyError, FileNotFoundError):
            return None

    def _draw_icon(
        self, 
        surface: pygame.Surface, 
        x: int, 
        y: int, 
        assets: Optional["AssetManager"]
    ) -> None:
        if not assets:
            return

        icon_name = self._get_icon_name()
        icon = self._try_load_icon(icon_name, assets)

        icon_scaled = pygame.transform.scale(icon, (24, 24))

        if self._status == SyncIndicatorStatus.SYNCING:
            angle = -(self._animation_time * 360) % 360
            rotated_icon = pygame.transform.rotate(icon_scaled, angle)
            icon_rect = rotated_icon.get_rect(center=(x, y))
            surface.blit(rotated_icon, icon_rect)
        else:
            icon_rect = icon_scaled.get_rect(center=(x, y))
            surface.blit(icon_scaled, icon_rect)

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

    def _get_icon_name(self) -> str:
        match self._status:
            case SyncIndicatorStatus.SYNCING:
                return "retry"
            case SyncIndicatorStatus.SUCCESS:
                return "check"
            case SyncIndicatorStatus.OFFLINE:
                return "signal-disabled"
            case SyncIndicatorStatus.ERROR:
                return "cancel"
            case _:
                return ""

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
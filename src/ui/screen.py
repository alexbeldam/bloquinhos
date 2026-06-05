from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, TYPE_CHECKING

import pygame

from settings import SETTINGS
from ui.assets import AssetManager
from ui.styles import SETTINGS_STYLE
from utils.localization import tr

if TYPE_CHECKING:
    from network.connection_manager import ConnectionStatusSnapshot, NetworkManager
    from ui.audio import AudioManager


Color = Tuple[int, int, int]


class Screen(ABC):
    NETWORK_ICON_SIZE = 20
    NETWORK_ICON_GAP = 10
    NETWORK_MARGIN = 14

    def __init__(self, assets: Optional[AssetManager] = None, audio_manager: Optional["AudioManager"] = None) -> None:
        self.assets = assets
        self.audio_manager = audio_manager
        self._network_manager: Optional["NetworkManager"] = None
        self._network_retry_hitbox: Optional[pygame.Rect] = None
        self._network_status_hitbox: Optional[pygame.Rect] = None

    @abstractmethod
    def handle_events(self, events: List[pygame.event.Event]) -> Optional[str]:
        """Process input and optionally return the next screen name."""

    @abstractmethod
    def update(self, delta_time: float) -> Optional[str]:
        """Update screen-specific logic and optionally return the next screen name."""

    @abstractmethod
    def render(self, surface: pygame.Surface) -> None:
        """Draw the screen."""

    def _font(self, size: int) -> pygame.font.Font:
        if self.assets is not None:
            try:
                return self.assets.get_font(size)
            except (KeyError, FileNotFoundError, pygame.error):
                pass
        return pygame.font.Font(None, size)

    def _draw_text(
        self,
        surface: pygame.Surface,
        text: str,
        size: int,
        color: Color,
        center: Tuple[int, int],
    ) -> None:
        rendered = self._render_text_surface(text, size, color)
        surface.blit(rendered, rendered.get_rect(center=center))

    def _render_text_surface(self, text: str, size: int, color: Color) -> pygame.Surface:
        return self._font(size).render(text, SETTINGS.UI_TYPOGRAPHY.ANTIALIAS, color)
    
    def _draw_wrapped_text(
        self,
        surface: pygame.Surface,
        text: str,
        size: int,
        color: Color,
        center: Tuple[int, int],
        max_width: int,
        line_spacing: int = 5,
    ) -> None:
        font = self._font(size)
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_width = font.size(test_line)[0]
            
            if test_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        line_height = font.get_height() + line_spacing
        total_height = len(lines) * line_height - line_spacing
        start_y = center[1] - total_height // 2
        
        for i, line in enumerate(lines):
            rendered = self._render_text_surface(line, size, color)
            line_rect = rendered.get_rect(center=(center[0], start_y + i * line_height))
            surface.blit(rendered, line_rect)
    
    def _try_load_image(self, image_name: str) -> Optional[pygame.Surface]:
        if self.assets is not None:
            try:
                return self.assets.get_image(image_name)
            except (KeyError, FileNotFoundError, pygame.error):
                pass
        return None

    def bind_network_manager(self, network_manager: Optional["NetworkManager"]) -> None:
        self._network_manager = network_manager

    def _handle_network_status_event(
        self,
        event: pygame.event.Event,
        enabled: bool = True,
    ) -> bool:
        if not enabled or self._network_manager is None:
            return False

        snapshot = self._network_manager.get_status_snapshot()
        if not snapshot.can_retry:
            return False

        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self._network_manager.request_connection()
            return True

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self._network_retry_hitbox is not None
            and self._network_retry_hitbox.collidepoint(event.pos)
        ):
            self._network_manager.request_connection()
            return True

        return False

    def _render_network_status(
        self,
        surface: pygame.Surface,
        enabled: bool = True,
    ) -> None:
        if not enabled or self._network_manager is None:
            self._network_retry_hitbox = None
            self._network_status_hitbox = None
            return

        snapshot = self._network_manager.get_status_snapshot()
        content_width = self.NETWORK_ICON_SIZE
        if snapshot.can_retry:
            content_width += self.NETWORK_ICON_SIZE + self.NETWORK_ICON_GAP

        icon_y = self.NETWORK_MARGIN
        icon_x = surface.get_width() - content_width - self.NETWORK_MARGIN
        self._network_retry_hitbox = None
        self._network_status_hitbox = None

        if snapshot.can_retry:
            retry_rect = pygame.Rect(icon_x, icon_y, self.NETWORK_ICON_SIZE, self.NETWORK_ICON_SIZE)
            self._draw_network_icon(surface, retry_rect, "retry", snapshot)
            self._network_retry_hitbox = retry_rect.inflate(6, 6)
            icon_x += self.NETWORK_ICON_SIZE + self.NETWORK_ICON_GAP

        status_rect = pygame.Rect(icon_x, icon_y, self.NETWORK_ICON_SIZE, self.NETWORK_ICON_SIZE)
        self._draw_network_icon(surface, status_rect, self._network_icon_name(snapshot), snapshot)
        self._network_status_hitbox = status_rect.inflate(6, 6)

        self._render_network_tooltip(surface, snapshot)

    def _draw_network_icon(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        icon_name: str,
        snapshot: "ConnectionStatusSnapshot",
    ) -> None:
        icon = self._try_load_image(icon_name)
        if icon is not None:
            scaled_icon = pygame.transform.smoothscale(icon, rect.size)
            surface.blit(scaled_icon, rect)
            return

        self._draw_network_fallback(surface, rect, icon_name, snapshot)

    def _network_icon_name(self, snapshot: "ConnectionStatusSnapshot") -> str:
        if snapshot.is_online:
            return "signal-full"
        if snapshot.is_retrying:
            animation_frames = (
                "signal-off",
                "signal-low",
                "signal-medium",
                "signal-full",
                "signal-medium",
                "signal-low",
                "signal-off"
            )
            frame_index = (pygame.time.get_ticks() // 150) % len(animation_frames)
            return animation_frames[frame_index]
        return "signal-disabled"

    def _draw_network_fallback(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        icon_name: str,
        snapshot: "ConnectionStatusSnapshot",
    ) -> None:
        if icon_name == "retry":
            pygame.draw.circle(surface, SETTINGS.UI_THEME.YELLOW, rect.center, rect.width // 2, 2)
            tip = (rect.right - 2, rect.centery - 2)
            base_top = (rect.right - 8, rect.top + 3)
            base_bottom = (rect.right - 10, rect.top + 10)
            pygame.draw.polygon(surface, SETTINGS.UI_THEME.YELLOW, [tip, base_top, base_bottom])
            return

        color = SETTINGS.UI_THEME.RED
        if snapshot.is_online:
            color = SETTINGS.UI_THEME.GREEN
        elif snapshot.is_retrying:
            color = SETTINGS.UI_THEME.ORANGE

        pygame.draw.circle(surface, color, rect.center, rect.width // 2)

    def _render_network_tooltip(
        self,
        surface: pygame.Surface,
        snapshot: "ConnectionStatusSnapshot",
    ) -> None:
        mouse_pos = pygame.mouse.get_pos()
        tooltip: Optional[tuple[str, tuple[int, int]]] = None

        if self._network_retry_hitbox is not None and self._network_retry_hitbox.collidepoint(mouse_pos):
            tooltip = (tr("network.tooltip.reconnect"), mouse_pos)
        elif self._network_status_hitbox is not None and self._network_status_hitbox.collidepoint(mouse_pos):
            tooltip = (self._network_tooltip_text(snapshot), mouse_pos)

        if tooltip is None:
            return

        self._render_tooltip(surface, tooltip)

    def _network_tooltip_text(self, snapshot: "ConnectionStatusSnapshot") -> str:
        if snapshot.is_online:
            return tr("network.tooltip.online")
        if snapshot.is_retrying:
            return tr("network.tooltip.reconnecting")
        return tr("network.tooltip.offline")

    def _render_tooltip(
        self,
        surface: pygame.Surface,
        tooltip: tuple[str, tuple[int, int]],
    ) -> None:
        text, pos = tooltip
        text_surface = self._render_text_surface(
            text,
            SETTINGS.UI_TYPOGRAPHY.SMALL,
            SETTINGS.UI_THEME.TEXT_PRIMARY,
        )

        padding_x = 10
        padding_y = 6
        tooltip_width = text_surface.get_width() + padding_x * 2
        tooltip_height = text_surface.get_height() + padding_y * 2

        x = pos[0] + 14
        y = pos[1] - tooltip_height // 2

        if x + tooltip_width > surface.get_width() - 8:
            x = surface.get_width() - tooltip_width - 8
        if y < 8:
            y = 8
        if y + tooltip_height > surface.get_height() - 8:
            y = surface.get_height() - tooltip_height - 8

        tooltip_rect = pygame.Rect(x, y, tooltip_width, tooltip_height)
        pygame.draw.rect(surface, SETTINGS_STYLE.TOOLTIP_BG, tooltip_rect, border_radius=6)
        pygame.draw.rect(surface, SETTINGS.UI_THEME.TEXT_MUTED, tooltip_rect, width=1, border_radius=6)
        surface.blit(text_surface, (x + padding_x, y + padding_y))

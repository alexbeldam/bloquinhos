import re
from typing import Callable, List, Optional, TYPE_CHECKING

import pygame

from network import DataSynchronizer, SyncStatus
from security.identity_manager import IdentityManager, IdentityStatus
from settings import SETTINGS
from ui.assets import AssetManager
from ui.components.sync_indicator import SyncIndicator
from ui.screen import Screen
from utils.localization import tr
from utils.logger import log

if TYPE_CHECKING:
    from ui.audio import AudioManager


class IdentityEntryScreen(Screen):
    INPUT_HEIGHT = 46
    INPUT_MAX_WIDTH = 380
    INPUT_HORIZONTAL_MARGIN = 48

    def __init__(
        self,
        identity_manager: IdentityManager,
        synchronizer: Optional[DataSynchronizer] = None,
        reason_provider: Optional[Callable[[], str]] = None,
        return_screen_provider: Optional[Callable[[], str]] = None,
        assets: Optional[AssetManager] = None,
        audio_manager: Optional["AudioManager"] = None,
    ) -> None:
        super().__init__(assets, audio_manager)
        self.identity_manager = identity_manager
        self._synchronizer = synchronizer
        self._reason_provider = reason_provider or (lambda: IdentityStatus.MISSING.value)
        self._return_screen_provider = return_screen_provider or (
            lambda: SETTINGS.SCREEN_NAMES.MENU
        )
        self._text = ""
        self._error: Optional[str] = None
        self._sync_indicator = SyncIndicator(self._font)
        self._registering = False
        self._sync_result_handled = False
        self._input_focused = True

    def handle_events(self, events: List[pygame.event.Event]) -> Optional[str]:
        for event in events:
            if event.type == pygame.QUIT:
                return SETTINGS.SCREEN_NAMES.QUIT

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                input_rect = self._input_rect_for_surface(pygame.display.get_surface())
                self._input_focused = input_rect.collidepoint(event.pos)

            if self._handle_network_status_event(event, enabled=not self._input_focused or event.type == pygame.MOUSEBUTTONDOWN):
                continue

            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                return SETTINGS.SCREEN_NAMES.QUIT

            if not self._input_focused:
                continue

            if event.key == pygame.K_BACKSPACE:
                self._text = self._text[:-1]
                self._error = None
                continue
            if event.key == pygame.K_RETURN:
                if self._registering:
                    continue
                    
                if self.identity_manager.register_identity(self._text):
                    self._registering = True
                    self._sync_indicator.set_syncing()
                    return None
                self._error = tr("identity.error.invalid_name")
                continue

            if event.unicode and len(self._text) < 15:
                candidate = self._text + event.unicode
                if re.fullmatch(r"[A-Za-z0-9_]{0,15}", candidate):
                    self._text = candidate
                    self._error = None

        return None

    def update(self, delta_time: float) -> Optional[str]:
        self._sync_indicator.update(delta_time)
        
        if self._registering and not self._sync_result_handled:
            self._sync_result_handled = True
            self._trigger_sync(self._text)
        
        if self._registering and self._sync_indicator.is_visible() is False:
            self._registering = False
            return self._return_screen_provider()
        
        return None

    def _trigger_sync(self, name: str) -> None:
        if self._synchronizer is None:
            self._sync_indicator.set_idle()
            return
        
        try:
            result = self._synchronizer.sync(name)
            log.info("Sync result after registration: %s — %s", result.status.name, result.message)
            
            if result.status == SyncStatus.SUCCESS:
                self._sync_indicator.set_success(duration=1.5)
            elif result.status == SyncStatus.OFFLINE:
                self._sync_indicator.set_offline(duration=1.5)
            elif result.status == SyncStatus.FAILURE:
                self._sync_indicator.set_error(result.message, duration=2.0)
            else:  
                self._sync_indicator.set_idle()
        except Exception as exc:
            log.error("Sync after registration failed", exc_info=True)
            self._sync_indicator.set_error(tr("game_over.unknown_error"), duration=2.0)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(SETTINGS.UI_THEME.BG_DARK)
        center_x = surface.get_width() // 2
        center_y = surface.get_height() // 2
        copy = self._copy_for_reason()

        self._draw_text(
            surface,
            copy["title"],
            SETTINGS.UI_TYPOGRAPHY.TITLE,
            SETTINGS.UI_THEME.TEXT_PRIMARY,
            (center_x, center_y - 105),
        )
        self._draw_text(
            surface,
            copy["help"],
            SETTINGS.UI_TYPOGRAPHY.SMALL,
            SETTINGS.UI_THEME.TEXT_MUTED,
            (center_x, center_y - 65),
        )

        input_rect = self._input_rect_for_surface(surface)
        pygame.draw.rect(surface, SETTINGS.UI_THEME.BG_MEDIUM, input_rect, border_radius=6)
        border_color = SETTINGS.UI_THEME.PURPLE if self._input_focused else SETTINGS.UI_THEME.TEXT_MUTED
        pygame.draw.rect(surface, border_color, input_rect, 2, border_radius=6)

        display_text = self._text or "_"
        rendered_input = self._font(SETTINGS.UI_TYPOGRAPHY.BODY).render(
            display_text,
            SETTINGS.UI_TYPOGRAPHY.ANTIALIAS,
            SETTINGS.UI_THEME.YELLOW,
        )
        surface.blit(rendered_input, rendered_input.get_rect(center=input_rect.center))

        if self._error:
            self._draw_wrapped_text(
                surface,
                self._error,
                SETTINGS.UI_TYPOGRAPHY.SMALL,
                SETTINGS.UI_THEME.RED,
                (center_x, center_y + 62),
                max_width=max(240, surface.get_width() - 48),
            )

        self._draw_text(
            surface,
            tr("identity.instruction"),
            SETTINGS.UI_TYPOGRAPHY.SMALL,
            SETTINGS.UI_THEME.TEXT_MUTED,
            (center_x, center_y + 105),
        )
        
        if self._registering:
            self._sync_indicator.render(surface, (center_x, surface.get_height() - 50), assets=self.assets)
        
        self._render_network_status(surface)

    def _input_rect_for_surface(self, surface: Optional[pygame.Surface]) -> pygame.Rect:
        surface_width = SETTINGS.GRID.GAME_WIDTH + SETTINGS.GRID.SIDEBAR_WIDTH
        surface_height = SETTINGS.GRID.GAME_HEIGHT
        if surface is not None:
            surface_width = surface.get_width()
            surface_height = surface.get_height()

        input_width = min(self.INPUT_MAX_WIDTH, surface_width - self.INPUT_HORIZONTAL_MARGIN)
        input_rect = pygame.Rect(0, 0, input_width, self.INPUT_HEIGHT)
        input_rect.center = (surface_width // 2, surface_height // 2)
        return input_rect

    def _copy_for_reason(self) -> dict[str, str]:
        reason = self._reason_provider()
        if reason == IdentityStatus.CONFLICT.value:
            return {
                "title": tr("identity.title.conflict"),
                "help": tr("identity.help.conflict"),
            }
        if reason == IdentityStatus.CORRUPTED.value:
            return {
                "title": tr("identity.title.corrupted"),
                "help": tr("identity.help.corrupted"),
            }
        return {
            "title": tr("identity.title.default"),
            "help": tr("identity.help.default"),
        }


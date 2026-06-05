from typing import List, Optional, TYPE_CHECKING
import time

import pygame

from settings import SETTINGS
from ui.assets import AssetManager
from ui.screen import Screen
from utils.localization import format_int, tr

if TYPE_CHECKING:
    from network.connection_manager import NetworkManager, ConnectionStatusSnapshot
    from network.leaderboard_manager import LeaderboardEntry, LeaderboardManager, LeaderboardSnapshot, UserRecord
    from ui.audio import AudioManager


class RankingScreen(Screen):
    def __init__(
        self,
        leaderboard_manager: Optional["LeaderboardManager"] = None,
        assets: Optional[AssetManager] = None,
        audio_manager: Optional["AudioManager"] = None,
    ) -> None:
        super().__init__(assets, audio_manager)
        self.leaderboard_manager = leaderboard_manager
        self._cached_snapshot: Optional["LeaderboardSnapshot"] = None
        self._last_snapshot_fetch_time = 0.0
        self._listener_registered = False
        self._refresh_requested = False

    def bind_network_manager(self, network_manager: Optional["NetworkManager"]) -> None:
        super().bind_network_manager(network_manager)
        if network_manager is not None and not self._listener_registered:
            network_manager.add_status_listener(self._on_status_changed)
            self._listener_registered = True

    def on_enter(self) -> None:
        """Called when entering ranking screen."""
        if self.audio_manager:
            self.audio_manager.play_sfx("open")

    def on_exit(self) -> None:
        """Called when leaving ranking screen."""
        pass

    def _on_status_changed(self, snapshot: "ConnectionStatusSnapshot") -> None:
        if snapshot.is_online:
            self._refresh_requested = True

    def handle_events(self, events: List[pygame.event.Event]) -> Optional[str]:
        for event in events:
            if event.type == pygame.QUIT:
                return SETTINGS.SCREEN_NAMES.QUIT
            if self._handle_network_status_event(event):
                self._refresh_requested = True
                continue
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_ESCAPE,
                pygame.K_RETURN,
                pygame.K_SPACE,
            ):
                if self.audio_manager:
                    self.audio_manager.play_sfx("cancel")
                return SETTINGS.SCREEN_NAMES.MENU
        return None

    def update(self, _delta_time: float) -> Optional[str]:
        current_time = time.time()
        force_refresh = self._refresh_requested

        if force_refresh:
            self._refresh_requested = False
            self._last_snapshot_fetch_time = 0.0

        if (
            self.leaderboard_manager is not None
            and (
                self._cached_snapshot is None
                or current_time - self._last_snapshot_fetch_time >= SETTINGS.NETWORK.LEADERBOARD_CACHE_DURATION
            )
        ):
            cached_user_name = None
            if self._cached_snapshot is not None and self._cached_snapshot.local_record is not None:
                cached_user_name = self._cached_snapshot.local_record.name

            self._cached_snapshot = self.leaderboard_manager.get_snapshot(
                user_name=cached_user_name,
                force_refresh=force_refresh,
            )
            self._last_snapshot_fetch_time = current_time
        
        return None

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(SETTINGS.UI_THEME.BG_MEDIUM)
        
        self._draw_text(
            surface,
            tr("ranking.title"),
            SETTINGS.UI_TYPOGRAPHY.DISPLAY,
            SETTINGS.UI_THEME.TEXT_PRIMARY,
            (surface.get_width() // 2, 80),
        )
        
        center_x = surface.get_width() // 2
        content_y = 150

        snapshot = self._cached_snapshot if self.leaderboard_manager else None
        entries = snapshot.top_entries if snapshot is not None else None
        local_record = snapshot.local_record if snapshot is not None else None

        if self.leaderboard_manager:
            if entries is None:
                self._render_unavailable_message(surface, center_x, content_y)
                content_y += 180
            elif entries:
                self._render_rankings(surface, entries, center_x, content_y)
                content_y += 280
            else:
                self._render_no_records_message(surface, center_x, content_y)
                content_y += 200
        else:
            self._render_unavailable_message(surface, center_x, content_y)
            content_y += 180
        
        if local_record is not None:
            self._render_local_record(
                surface,
                local_record,
                center_x,
                content_y
            )
        
        self._render_network_status(surface)

    def _render_rankings(
        self,
        surface: pygame.Surface,
        entries: List["LeaderboardEntry"],
        center_x: int,
        start_y: int,
    ) -> None:
        title_y = start_y
        self._draw_text(
            surface,
            tr("ranking.top_five"),
            SETTINGS.UI_TYPOGRAPHY.TITLE,
            SETTINGS.UI_THEME.YELLOW,
            (center_x, title_y),
        )
        
        entry_y = title_y + 50
        item_spacing = 40
        
        for entry in entries:
            rank_text = f"#{format_int(entry.rank)}"
            name_text = self._display_name(entry.name)
            score_text = format_int(entry.score)
            
            self._draw_text(
                surface,
                rank_text,
                SETTINGS.UI_TYPOGRAPHY.BODY,
                SETTINGS.UI_THEME.PURPLE,
                (center_x - 180, entry_y),
            )
            
            self._draw_text(
                surface,
                name_text,
                SETTINGS.UI_TYPOGRAPHY.BODY,
                SETTINGS.UI_THEME.TEXT_PRIMARY,
                (center_x - 30, entry_y),
            )
            
            self._draw_text(
                surface,
                score_text,
                SETTINGS.UI_TYPOGRAPHY.BODY,
                SETTINGS.UI_THEME.TEXT_PRIMARY,
                (center_x + 150, entry_y),
            )
            
            entry_y += item_spacing

    def _render_unavailable_message(
        self,
        surface: pygame.Surface,
        center_x: int,
        start_y: int,
    ) -> None:
        self._draw_text(
            surface,
            tr("ranking.offline.title"),
            SETTINGS.UI_TYPOGRAPHY.LARGE,
            SETTINGS.UI_THEME.PURPLE,
            (center_x, start_y + 40),
        )
        
        self._draw_text(
            surface,
            tr("ranking.offline.subtitle"),
            SETTINGS.UI_TYPOGRAPHY.BODY,
            SETTINGS.UI_THEME.TEXT_MUTED,
            (center_x, start_y + 100),
        )

    def _render_no_records_message(
        self,
        surface: pygame.Surface,
        center_x: int,
        start_y: int,
    ) -> None:
        self._draw_text(
            surface,
            "Ainda sem registros",
            SETTINGS.UI_TYPOGRAPHY.LARGE,
            SETTINGS.UI_THEME.PURPLE,
            (center_x, start_y + 80),
        )

    def _render_local_record(
        self,
        surface: pygame.Surface,
        record: "UserRecord",
        center_x: int,
        start_y: int,
    ) -> None:
        self._draw_text(
            surface,
            tr("ranking.local_best"),
            SETTINGS.UI_TYPOGRAPHY.TITLE,
            SETTINGS.UI_THEME.YELLOW,
            (center_x, start_y),
        )
        
        name = record.name
        score = record.score
        score_text = format_int(score)
        rank = record.rank
        
        record_text = tr("ranking.local_record", name=name, score=score_text)
        if rank is not None:
            record_text = tr(
                "ranking.local_record_with_rank",
                name=name,
                score=score_text,
                rank=format_int(rank),
            )
        
        self._draw_text(
            surface,
            record_text,
            SETTINGS.UI_TYPOGRAPHY.BODY,
            SETTINGS.UI_THEME.TEXT_PRIMARY,
            (center_x, start_y + 50),
        )

    @staticmethod
    def _display_name(name: object) -> str:
        if isinstance(name, str) and name.strip():
            return name[:15]
        return tr("ranking.unknown_player")
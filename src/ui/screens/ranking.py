from typing import List, Optional, TYPE_CHECKING
import time

import pygame

from settings import SETTINGS
from ui.assets import AssetManager
from ui.screen import Screen

if TYPE_CHECKING:
    from network.leaderboard_manager import LeaderboardManager
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
        self._last_fetch_time = 0.0
        self._cached_entries = None
        self._cached_local_record = None

    def handle_events(self, events: List[pygame.event.Event]) -> Optional[str]:
        for event in events:
            if event.type == pygame.QUIT:
                return SETTINGS.SCREEN_NAMES.QUIT
            if self._handle_network_status_event(event):
                self._last_fetch_time = 0.0
                continue
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_ESCAPE,
                pygame.K_RETURN,
                pygame.K_SPACE,
            ):
                return SETTINGS.SCREEN_NAMES.MENU
        return None

    def update(self, delta_time: float) -> Optional[str]:
        if self.audio_manager:
            self.audio_manager.play_bgm("menu")
        
        current_time = time.time()
        if current_time - self._last_fetch_time >= SETTINGS.NETWORK.LEADERBOARD_CACHE_DURATION:
            self._fetch_data()
            self._last_fetch_time = current_time
        
        return None

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(SETTINGS.UI_THEME.BG_MEDIUM)
        
        self._draw_text(
            surface,
            "RANKING GLOBAL",
            SETTINGS.UI_TYPOGRAPHY.DISPLAY,
            SETTINGS.UI_THEME.TEXT_PRIMARY,
            (surface.get_width() // 2, 80),
        )
        
        center_x = surface.get_width() // 2
        content_y = 150
        
        if self.leaderboard_manager and self.leaderboard_manager.network.is_online:
            if self._cached_entries:
                self._render_rankings(surface, self._cached_entries, center_x, content_y)
                content_y += 280
            else:
                self._draw_text(
                    surface,
                    "Ainda sem registros",
                    SETTINGS.UI_TYPOGRAPHY.LARGE,
                    SETTINGS.UI_THEME.PURPLE,
                    (center_x, content_y + 80),
                )
                content_y += 200
        else:
            self._render_offline_message(surface, center_x, content_y)
            content_y += 180
        
        if self._cached_local_record:
            self._render_local_record(
                surface,
                self._cached_local_record,
                center_x,
                content_y
            )
        
        self._render_network_status(surface)

    def _fetch_data(self) -> None:
        if not self.leaderboard_manager:
            return
        
        if self.leaderboard_manager.network.is_online:
            self._cached_entries = self.leaderboard_manager.get_top_5()
        else:
            self._cached_entries = None
        
        self._cached_local_record = self.leaderboard_manager.get_local_record()

    def _render_rankings(
        self,
        surface: pygame.Surface,
        entries,
        center_x: int,
        start_y: int,
    ) -> None:
        title_y = start_y
        self._draw_text(
            surface,
            "TOP 5",
            SETTINGS.UI_TYPOGRAPHY.TITLE,
            SETTINGS.UI_THEME.YELLOW,
            (center_x, title_y),
        )
        
        entry_y = title_y + 50
        item_spacing = 40
        
        for entry in entries:
            rank_text = f"#{entry.rank}"
            name_text = entry.name[:15]
            score_text = self._format_score(entry.score)
            
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

    def _render_offline_message(
        self,
        surface: pygame.Surface,
        center_x: int,
        start_y: int,
    ) -> None:
        self._draw_text(
            surface,
            "Sem conexão com servidor",
            SETTINGS.UI_TYPOGRAPHY.LARGE,
            SETTINGS.UI_THEME.PURPLE,
            (center_x, start_y + 40),
        )
        
        self._draw_text(
            surface,
            "Ranking indisponível",
            SETTINGS.UI_TYPOGRAPHY.BODY,
            SETTINGS.UI_THEME.TEXT_MUTED,
            (center_x, start_y + 100),
        )

    def _render_local_record(
        self,
        surface: pygame.Surface,
        record: dict,
        center_x: int,
        start_y: int,
    ) -> None:
        self._draw_text(
            surface,
            "SEU MELHOR",
            SETTINGS.UI_TYPOGRAPHY.TITLE,
            SETTINGS.UI_THEME.YELLOW,
            (center_x, start_y),
        )
        
        name = record.get("name", "Desconhecido")
        score = record.get("score", 0)
        score_text = self._format_score(score)
        
        rank = None
        if self.leaderboard_manager and self.leaderboard_manager.network.is_online:
            rank = self.leaderboard_manager.get_user_rank(name)
        
        record_text = f"{name}: {score_text}"
        if rank:
            record_text += f" (Rank #{rank})"
        
        self._draw_text(
            surface,
            record_text,
            SETTINGS.UI_TYPOGRAPHY.BODY,
            SETTINGS.UI_THEME.TEXT_PRIMARY,
            (center_x, start_y + 50),
        )

    @staticmethod
    def _format_score(score: int) -> str:
        return f"{score:,}".replace(",", ".")

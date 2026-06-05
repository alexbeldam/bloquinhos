from typing import List, Optional, TYPE_CHECKING

import pygame

from network import DataSynchronizer, SyncStatus
from network.leaderboard_manager import LeaderboardManager
from network.user_data_dao import UserDataDAO
from settings import SETTINGS
from ui.assets import AssetManager
from ui.components.sync_indicator import SyncIndicator
from ui.screen import Screen
from ui.screens.game import GameScreen
from utils.localization import format_int, tr
from utils.logger import log

if TYPE_CHECKING:
    from ui.audio import AudioManager


class GameOverScreen(Screen):
    PANEL_WIDTH = 460
    PANEL_MAX_WIDTH_RATIO = 0.85

    def __init__(
        self,
        game_screen: GameScreen,
        leaderboard_manager: Optional[LeaderboardManager] = None,
        synchronizer: Optional[DataSynchronizer] = None,
        assets: Optional[AssetManager] = None,
        audio_manager: Optional["AudioManager"] = None,
    ) -> None:
        super().__init__(assets, audio_manager)
        self.game_screen = game_screen
        self.user_data_dao = UserDataDAO()
        self._leaderboard_manager = leaderboard_manager
        self._synchronizer = synchronizer
        self._save_attempted = False
        self._new_high_score = False
        self._personal_best: Optional[int] = None
        self._rank_position: Optional[int] = None
        self._selected_option = 0
        self._sync_indicator = SyncIndicator(self._font)

    def handle_events(self, events: List[pygame.event.Event]) -> Optional[str]:
        for event in events:
            if event.type == pygame.QUIT:
                return SETTINGS.SCREEN_NAMES.QUIT

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._reset_state()
                    return SETTINGS.SCREEN_NAMES.MENU

                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self._selected_option = (self._selected_option - 1) % 2
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self._selected_option = (self._selected_option + 1) % 2
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self._selected_option == 0:
                        self._reset_state()
                        return SETTINGS.SCREEN_NAMES.GAME
                    else:
                        self._reset_state()
                        return SETTINGS.SCREEN_NAMES.MENU

        return None

    def _reset_state(self) -> None:
        self.game_screen.session.reset()
        self._save_attempted = False
        self._sync_indicator.set_idle()
        self._selected_option = 0
        self._new_high_score = False
        self._personal_best = None
        self._rank_position = None

    def update(self, delta_time: float) -> Optional[str]:
        self._sync_indicator.update(delta_time)

        if not self._save_attempted:
            self._save_attempted = True
            self._evaluate_results()
            try:
                name = self.user_data_dao.load_name()
                if name:
                    self.user_data_dao.save(self.game_screen.session, name)
                    self._trigger_sync(name)
            except Exception:
                log.error("Failed to save game over user data", exc_info=True)
        return None

    def _evaluate_results(self) -> None:
        self._new_high_score = False
        self._rank_position = None

        session = self.game_screen.session
        high_score_data = self.user_data_dao.load()

        if high_score_data:
            self._personal_best = high_score_data.get("score", 0)
        else:
            self._personal_best = None

        if self._personal_best is None or session.score > self._personal_best:
            self._new_high_score = True

    def _trigger_sync(self, name: str) -> None:
        should_submit_score = self._synchronizer is None

        if self._synchronizer is not None:
            self._sync_indicator.set_syncing()

            try:
                result = self._synchronizer.sync(name)
                log.info("Sync result: %s — %s", result.status.name, result.message)

                if result.status == SyncStatus.SUCCESS:
                    self._sync_indicator.set_success(duration=2.0)
                    should_submit_score = False
                elif result.status == SyncStatus.OFFLINE:
                    self._sync_indicator.set_offline(duration=2.0)
                    should_submit_score = True
                elif result.status == SyncStatus.FAILURE:
                    self._sync_indicator.set_error(result.message, duration=3.0)
                    should_submit_score = True
                else:
                    self._sync_indicator.set_idle()
                    should_submit_score = False
            except Exception:
                log.error("Sync after game over failed", exc_info=True)
                self._sync_indicator.set_error(tr("game_over.unknown_error"), duration=3.0)
                should_submit_score = True

        if should_submit_score:
            self._submit_score_for_rank(name)
            return

        if self._leaderboard_manager is not None:
            snapshot = self._leaderboard_manager.get_snapshot(name, force_refresh=True)
            self._rank_position = snapshot.local_record.rank if snapshot.local_record else None

    def _submit_score_for_rank(self, name: str) -> None:
        if self._leaderboard_manager is None:
            return
        
        session = self.game_screen.session
        self._leaderboard_manager.submit_score(name, session.score, session.total_lines, session.level)
        
        snapshot = self._leaderboard_manager.get_snapshot(name)
        self._rank_position = snapshot.local_record.rank if snapshot.local_record else None

    def render(self, surface: pygame.Surface) -> None:
        self.game_screen.render(surface)

        w = surface.get_width()
        h = surface.get_height()
        cx = w // 2

        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        surface.blit(overlay, (0, 0))

        panel_w = min(self.PANEL_WIDTH, int(w * self.PANEL_MAX_WIDTH_RATIO))
        panel_h = int(h * 0.82)
        panel_x = cx - panel_w // 2
        panel_y = int(h * 0.09)

        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((15, 17, 23, 235))
        surface.blit(panel_surf, (panel_x, panel_y))
        pygame.draw.rect(
            surface,
            SETTINGS.UI_THEME.BG_LIGHT,
            (panel_x, panel_y, panel_w, panel_h),
            width=2,
            border_radius=14,
        )

        title_y = panel_y + 40
        self._draw_text(
            surface,
            tr("game_over.title"),
            SETTINGS.UI_TYPOGRAPHY.DISPLAY,
            SETTINGS.UI_THEME.RED,
            (cx, title_y),
        )

        sep1_y = title_y + 50
        pygame.draw.line(
            surface,
            SETTINGS.UI_THEME.BG_LIGHT,
            (cx - 110, sep1_y),
            (cx + 110, sep1_y),
            2,
        )

        score_y = sep1_y + 60
        score_text = format_int(self.game_screen.session.score)
        score_surf = self._render_text_surface(
            score_text,
            SETTINGS.UI_TYPOGRAPHY.DISPLAY + 24,
            SETTINGS.UI_THEME.YELLOW,
        )
        score_rect = score_surf.get_rect(center=(cx, score_y))
        score_shadow = self._render_text_surface(
            score_text,
            SETTINGS.UI_TYPOGRAPHY.DISPLAY + 24,
            (0, 0, 0),
        )
        surface.blit(score_shadow, (score_rect.x + 3, score_rect.y + 3))
        surface.blit(score_surf, score_rect)

        cur_y = score_y + 42

        if self._new_high_score:
            new_high_score_text = tr("game_over.new_high_score")
            hs_surf = self._render_text_surface(
                new_high_score_text,
                SETTINGS.UI_TYPOGRAPHY.LARGE,
                SETTINGS.UI_THEME.GREEN,
            )
            hs_rect = hs_surf.get_rect(center=(cx, cur_y))
            for dx, dy in [(1, 1), (-1, -1), (1, -1), (-1, 1)]:
                surface.blit(
                    self._render_text_surface(
                        new_high_score_text,
                        SETTINGS.UI_TYPOGRAPHY.LARGE,
                        (255, 255, 255, 30),
                    ),
                    (hs_rect.x + dx, hs_rect.y + dy),
                )
            surface.blit(hs_surf, hs_rect)
            cur_y += 35

        if self._personal_best is not None:
            if self._new_high_score:
                pb_label = tr("game_over.previous_high_score")
            else:
                pb_label = tr("game_over.high_score")
            self._draw_text(
                surface,
                f"{pb_label} {format_int(self._personal_best)}",
                SETTINGS.UI_TYPOGRAPHY.SMALL,
                SETTINGS.UI_THEME.TEXT_MUTED,
                (cx, cur_y),
            )
            cur_y += 30

        cur_y += 15

        sep2_y = cur_y
        pygame.draw.line(
            surface,
            SETTINGS.UI_THEME.BG_LIGHT,
            (cx - 120, sep2_y),
            (cx + 120, sep2_y),
            1,
        )
        cur_y += 18

        self._draw_text(
            surface,
            tr("game_over.statistics"),
            SETTINGS.UI_TYPOGRAPHY.BODY,
            SETTINGS.UI_THEME.CYAN,
            (cx, cur_y),
        )
        cur_y += 35

        stat_item_spacing = 24

        stat_row1 = [
            tr("game_over.stats.level", value=format_int(self.game_screen.session.level)),
            tr("game_over.stats.lines", value=format_int(self.game_screen.session.total_lines)),
        ]
        stat_row2a = [
            tr("game_over.stats.singles", value=format_int(self.game_screen.session.singles)),
            tr("game_over.stats.doubles", value=format_int(self.game_screen.session.doubles)),
        ]
        stat_row2b = [
            tr("game_over.stats.triples", value=format_int(self.game_screen.session.triples)),
            tr("game_over.stats.tetris", value=format_int(self.game_screen.session.tetris)),
        ]

        row1_y = cur_y
        cell_w2 = panel_w // 2
        for idx, item in enumerate(stat_row1):
            item_cx = panel_x + cell_w2 // 2 + idx * cell_w2
            self._draw_text(
                surface,
                item,
                SETTINGS.UI_TYPOGRAPHY.SMALL,
                SETTINGS.UI_THEME.TEXT_PRIMARY,
                (item_cx, row1_y),
            )
        cur_y += stat_item_spacing

        row2a_y = cur_y
        for idx, item in enumerate(stat_row2a):
            item_cx = panel_x + cell_w2 // 2 + idx * cell_w2
            self._draw_text(
                surface,
                item,
                SETTINGS.UI_TYPOGRAPHY.SMALL,
                SETTINGS.UI_THEME.TEXT_PRIMARY,
                (item_cx, row2a_y),
            )
        cur_y += stat_item_spacing

        row2b_y = cur_y
        for idx, item in enumerate(stat_row2b):
            item_cx = panel_x + cell_w2 // 2 + idx * cell_w2
            self._draw_text(
                surface,
                item,
                SETTINGS.UI_TYPOGRAPHY.SMALL,
                SETTINGS.UI_THEME.TEXT_PRIMARY,
                (item_cx, row2b_y),
            )
        cur_y += stat_item_spacing + 10

        sep3_y = cur_y
        pygame.draw.line(
            surface,
            SETTINGS.UI_THEME.BG_LIGHT,
            (cx - 130, sep3_y),
            (cx + 130, sep3_y),
            1,
        )
        cur_y = sep3_y + 20

        if self._rank_position is not None:
            self._draw_text(
                surface,
                tr("game_over.rank_position", rank=format_int(self._rank_position)),
                SETTINGS.UI_TYPOGRAPHY.BODY,
                SETTINGS.UI_THEME.PURPLE,
                (cx, cur_y),
            )
            cur_y += 45

        cur_y = panel_y + panel_h - 75

        icon_size = 48
        icon_gap = 30
        total_icons_w = 2 * icon_size + icon_gap
        icon_start_x = cx - total_icons_w // 2

        options = [
            ("retry", SETTINGS.SCREEN_NAMES.GAME),
            ("back", SETTINGS.SCREEN_NAMES.MENU),
        ]

        for i in range(2):
            is_selected = i == self._selected_option
            icon_name = options[i][0]
            bx = icon_start_x + i * (icon_size + icon_gap)
            by = cur_y

            icon = self._try_load_image(icon_name)
            if icon:
                icon_scaled = pygame.transform.scale(icon, (icon_size, icon_size))

                circle_radius = icon_size // 2 + 8
                circle_center = (bx + icon_size // 2, by + icon_size // 2)

                if is_selected:
                    pygame.draw.circle(
                        surface,
                        SETTINGS.UI_THEME.YELLOW,
                        circle_center,
                        circle_radius,
                        width=3,
                    )
                else:
                    pygame.draw.circle(
                        surface,
                        SETTINGS.UI_THEME.BG_LIGHT,
                        circle_center,
                        circle_radius,
                        width=2,
                    )

                surface.blit(icon_scaled, (bx, by))

        self._sync_indicator.render(surface, (cx, 40))
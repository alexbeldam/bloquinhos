from typing import Optional, Tuple, TYPE_CHECKING

import pygame

from engine import Board, GameController, GameSession, Tetromino, Tile
from engine.tile import Tetromino as TetrominoType
from settings import SETTINGS
from ui.assets import AssetManager
from ui.effects import EffectManager, ScreenShake
from ui.styles import GAME_STYLE
from utils.localization import format_int, tr

if TYPE_CHECKING:
    from utils.settings_manager import SettingsManager


Color = Tuple[int, int, int]


class GameRenderer:
    def __init__(
        self,
        screen: pygame.Surface,
        assets: Optional[AssetManager],
        controller: GameController,
        session: GameSession,
        settings_manager: Optional['SettingsManager'] = None,
    ) -> None:
        self.screen = screen
        self.assets = assets
        self.controller = controller
        self.session = session
        self.settings_manager = settings_manager
        self.effect_manager = EffectManager()

    def render(self) -> None:
        shake_offset_x, shake_offset_y = self._get_shake_offset()

        if shake_offset_x or shake_offset_y:
            self._render_with_shake(shake_offset_x, shake_offset_y)
        else:
            self._render_game_area()
            self.effect_manager.render(self.screen)
            self._render_sidebar()

    def _get_shake_offset(self) -> Tuple[int, int]:
        for effect in self.effect_manager.get_active_effects():
            if isinstance(effect, ScreenShake):
                return effect.offset_x, effect.offset_y
        return 0, 0

    def _render_with_shake(self, offset_x: int, offset_y: int) -> None:
        original_surface = self.screen
        buffer = original_surface.copy()
        self.screen = buffer
        self._render_game_area()
        self.effect_manager.render(buffer)
        self._render_sidebar()
        self.screen = original_surface
        original_surface.fill((0, 0, 0))
        original_surface.blit(buffer, (offset_x, offset_y))

    def _render_game_area(self) -> None:
        self.screen.fill((10, 14, 22))
        self._render_board()
        if self._setting_enabled("graphics.draw_ghost", True):
            self._render_ghost_piece()
        self._render_active_piece()
        if self._setting_enabled("graphics.draw_grid", True):
            self._render_grid_lines()

    def _setting_enabled(self, path: str, fallback: bool) -> bool:
        if self.settings_manager is None:
            return fallback
        try:
            return self.settings_manager.get_bool(path)
        except (KeyError, TypeError, ValueError):
            return fallback

    def _render_board(self) -> None:
        board_rect = pygame.Rect(
            0,
            0,
            SETTINGS.GRID.GAME_WIDTH,
            SETTINGS.GRID.GAME_HEIGHT,
        )
        pygame.draw.rect(self.screen, (24, 30, 42), board_rect)

        for y, row in enumerate(self.controller.board.grid):
            for x, tile in enumerate(row):
                self._render_tile(tile, x, y)

    def _render_active_piece(self) -> None:
        piece = self.controller.current_piece
        if piece is None:
            return

        for x, y in piece.get_occupied_places():
            if y >= 0:
                self._render_tile(piece.tile, x, y)

    def _render_ghost_piece(self) -> None:
        piece = self.controller.current_piece
        if piece is None:
            return

        ghost = self._calculate_ghost_position(piece)
        if ghost is None:
            return

        tile_size = SETTINGS.GRID.TILE_SIZE
        ghost_surface = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)

        if self.assets is not None:
            try:
                tile_img = self.assets.get_tile_surface(ghost.tile)
                ghost_surface.blit(tile_img, (0, 0))
            except (KeyError, FileNotFoundError, pygame.error):
                color = SETTINGS.TILE_COLORS.get_tile_info(ghost.tile).color
                pygame.draw.rect(
                    ghost_surface,
                    color,
                    pygame.Rect(0, 0, tile_size, tile_size).inflate(-2, -2),
                    border_radius=3,
                )
        else:
            color = SETTINGS.TILE_COLORS.get_tile_info(ghost.tile).color
            pygame.draw.rect(
                ghost_surface,
                color,
                pygame.Rect(0, 0, tile_size, tile_size).inflate(-2, -2),
                border_radius=3,
            )

        ghost_surface.set_alpha(80)

        for x, y in ghost.get_occupied_places():
            if y >= 0:
                rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                self.screen.blit(ghost_surface, rect)

    def _render_grid_lines(self) -> None:
        tile_size = SETTINGS.GRID.TILE_SIZE

        for x in range(SETTINGS.GRID.GRID_WIDTH + 1):
            pygame.draw.line(
                self.screen,
                (37, 45, 61),
                (x * tile_size, 0),
                (x * tile_size, SETTINGS.GRID.GAME_HEIGHT),
            )
        for y in range(SETTINGS.GRID.GRID_HEIGHT + 1):
            pygame.draw.line(
                self.screen,
                (37, 45, 61),
                (0, y * tile_size),
                (SETTINGS.GRID.GAME_WIDTH, y * tile_size),
            )

    def _render_sidebar(self) -> None:
        left = SETTINGS.GRID.GAME_WIDTH + GAME_STYLE.SIDEBAR_LEFT_OFFSET
        center_x = left + GAME_STYLE.SIDEBAR_CENTER_X

        self._render_hold_piece(center_x, GAME_STYLE.HOLD_TITLE_Y)
        self._render_next_piece(center_x, GAME_STYLE.NEXT_TITLE_Y)

        self._draw_text(tr("hud.score"), SETTINGS.UI_TYPOGRAPHY.BODY, (159, 173, 189), (center_x, GAME_STYLE.SCORE_TITLE_Y))
        self._draw_text(format_int(self.session.score), SETTINGS.UI_TYPOGRAPHY.BODY, (242, 244, 248), (center_x, GAME_STYLE.SCORE_VALUE_Y))

        self._draw_text(tr("hud.level"), SETTINGS.UI_TYPOGRAPHY.BODY, (159, 173, 189), (center_x, GAME_STYLE.LEVEL_TITLE_Y))
        self._draw_text(format_int(self.session.level), SETTINGS.UI_TYPOGRAPHY.BODY, (242, 244, 248), (center_x, GAME_STYLE.LEVEL_VALUE_Y))

        self._draw_text(tr("hud.lines"), SETTINGS.UI_TYPOGRAPHY.BODY, (159, 173, 189), (center_x, GAME_STYLE.LINES_TITLE_Y))
        self._draw_text(format_int(self.session.total_lines), SETTINGS.UI_TYPOGRAPHY.BODY, (242, 244, 248), (center_x, GAME_STYLE.LINES_VALUE_Y))

    def _render_next_piece(self, center_x: int, center_y: int) -> None:
        self._render_piece_preview(tr("hud.next"), self.controller.next_piece, center_x, center_y)

    def _render_hold_piece(self, center_x: int, center_y: int) -> None:
        self._render_piece_preview(tr("hud.hold"), self.controller.held_piece, center_x, center_y)

    def _render_piece_preview(
        self,
        label: str,
        piece_type: Optional[TetrominoType],
        center_x: int,
        center_y: int,
    ) -> None:
        self._draw_text(label, SETTINGS.UI_TYPOGRAPHY.BODY, (159, 173, 189), (center_x, center_y))

        preview_size = SETTINGS.GRID.TILE_SIZE * 0.7
        preview_padding = GAME_STYLE.PREVIEW_PADDING
        preview_box_size = int(preview_size * 4 + preview_padding * 2)
        box_left = int(center_x - preview_box_size / 2)
        box_top = int(center_y + GAME_STYLE.PREVIEW_BOX_TOP_OFFSET)
        preview_box = pygame.Rect(box_left, box_top, preview_box_size, preview_box_size)

        pygame.draw.rect(self.screen, (24, 30, 42), preview_box, border_radius=6)
        pygame.draw.rect(self.screen, (58, 69, 89), preview_box, width=2, border_radius=6)

        if piece_type is None:
            return

        from engine.shapes import get_shape

        matrix = get_shape(piece_type, 0)
        occupied_cells = [
            (row_index, col_index)
            for row_index, row in enumerate(matrix)
            for col_index, cell in enumerate(row)
            if cell
        ]

        if not occupied_cells:
            return

        min_row = min(row for row, _ in occupied_cells)
        max_row = max(row for row, _ in occupied_cells)
        min_col = min(col for _, col in occupied_cells)
        max_col = max(col for _, col in occupied_cells)

        piece_width = (max_col - min_col + 1) * preview_size
        piece_height = (max_row - min_row + 1) * preview_size

        start_x = box_left + (preview_box_size - piece_width) / 2 - min_col * preview_size
        start_y = box_top + (preview_box_size - piece_height) / 2 - min_row * preview_size

        for row_index, row in enumerate(matrix):
            for col_index, cell in enumerate(row):
                if cell:
                    x = start_x + col_index * preview_size
                    y = start_y + row_index * preview_size

                    tile = piece_type.tile
                    rect = pygame.Rect(
                        int(x),
                        int(y),
                        int(preview_size),
                        int(preview_size),
                    )

                    if self.assets is not None:
                        try:
                            tile_img = self.assets.get_tile_surface(tile)
                            scaled = pygame.transform.scale(tile_img, (int(preview_size), int(preview_size)))
                            self.screen.blit(scaled, rect)
                            continue
                        except (KeyError, FileNotFoundError, pygame.error):
                            pass

                    color = SETTINGS.TILE_COLORS.get_tile_info(tile).color
                    pygame.draw.rect(
                        self.screen,
                        color,
                        rect.inflate(-2, -2),
                        border_radius=3,
                    )

    def _render_tile(self, tile: Tile, x: int, y: int) -> None:
        if tile == Tile.EMPTY:
            return

        tile_size = SETTINGS.GRID.TILE_SIZE
        rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)

        if self.assets is not None:
            try:
                self.screen.blit(self.assets.get_tile_surface(tile), rect)
                return
            except (KeyError, FileNotFoundError, pygame.error):
                pass

        color = SETTINGS.TILE_COLORS.get_tile_info(tile).color
        pygame.draw.rect(self.screen, color, rect.inflate(-2, -2), border_radius=3)

    def _calculate_ghost_position(self, piece: Tetromino) -> Optional[Tetromino]:
        ghost = Tetromino(
            piece=piece.piece,
            x=piece.x,
            y=piece.y,
            rotation_index=piece.rotation_index,
        )

        ghost.fall(self.controller.board)

        if ghost.y == piece.y:
            return None

        return ghost

    def _draw_text(
        self, text: str, size: int, color: Color, center: Tuple[int, int]
    ) -> None:
        font = self._get_font(size)
        rendered = font.render(text, SETTINGS.UI_TYPOGRAPHY.ANTIALIAS, color)
        self.screen.blit(rendered, rendered.get_rect(center=center))

    def _get_font(self, size: int) -> pygame.font.Font:
        if self.assets is not None:
            try:
                return self.assets.get_font(size)
            except (KeyError, FileNotFoundError, pygame.error):
                pass
        return pygame.font.Font(None, size)
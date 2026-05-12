from typing import Optional, Tuple

import pygame

from engine import Board, GameController, GameSession, Tetromino, Tile
from settings import SETTINGS
from ui.assets import AssetManager


Color = Tuple[int, int, int]


class GameRenderer:
    def __init__(
        self,
        screen: pygame.Surface,
        assets: Optional[AssetManager],
        controller: GameController,
        session: GameSession,
    ) -> None:
        self.screen = screen
        self.assets = assets
        self.controller = controller
        self.session = session

    def render(self) -> None:
        self.screen.fill((10, 14, 22))
        self._render_board()
        self._render_ghost_piece()
        self._render_active_piece()
        self._render_grid_lines()
        self._render_sidebar()

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
        left = SETTINGS.GRID.GAME_WIDTH + 24

        self._render_next_piece(left + 76, 50)

        self._draw_text("SCORE", 16, (159, 173, 189), (left + 76, 210))
        self._draw_text(str(self.session.score), 20, (242, 244, 248), (left + 76, 245))

        self._draw_text("LEVEL", 16, (159, 173, 189), (left + 76, 310))
        self._draw_text(str(self.session.level), 20, (242, 244, 248), (left + 76, 345))

        self._draw_text("LINES", 16, (159, 173, 189), (left + 76, 410))
        self._draw_text(str(self.session.total_lines), 20, (242, 244, 248), (left + 76, 445))

    def _render_next_piece(self, center_x: int, center_y: int) -> None:
        self._draw_text("NEXT", 16, (159, 173, 189), (center_x, center_y))

        next_piece_type = self.controller.next_piece
        if next_piece_type is None:
            return

        from engine.shapes import get_shape

        matrix = get_shape(next_piece_type, 0)
        tile_size = SETTINGS.GRID.TILE_SIZE
        preview_size = tile_size * 0.7

        matrix_width = len(matrix[0])
        matrix_height = len(matrix)
        total_width = matrix_width * preview_size
        total_height = matrix_height * preview_size

        start_x = center_x - total_width / 2
        start_y = center_y + 30

        for row_index, row in enumerate(matrix):
            for col_index, cell in enumerate(row):
                if cell:
                    x = start_x + col_index * preview_size
                    y = start_y + row_index * preview_size

                    tile = next_piece_type.tile
                    rect = pygame.Rect(x, y, preview_size, preview_size)

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
        rendered = font.render(text, True, color)
        self.screen.blit(rendered, rendered.get_rect(center=center))

    def _get_font(self, size: int) -> pygame.font.Font:
        if self.assets is not None:
            try:
                return self.assets.get_font(size)
            except (KeyError, FileNotFoundError, pygame.error):
                pass
        return pygame.font.Font(None, size)

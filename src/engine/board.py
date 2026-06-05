from typing import Any, List, Optional, Sequence, Tuple

from .tile import Tile


Cell = Tile
Matrix = Sequence[Sequence[int]]
Position = Tuple[int, int]


class Board:
    def __init__(
        self,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> None:
        if width is None or height is None:
            from settings import SETTINGS

            if width is None:
                width = SETTINGS.GRID.GRID_WIDTH
            if height is None:
                height = SETTINGS.GRID.GRID_HEIGHT

        self.width = width
        self.height = height
        self.grid: List[List[Cell]] = [
            [Tile.EMPTY for _ in range(self.width)] for _ in range(self.height)
        ]

    def check_collision(self, matrix: Matrix, x: int, y: int, allow_top_overflow: bool = False) -> bool:
        for row_index, row in enumerate(matrix):
            for col_index, cell in enumerate(row):
                if not cell:
                    continue

                board_x = x + col_index
                board_y = y + row_index

                if not self._is_inside(board_x, board_y, allow_top_overflow):
                    return True

                if board_y >= 0 and self.grid[board_y][board_x] != Tile.EMPTY:
                    return True

        return False
    
    def get_full_row_indices(self) -> list[int]:
        return [y for y in range(self.height) if self._is_full_row(self.grid[y])]

    def clear_full_rows(self) -> int:
        remaining_rows = [row for row in self.grid if not self._is_full_row(row)]
        cleared_count = self.height - len(remaining_rows)

        empty_rows = [
            [Tile.EMPTY for _ in range(self.width)] for _ in range(cleared_count)
        ]
        self.grid = empty_rows + remaining_rows

        return cleared_count

    def fix_block(self, tetromino: Any) -> None:
        tile = self._get_tile(tetromino)

        for x, y in tetromino.get_occupied_places():
            if not self._is_inside(x, y):
                raise ValueError(f"Cannot fix block outside board at ({x}, {y})")
            if self.grid[y][x] != Tile.EMPTY:
                raise ValueError(f"Cannot fix block over occupied cell at ({x}, {y})")

            self.grid[y][x] = tile

    def _is_inside(self, x: int, y: int, allow_top_overflow: bool = False) -> bool:
        x_in_bounds = 0 <= x < self.width
        y_in_bounds = y < self.height if allow_top_overflow else 0 <= y < self.height
        return x_in_bounds and y_in_bounds

    @staticmethod
    def _is_full_row(row: Sequence[Cell]) -> bool:
        return all(cell != Tile.EMPTY for cell in row)

    @staticmethod
    def _get_tile(tetromino: Any) -> Tile:
        tile = getattr(tetromino, "tile", None)
        if tile is not None:
            return Tile(tile)

        raise ValueError("Tetromino must expose a tile.")

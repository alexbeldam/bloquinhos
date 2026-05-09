from typing import Any, List, Optional, Sequence, Tuple

try:
    from settings import SETTINGS
except ModuleNotFoundError:
    from src.settings import SETTINGS


ImageKey = str
Cell = Optional[ImageKey]
Matrix = Sequence[Sequence[int]]
Position = Tuple[int, int]


class Board:
    def __init__(
        self,
        width: int = SETTINGS.SCREEN.GRID_WIDTH,
        height: int = SETTINGS.SCREEN.GRID_HEIGHT,
    ) -> None:
        self.width = width
        self.height = height
        self.grid: List[List[Cell]] = [
            [None for _ in range(self.width)] for _ in range(self.height)
        ]

    def check_collision(self, matrix: Matrix, x: int, y: int) -> bool:
        for row_index, row in enumerate(matrix):
            for col_index, cell in enumerate(row):
                if not cell:
                    continue

                board_x = x + col_index
                board_y = y + row_index

                if not self._is_inside(board_x, board_y):
                    return True

                if self.grid[board_y][board_x] is not None:
                    return True

        return False

    def clear_full_rows(self) -> int:
        remaining_rows = [row for row in self.grid if not self._is_full_row(row)]
        cleared_count = self.height - len(remaining_rows)

        empty_rows = [
            [None for _ in range(self.width)] for _ in range(cleared_count)
        ]
        self.grid = empty_rows + remaining_rows

        return cleared_count

    def fix_block(self, tetromino: Any) -> None:
        image_key = self._get_image_key(tetromino)

        for x, y in tetromino.get_occupied_places():
            if not self._is_inside(x, y):
                raise ValueError(f"Cannot fix block outside board at ({x}, {y})")
            if self.grid[y][x] is not None:
                raise ValueError(f"Cannot fix block over occupied cell at ({x}, {y})")

            self.grid[y][x] = image_key

    def _is_inside(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    @staticmethod
    def _is_full_row(row: Sequence[Cell]) -> bool:
        return all(cell is not None for cell in row)

    @staticmethod
    def _get_image_key(tetromino: Any) -> ImageKey:
        for attr_name in ("image_key", "image_asset", "asset_name"):
            image_key = getattr(tetromino, attr_name, None)
            if image_key is not None:
                return image_key

        raise ValueError(
            "Tetromino must expose image_key, image_asset, or asset_name."
        )

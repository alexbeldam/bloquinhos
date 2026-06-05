from enum import Enum, auto
from typing import Callable

from .tile import Tetromino as TetrominoType


class EventType(Enum):
    LINE_CLEAR = auto()
    PIECE_LOCKED = auto()
    GAME_OVER = auto()
    NEXT_PIECE_CHANGED = auto()
    HOLD = auto()
    HARD_DROP = auto()
    LEVEL_UP = auto()

LinesClearedHandler = Callable[[int], None]
PieceLockedHandler = Callable[[TetrominoType], None]
GameOverHandler = Callable[[], None]
NextPieceChangedHandler = Callable[[TetrominoType], None]
HoldHandler = Callable[[TetrominoType], None]
HardDropHandler = Callable[[], None]
LevelUpHandler = Callable[[int], None]

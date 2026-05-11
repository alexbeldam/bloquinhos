from typing import Callable, Protocol
from .tile import Tetromino as TetrominoType


class GameEventHandler(Protocol):
    def __call__(self, *args, **kwargs) -> None:
        ...


LinesClearedHandler = Callable[[int], None]
PieceLockedHandler = Callable[[TetrominoType], None]
GameOverHandler = Callable[[], None]
NextPieceChangedHandler = Callable[[TetrominoType], None]

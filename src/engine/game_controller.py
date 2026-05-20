import random
from typing import Dict, List, Optional

from .board import Board
from .events import (
    GameOverHandler,
    LinesClearedHandler,
    NextPieceChangedHandler,
    PieceLockedHandler,
)
from .physics import GravityController
from .tetromino import Tetromino
from .tile import Tetromino as TetrominoType
from utils.logger import log


class GameController:
    def __init__(self, board: Optional[Board] = None) -> None:
        self.board = board if board is not None else Board()
        self.current_piece: Optional[Tetromino] = None
        self.next_piece: Optional[TetrominoType] = None
        self.is_game_over: bool = False
        self.gravity_timer: float = 0.0
        self.gravity_interval: float = 1.0
        
        self._piece_bag: List[TetrominoType] = []
        self._event_handlers: Dict[str, List] = {
            'line_clear': [],
            'piece_locked': [],
            'game_over': [],
            'next_piece_changed': [],
        }
        
        self._initialize_game()

    def _initialize_game(self) -> None:
        from settings import SETTINGS
        
        self.gravity_interval = GravityController.calculate_gravity_interval(
            SETTINGS.DIFFICULTY.STARTING_LEVEL
        )
        self.next_piece = self._generate_next_piece()
        self._spawn_new_piece()

    def update(self, delta_time: float) -> None:
        if self.is_game_over or self.current_piece is None:
            return

        self.gravity_timer += delta_time

        if self.gravity_timer >= self.gravity_interval:
            self.gravity_timer = 0.0
            self._apply_gravity()

    def move_left(self) -> bool:
        if self.is_game_over or self.current_piece is None:
            return False
        
        moved = self.current_piece.move_left(self.board)
        return moved

    def move_right(self) -> bool:
        if self.is_game_over or self.current_piece is None:
            return False
        
        moved = self.current_piece.move_right(self.board)
        return moved

    def move_down(self) -> bool:
        if self.is_game_over or self.current_piece is None:
            return False
        
        moved = self.current_piece.move_down(self.board)
        
        if not moved:
            self._lock_piece()
        
        return moved

    def rotate(self) -> bool:
        if self.is_game_over or self.current_piece is None:
            return False
        
        rotated = self.current_piece.rotate(self.board)
        return rotated

    def hard_drop(self) -> int:
        if self.is_game_over or self.current_piece is None:
            return 0
        
        distance = self.current_piece.fall(self.board)
        self._lock_piece()
        
        return distance

    def reset(self) -> None:
        self.board = Board(self.board.width, self.board.height)
        self.current_piece = None
        self.next_piece = None
        self.is_game_over = False
        self.gravity_timer = 0.0
        self._piece_bag = []
        self._initialize_game()

    def on_line_clear(self, handler: LinesClearedHandler) -> None:
        self._event_handlers['line_clear'].append(handler)

    def on_piece_locked(self, handler: PieceLockedHandler) -> None:
        self._event_handlers['piece_locked'].append(handler)

    def on_game_over(self, handler: GameOverHandler) -> None:
        self._event_handlers['game_over'].append(handler)

    def on_next_piece_changed(self, handler: NextPieceChangedHandler) -> None:
        self._event_handlers['next_piece_changed'].append(handler)

    def _apply_gravity(self) -> None:
        self.move_down()

    def _lock_piece(self) -> None:
        if self.current_piece is None:
            return

        self.board.fix_block(self.current_piece)
        
        self._emit_event('piece_locked', self.current_piece.piece)
        
        cleared_lines = self.board.clear_full_rows()
        if cleared_lines > 0:
            self._emit_event('line_clear', cleared_lines)
        
        self._spawn_new_piece()

    def _spawn_new_piece(self) -> None:
        if self.next_piece is None:
            self.next_piece = self._generate_next_piece()

        self.current_piece = Tetromino(piece=self.next_piece)
        
        if self._check_game_over():
            self._displace_piece_on_game_over()
            self.is_game_over = True
            self._emit_event('game_over')
            return
        
        self.next_piece = self._generate_next_piece()
        self._emit_event('next_piece_changed', self.next_piece)

    def _check_game_over(self) -> bool:
        if self.current_piece is None:
            return False
        
        collision = self.board.check_collision(
            self.current_piece.matrix,
            self.current_piece.x,
            self.current_piece.y,
        )
        
        return collision
    
    def _displace_piece_on_game_over(self) -> None:
        if self.current_piece is None:
            return
        
        max_displacement = 2
        
        for _ in range(max_displacement):
            self.current_piece.y -= 1
            
            if not self.board.check_collision(
                self.current_piece.matrix,
                self.current_piece.x,
                self.current_piece.y,
                allow_top_overflow=True,
            ):
                return
        
        log.warning(f"Could not find clear position for game over piece after {max_displacement} attempts")

    def _generate_next_piece(self) -> TetrominoType:
        from settings import SETTINGS
        
        if SETTINGS.GAMEPLAY.USE_BAG_SYSTEM:
            return self._generate_from_bag()
        
        return random.choice(list(TetrominoType))

    def _generate_from_bag(self) -> TetrominoType:
        if not self._piece_bag:
            self._piece_bag = list(TetrominoType)
            random.shuffle(self._piece_bag)
        
        return self._piece_bag.pop()

    def _emit_event(self, event_type: str, *args) -> None:
        for handler in self._event_handlers.get(event_type, []):
            handler(*args)

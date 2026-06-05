from enum import Enum, auto
from typing import Type

from .events import LevelUpHandler
from .game_controller import GameController
from .physics import GravityController
from .progression import LevelManager
from .scoring import ScoreCalculator
from utils.logger import log


class GameState(Enum):
    RUNNING = auto()
    PAUSED = auto()
    GAME_OVER = auto()


class GameSession:
    def __init__(
        self,
        game_controller: GameController,
        score_calculator: Type[ScoreCalculator] = ScoreCalculator,
        level_manager: LevelManager | None = None,
        gravity_controller: Type[GravityController] = GravityController,
    ) -> None:
        self.game_controller = game_controller
        self._score_calculator = score_calculator
        self._level_manager = level_manager if level_manager is not None else LevelManager()
        self._gravity_controller = gravity_controller
        self._score = 0
        self._state = GameState.RUNNING
        self._singles = 0
        self._doubles = 0
        self._triples = 0
        self._tetris = 0
        self._level_up_handlers: list[LevelUpHandler] = []

        self.game_controller.on_line_clear(self._on_line_clear)
        self.game_controller.on_game_over(self._on_game_over)
        self._sync_gravity_interval()
    
    def on_level_up(self, handler: LevelUpHandler) -> None:
        self._level_up_handlers.append(handler)

    @property
    def score(self) -> int:
        return self._score

    @property
    def level(self) -> int:
        return self._level_manager.current_level

    @property
    def total_lines(self) -> int:
        return self._level_manager.total_lines

    @property
    def singles(self) -> int:
        return self._singles

    @property
    def doubles(self) -> int:
        return self._doubles

    @property
    def triples(self) -> int:
        return self._triples

    @property
    def tetris(self) -> int:
        return self._tetris

    @property
    def state(self) -> GameState:
        return self._state

    def pause(self) -> None:
        if self._state == GameState.RUNNING:
            self._state = GameState.PAUSED
            log.debug("Game paused")

    def resume(self) -> None:
        if self._state == GameState.PAUSED:
            self._state = GameState.RUNNING
            log.debug("Game resumed")

    def reset(self) -> None:
        log.debug("Resetting game session")
        self._score = 0
        self._level_manager.reset()
        self._state = GameState.RUNNING
        self.game_controller.reset()
        self._singles = 0
        self._doubles = 0
        self._triples = 0
        self._tetris = 0
        self._sync_gravity_interval()

    def end_game(self) -> None:
        self._state = GameState.GAME_OVER
        self.game_controller.is_game_over = True

    def _on_line_clear(self, lines_cleared: int) -> None:
        if self._state != GameState.RUNNING:
            return

        points_earned = self._score_calculator.calculate_points(
            lines_cleared,
            self.level,
        )
        self._score += points_earned
        log.debug(f"Score updated: +{points_earned} points (total: {self._score})")

        if lines_cleared == 1:
            self._singles += 1
        elif lines_cleared == 2:
            self._doubles += 1
        elif lines_cleared == 3:
            self._triples += 1
        elif lines_cleared == 4:
            self._tetris += 1
        
        level_changed = self._level_manager.add_lines(lines_cleared)

        if level_changed:
            log.info(f"Level up! Now at level {self.level}")
            self._sync_gravity_interval()
            for handler in self._level_up_handlers:
                handler(self.level)

    def _on_game_over(self) -> None:
        self._state = GameState.GAME_OVER

    def _sync_gravity_interval(self) -> None:
        self.game_controller.gravity_interval = (
            self._gravity_controller.calculate_gravity_interval(self.level)
        )

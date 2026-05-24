from typing import Tuple

from engine import GameController, GameSession, TetrominoType
from service_container import ServiceContainer
from utils.logger import log


class GameInitializer:
    def __init__(self, services: ServiceContainer):
        self.services = services
        self.game_controller: GameController = None
        self.game_session: GameSession = None
    
    def initialize(self) -> Tuple[GameController, GameSession]:
        log.debug("Initializing game session")
        
        self.game_controller = GameController()
        self.game_session = GameSession(self.game_controller)
        
        self._setup_event_handlers(self.game_controller)
        
        return self.game_controller, self.game_session
    
    @staticmethod
    def _setup_event_handlers(game: GameController) -> None:
        def on_line_cleared(lines: int) -> None:
            log.info(f"Cleared {lines} line(s)")
        
        def on_piece_locked(piece: TetrominoType) -> None:
            pass
        
        def on_game_over() -> None:
            log.info("Game over")
        
        def on_next_piece(piece: TetrominoType) -> None:
            pass
        
        game.on_line_clear(on_line_cleared)
        game.on_piece_locked(on_piece_locked)
        game.on_game_over(on_game_over)
        game.on_next_piece_changed(on_next_piece)

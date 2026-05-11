from settings import SETTINGS
from engine import GameController, TetrominoType
from network.connection_manager import NetworkManager
from utils.path_manager import PathManager as pm
import utils.env_manager as env
from utils.logger import log


def on_line_cleared(lines: int) -> None:
    log.info(f"🎯 Cleared {lines} line(s)!")


def on_piece_locked(piece: TetrominoType) -> None:
    log.info(f"🔒 Piece locked: {piece.name}")


def on_game_over() -> None:
    log.warning("💀 Game Over!")


def on_next_piece(piece: TetrominoType) -> None:
    log.info(f"🔮 Next piece: {piece.name}")


def bootstrap():
    env.load_env_vars()

    log.info("🚀 Starting application...")

    net = NetworkManager()

    log.info("🔌 Waiting for network connection...")

    if not net.wait_for_connection(timeout=5.0):
        log.warning("⚠️ Network connection not established. Continuing offline.")

    tilemap_path = pm.get_image_path(SETTINGS.TILEMAP.FILENAME)
    log.info(f"🗺️ Tilemap path: {tilemap_path}")

    log.info("🎮 Initializing Game Controller...")
    game = GameController()

    game.on_line_clear(on_line_cleared)
    game.on_piece_locked(on_piece_locked)
    game.on_game_over(on_game_over)
    game.on_next_piece_changed(on_next_piece)

    log.info(f"🎲 Current piece: {game.current_piece.piece.name if game.current_piece else 'None'}")
    log.info(f"🔮 Next piece: {game.next_piece.name if game.next_piece else 'None'}")
    log.info(f"⏱️ Gravity interval: {game.gravity_interval}s")

    log.info("✨ Game Controller ready!")


if __name__ == "__main__":
    bootstrap()
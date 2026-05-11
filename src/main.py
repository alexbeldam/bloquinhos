from settings import SETTINGS
from engine import GameController, GameSession, TetrominoType
from network.connection_manager import NetworkManager
from ui.assets import AssetLoader
from utils.path_manager import PathManager as pm
import utils.env_manager as env
from utils.logger import log
import pygame


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

    pygame.init()

    log.info("📦 Loading game assets...")
    assets = AssetLoader()
    asset_stats = assets.load_all_assets()
    log.info(
        f"✨ Assets loaded: {asset_stats['images']} images, "
        f"{asset_stats['sfx']} SFX, {asset_stats['music']} music, "
        f"{asset_stats['fonts']} fonts, {asset_stats['tiles']} tiles"
    )

    net = NetworkManager()

    log.info("🔌 Waiting for network connection...")

    if not net.wait_for_connection(timeout=5.0):
        log.warning("⚠️ Network connection not established. Continuing offline.")

    log.info("🎮 Initializing Game Controller...")
    game = GameController()
    session = GameSession(game)

    game.on_line_clear(on_line_cleared)
    game.on_piece_locked(on_piece_locked)
    game.on_game_over(on_game_over)
    game.on_next_piece_changed(on_next_piece)

    log.info(f"🎲 Current piece: {game.current_piece.piece.name if game.current_piece else 'None'}")
    log.info(f"🔮 Next piece: {game.next_piece.name if game.next_piece else 'None'}")
    log.info(f"⏱️ Gravity interval: {game.gravity_interval}s")
    log.info(
        f"📊 Session state: {session.state.name} | "
        f"score={session.score} | level={session.level} | lines={session.total_lines}"
    )

    log.info("✨ Game Controller ready!")


if __name__ == "__main__":
    bootstrap()

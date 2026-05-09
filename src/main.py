from settings import SETTINGS
from engine.tile import Tetromino
from network.connection_manager import NetworkManager
from utils.path_manager import PathManager as pm
import utils.env_manager as env
from utils.logger import log
import random

def bootstrap():
    env.load_env_vars()

    log.info("🚀 Starting application...")

    net = NetworkManager()

    log.info("🔌 Waiting for network connection...")

    if not net.wait_for_connection(timeout=5.0):
        log.warning("⚠️ Network connection not established. Continuing offline.")

    tetromino = random.choice(list(Tetromino))
    tile = tetromino.tile
    tile_info = SETTINGS.TILE_COLORS.get_tile_info(tile)
    tilemap_path = pm.get_image_path(SETTINGS.TILEMAP.FILENAME)

    log.info(f"🎲 Randomly selected tetromino: {tetromino.name}")
    log.info(
        "🧩 Tile mapping: tile=%s index=%s color=%s",
        tile.name,
        tile_info.index,
        tile_info.color,
    )
    log.info(f"🗺️ Tilemap path: {tilemap_path}")

if __name__ == "__main__":
    bootstrap()
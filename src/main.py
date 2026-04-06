from settings import SETTINGS
from network.connection_manager import NetworkManager
from utils.path_manager import get_image_path
import utils.env_manager as env
from utils.logger import log
import random

_ASSETS = SETTINGS.ASSETS.TETROMINO_ASSETS

def bootstrap():
    env.load_env_vars()

    log.info("🚀 Starting application...")

    net = NetworkManager()

    log.info("🔌 Waiting for network connection...")

    if not net.wait_for_connection(timeout=5.0):
        log.warning("⚠️ Network connection not established. Continuing offline.")

    tetromino = random.choice(list(_ASSETS.keys()))

    log.info(f"🎲 Randomly selected tetromino: {tetromino}")

    img_path = get_image_path(_ASSETS[tetromino])
    
    log.info(f"📁 Image path for {tetromino}: {img_path}")

if __name__ == "__main__":
    bootstrap()
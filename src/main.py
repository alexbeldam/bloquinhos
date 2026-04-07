from settings import SETTINGS
from network.connection_manager import NetworkManager
from utils.path_manager import PathManager as pm
import utils.env_manager as env
from utils.logger import log
import random
import pygame

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

    img_path = pm.get_image_path(_ASSETS[tetromino])
    
    log.info(f"📁 Image path for {tetromino}: {img_path}")

    pygame.init()

    screen = pygame.display.set_mode((400, 400))
    pygame.display.set_caption("Tetris Tetromino Display")

    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((0, 0, 0))

        try:
            tetromino_image = pygame.image.load(img_path)
            screen.blit(tetromino_image, (150, 150))
        except Exception as e:
            log.error(f"❌ Failed to load image: {e}")

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    bootstrap()
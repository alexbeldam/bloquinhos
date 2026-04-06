from utils.path_manager import get_image_path
from settings import SETTINGS
from network.connection_manager import NetworkManager

_TETROMINO_ASSETS = SETTINGS.ASSETS.TETROMINO_ASSETS

print("Hello World!")
print("The O tetromino has the image with path:", get_image_path(_TETROMINO_ASSETS['O']))

manager = NetworkManager()
online = manager.wait_for_connection(timeout=5.0)

print("Is online?", online)
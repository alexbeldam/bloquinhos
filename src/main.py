import utils.path_manager as pm
import network.connection_manager as cm
from constants import TETROMINO_ASSETS

print("Hello World!")
print("The O tetromino has the image with path:", pm.get_image_path(TETROMINO_ASSETS['O']))

manager = cm.NetworkManager()
online = manager.wait_for_connection(timeout=5.0)

print("Is online?", online)
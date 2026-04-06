import sys
import os

def get_base_path(bundled=False):
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS if bundled else os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

        return os.path.abspath(os.path.join(base_path, '../..'))

def get_assets_path():
    return os.path.join(get_base_path(), 'assets')

def get_data_path():
    return os.path.join(get_base_path(), 'data')

def get_env_path():
    return os.path.join(get_base_path(bundled=True), '.env')

def get_image_path(filename=""):
    return os.path.join(get_assets_path(), 'img', filename)

def get_audio_path(filename=""):
    return os.path.join(get_assets_path(), 'aud', filename)

def get_user_save_path():
    return os.path.join(get_data_path(), 'user_data.bin')

def get_preferences_path():
    return os.path.join(get_data_path(), 'preferences.json')
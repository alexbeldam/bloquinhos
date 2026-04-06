import os
import sys
from settings import SETTINGS

_PATHS = SETTINGS.PATHS

def get_assets_path(*args):
    return _get_abs_path(_PATHS.ASSETS_DIR, *args)

def get_data_path(*args):
    return _get_abs_path(_PATHS.DATA_DIR, *args)

def get_env_path():
    return _get_abs_path(_PATHS.ENV_FILE, bundled=True)

def get_image_path(filename=""):
    return get_assets_path(_PATHS.IMG_DIR, filename)

def get_audio_path(filename=""):
    return get_assets_path(_PATHS.AUD_DIR, filename)

def get_user_save_path():
    return get_data_path(_PATHS.SAVE_FILE)

def get_preferences_path():
    return get_data_path(_PATHS.PREFS_FILE)

def get_log_path():
    return _get_abs_path(_PATHS.LOG_DIR, _PATHS.LOG_FILE)

def _get_base_path(bundled):
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS if bundled else os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

        return os.path.abspath(os.path.join(base_path, '../..'))
    
def _get_abs_path(*args, bundled=False):
    return os.path.join(_get_base_path(bundled), *args)
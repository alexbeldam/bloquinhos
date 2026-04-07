import os
import sys
import platform
from settings import SETTINGS

class PathManager:
    _IS_FROZEN = getattr(sys, 'frozen', False)
    _OS = platform.system().lower()
    _APP_NAME = SETTINGS.APP_NAME.lower()
    _PATHS = SETTINGS.PATHS

    @classmethod
    def _get_static_base(cls, bundled: bool = False) -> str:
        if cls._IS_FROZEN:
            if bundled:
                return sys._MEIPASS
            if cls._OS == "linux":
                return f"/usr/share/{cls._APP_NAME}"
            return os.path.dirname(sys.executable)
        
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

    @classmethod
    def _get_cached_base(cls) -> str:
        if not cls._IS_FROZEN:
            return cls._get_static_base()

        if cls._OS == "windows":
            base = os.getenv("APPDATA", os.path.expanduser("~"))
        else:
            base = os.path.expanduser("~/.local/share")
            
        path = os.path.join(base, cls._APP_NAME)
        os.makedirs(path, exist_ok=True)
        return path

    @classmethod
    def get_assets_path(cls, *args) -> str:
        return os.path.join(cls._get_static_base(), cls._PATHS.ASSETS_DIR, *args)

    @classmethod
    def get_image_path(cls, filename: str = "") -> str:
        return cls.get_assets_path(cls._PATHS.IMG_DIR, filename)

    @classmethod
    def get_audio_path(cls, filename: str = "") -> str:
        return cls.get_assets_path(cls._PATHS.AUD_DIR, filename)

    @classmethod
    def get_env_path(cls) -> str:
        return os.path.join(cls._get_static_base(bundled=True), cls._PATHS.ENV_FILE)

    @classmethod
    def get_data_path(cls, *args) -> str:
        path = os.path.join(cls._get_cached_base(), cls._PATHS.DATA_DIR, *args)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path

    @classmethod
    def get_user_save_path(cls) -> str:
        return cls.get_data_path(cls._PATHS.SAVE_FILE)

    @classmethod
    def get_preferences_path(cls) -> str:
        return cls.get_data_path(cls._PATHS.PREFS_FILE)

    @classmethod
    def get_log_path(cls) -> str:
        path = os.path.join(cls._get_cached_base(), cls._PATHS.LOG_DIR, cls._PATHS.LOG_FILE)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path
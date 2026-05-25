import os
import sys
import platform

class PathManager:
    _IS_FROZEN = getattr(sys, 'frozen', False)
    _OS = platform.system().lower()

    @classmethod
    def _get_app_name(cls) -> str:
        from settings import SETTINGS
        return SETTINGS.APP_NAME.lower()

    @classmethod
    def _get_paths(cls):
        from settings import SETTINGS
        return SETTINGS.PATHS

    @classmethod
    def _get_static_base(cls, bundled: bool = False) -> str:
        if cls._IS_FROZEN:
            if bundled:
                return sys._MEIPASS
            if cls._OS == "linux":
                return f"/usr/share/{cls._get_app_name()}"
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
            
        path = os.path.join(base, cls._get_app_name())
        os.makedirs(path, exist_ok=True)
        return path

    @classmethod
    def get_assets_path(cls, *args) -> str:
        return os.path.join(cls._get_static_base(), cls._get_paths().ASSETS_DIR, *args)

    @classmethod
    def get_image_path(cls) -> str:
        return cls.get_assets_path(cls._get_paths().IMG_DIR)
    
    @classmethod
    def get_icon_path(cls) -> str:
        paths = cls._get_paths()
        return cls.get_assets_path(paths.IMG_DIR, paths.ICON_FILE)

    @classmethod
    def get_audio_path(cls) -> str:
        return cls.get_assets_path(cls._get_paths().AUD_DIR)

    @classmethod
    def get_font_path(cls) -> str:
        return cls.get_assets_path(cls._get_paths().FONT_DIR)

    @classmethod
    def get_env_path(cls) -> str:
        return os.path.join(cls._get_static_base(bundled=True), cls._get_paths().ENV_FILE)

    @classmethod
    def get_data_path(cls, *args) -> str:
        path = os.path.join(cls._get_cached_base(), cls._get_paths().DATA_DIR, *args)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path

    @classmethod
    def get_user_save_path(cls) -> str:
        return cls.get_data_path(cls._get_paths().SAVE_FILE)

    @classmethod
    def get_preferences_path(cls) -> str:
        return cls.get_data_path(cls._get_paths().PREFS_FILE)

    @classmethod
    def get_fallback_key_path(cls) -> str:
        from settings import SETTINGS
        return cls.get_data_path(SETTINGS.SECURITY.FALLBACK_KEY_FILE)

    @classmethod
    def get_dpapi_key_path(cls) -> str:
        from settings import SETTINGS
        return cls.get_data_path(SETTINGS.SECURITY.DPAPI_KEY_FILE)

    @classmethod
    def get_log_path(cls) -> str:
        paths = cls._get_paths()
        path = os.path.join(cls._get_cached_base(), paths.LOG_DIR, paths.LOG_FILE)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path
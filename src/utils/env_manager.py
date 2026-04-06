import os
from dotenv import load_dotenv
from .path_manager import get_env_path
from .logger import log, update_log_level

def load_env_vars():
    env_path = get_env_path()
    
    if os.path.exists(env_path):
        load_dotenv(env_path)
        log.info("⚙️ Subsystem successfully configured!")

        log_level = os.getenv("LOG_LEVEL", "INFO")
        update_log_level(log_level)
    else:
        log.warning("⚠️ Error configuring subsystem. Using default values.")

def get_env(key, default=None):
    return os.getenv(key, default)

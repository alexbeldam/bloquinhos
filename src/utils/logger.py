import logging
import os
from .path_manager import PathManager as pm

class DraculaFormatter(logging.Formatter):
    PINK = "\033[95m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"
    GREY = "\033[90m"

    FORMAT = "%(asctime)s [%(levelname)s] %(message)s"

    LEVEL_COLORS = {
        logging.DEBUG: PINK + FORMAT + RESET,
        logging.INFO: CYAN + FORMAT + RESET,
        logging.WARNING: YELLOW + FORMAT + RESET,
        logging.ERROR: RED + FORMAT + RESET,
        logging.CRITICAL: RED + "\033[1m" + FORMAT + RESET
    }

    def format(self, record):
        log_fmt = self.LEVEL_COLORS.get(record.levelno, self.FORMAT)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

class LogManager:
    _LEVELS = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }

    def __init__(self):
        self.logger = logging.getLogger("BlockProvider")
        self._setup()

    def _setup(self):
        log_path = pm.get_log_path()
        log_dir = os.path.dirname(log_path)

        self.logger.setLevel(logging.INFO)

        file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(DraculaFormatter())
        self.logger.addHandler(console_handler)

    def update_level(self, level_name: str):
        target_level = self._LEVELS.get(level_name.upper())
        
        if target_level is not None:
            if self.logger.level != target_level:
                self.logger.setLevel(target_level)
                self.logger.info(f"🔧 Log level updated to: {level_name.upper()}")
        else:
            self.logger.warning(f"⚠️ Invalid log level: {level_name}. Keeping current level.")

_manager = LogManager()
log = _manager.logger
update_log_level = _manager.update_level
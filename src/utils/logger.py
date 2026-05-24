import logging
import os

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
        from .path_manager import PathManager as pm
        log_path = pm.get_log_path()

        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        log_level = self._LEVELS.get(log_level_str, logging.INFO)
        
        self.logger.setLevel(log_level)

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


class _LazyLogger:
    _manager: LogManager | None = None

    def _get_manager(self) -> LogManager:
        if self._manager is None:
            self._manager = LogManager()
        return self._manager

    def __getattr__(self, name: str):
        return getattr(self._get_manager().logger, name)


log = _LazyLogger()

def update_log_level(level_name: str):
    log._get_manager().update_level(level_name)

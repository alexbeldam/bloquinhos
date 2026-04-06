from dataclasses import dataclass, field
from typing import Dict

@dataclass(frozen=True)
class ScreenConfig:
    TILE_SIZE: int = 32
    GRID_WIDTH: int = 10
    GRID_HEIGHT: int = 20
    GAME_WIDTH: int = 320         # GRID_WIDTH * TILE_SIZE
    GAME_HEIGHT: int = 640        # GRID_HEIGHT * TILE_SIZE
    SIDEBAR_WIDTH: int = 200
    SCREEN_WIDTH: int = 520       # GAME_WIDTH + SIDEBAR_WIDTH
    SCREEN_HEIGHT: int = 640      # GAME_HEIGHT
    FPS: int = 60

@dataclass(frozen=True)
class DifficultyConfig:
    STARTING_LEVEL: int = 1
    LINES_TO_LEVEL_UP: int = 10
    INITIAL_FALL_SPEED: int = 1000
    MIN_FALL_SPEED: int = 100
    SPEED_DECREMENT_RATIO: float = 0.8

@dataclass(frozen=True)
class ScoringConfig:
    SCORE_TABLE: Dict[int, int] = field(default_factory=lambda: {
        1: 100,
        2: 300,
        3: 500,
        4: 800
    })
    COMBO_BONUS: int = 50
    B2B_MULTIPLIER: float = 1.5

@dataclass(frozen=True)
class AssetConfig:
    TETROMINO_ASSETS: Dict[str, str] = field(default_factory=lambda: {
        'I': 'cyan.png',
        'J': 'blue.png',
        'L': 'orange.png',
        'O': 'yellow.png',
        'S': 'green.png',
        'T': 'purple.png',
        'Z': 'red.png'
    })

@dataclass(frozen=True)
class PathConfig:
    ASSETS_DIR: str = "assets"
    DATA_DIR: str = "data"
    ENV_FILE: str = ".env"
    SAVE_FILE: str = "user_data.bin"
    PREFS_FILE: str = "preferences.json"
    IMG_DIR: str = "img"
    AUD_DIR: str = "aud"
    LOG_DIR: str = "logs"          
    LOG_FILE: str = "game.log"

@dataclass(frozen=True)
class Settings:
    SCREEN: ScreenConfig = ScreenConfig()
    DIFFICULTY: DifficultyConfig = DifficultyConfig()
    SCORING: ScoringConfig = ScoringConfig()
    ASSETS: AssetConfig = AssetConfig()
    PATHS: PathConfig = PathConfig()

SETTINGS = Settings()
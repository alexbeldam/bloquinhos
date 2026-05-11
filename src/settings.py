from dataclasses import dataclass, field
from typing import Dict, Tuple, List
from engine.tile import Tile

@dataclass(frozen=True)
class TileInfo:
    index: int
    color: Tuple[int, int, int]

@dataclass(frozen=True)
class TilemapConfig:
    FILENAME: str = "tilemap"
    ROWS: int = 2
    COLUMNS: int = 4

@dataclass(frozen=True)
class TileColorConfig:
    CYAN: TileInfo = field(default_factory=lambda: TileInfo(0, (0, 255, 255)))
    BLUE: TileInfo = field(default_factory=lambda: TileInfo(1, (0, 0, 255)))
    ORANGE: TileInfo = field(default_factory=lambda: TileInfo(2, (255, 127, 0)))
    YELLOW: TileInfo = field(default_factory=lambda: TileInfo(3, (255, 255, 0)))
    GREEN: TileInfo = field(default_factory=lambda: TileInfo(4, (0, 255, 0)))
    PURPLE: TileInfo = field(default_factory=lambda: TileInfo(5, (160, 32, 240)))
    RED: TileInfo = field(default_factory=lambda: TileInfo(6, (255, 0, 0)))
    
    def get_tile_info(self, tile: Tile) -> TileInfo:
        tile_map = {
            Tile.CYAN: self.CYAN,
            Tile.BLUE: self.BLUE,
            Tile.ORANGE: self.ORANGE,
            Tile.YELLOW: self.YELLOW,
            Tile.GREEN: self.GREEN,
            Tile.PURPLE: self.PURPLE,
            Tile.RED: self.RED
        }
        if tile not in tile_map:
            raise ValueError(f"No tile info configured for {tile}")
        return tile_map[tile]

@dataclass(frozen=True)
class ScreenConfig:
    TILE_SIZE: int = 30
    GRID_WIDTH: int = 10
    GRID_HEIGHT: int = 20
    GAME_WIDTH: int = GRID_WIDTH * TILE_SIZE
    GAME_HEIGHT: int = GRID_HEIGHT * TILE_SIZE
    SIDEBAR_WIDTH: int = 200
    SCREEN_WIDTH: int = GAME_WIDTH + SIDEBAR_WIDTH
    SCREEN_HEIGHT: int = GAME_HEIGHT
    FPS: int = 60

@dataclass(frozen=True)
class DifficultyConfig:
    STARTING_LEVEL: int = 1
    LINES_TO_LEVEL_UP: int = 10
    INITIAL_FALL_SPEED: int = 1000
    MIN_FALL_SPEED: int = 100
    SPEED_DECREMENT_RATIO: float = 0.8
    GRAVITY_INTERVAL: float = 1.0

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
class PathConfig:
    ASSETS_DIR: str = "assets"
    DATA_DIR: str = "data"
    ENV_FILE: str = ".env"
    SAVE_FILE: str = "user_data.bin"
    PREFS_FILE: str = "preferences.json"
    IMG_DIR: str = "img"
    AUD_DIR: str = "aud"
    FONT_DIR: str = "fonts"
    LOG_DIR: str = "logs"          
    LOG_FILE: str = "game.log"

@dataclass(frozen=True)
class TetrominoConfig:
    SPAWN_X: int = 3
    SPAWN_Y: int = 0

@dataclass(frozen=True)
class GameplayConfig:
    USE_BAG_SYSTEM: bool = True
    LOCK_DELAY: float = 0.5
    DAS_DELAY: float = 0.133
    ARR_DELAY: float = 0.033

@dataclass(frozen=True)
class AssetConfig:
    FONT_NAME: str = "PressStart2P-Regular.ttf"
    FONT_SIZES: Tuple[int, ...] = (8, 12, 16, 24, 32)
    IMAGE_EXTENSIONS: Tuple[str, ...] = ('.png',)
    SFX_EXTENSIONS: Tuple[str, ...] = ('.wav',)
    MUSIC_EXTENSIONS: Tuple[str, ...] = ('.ogg',)

@dataclass(frozen=True)
class Settings:
    SCREEN: ScreenConfig = field(default_factory=ScreenConfig)
    DIFFICULTY: DifficultyConfig = field(default_factory=DifficultyConfig)
    SCORING: ScoringConfig = field(default_factory=ScoringConfig)
    PATHS: PathConfig = field(default_factory=PathConfig)
    TILEMAP: TilemapConfig = field(default_factory=TilemapConfig)
    TILE_COLORS: TileColorConfig = field(default_factory=TileColorConfig)
    TETROMINO: TetrominoConfig = field(default_factory=TetrominoConfig)
    GAMEPLAY: GameplayConfig = field(default_factory=GameplayConfig)
    ASSETS: AssetConfig = field(default_factory=AssetConfig)
    APP_NAME: str = "Bloquinhos"

SETTINGS = Settings()
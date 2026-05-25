from dataclasses import dataclass, field
from typing import Dict, Tuple, List
from engine.tile import Tile

Color = Tuple[int, int, int]

@dataclass(frozen=True)
class TileInfo:
    index: int
    color: Color

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
class GridConfig:
    TILE_SIZE: int = 30
    GRID_WIDTH: int = 10
    GRID_HEIGHT: int = 20
    SIDEBAR_WIDTH: int = 200
    
    @property
    def GAME_WIDTH(self) -> int:
        return self.GRID_WIDTH * self.TILE_SIZE
    
    @property
    def GAME_HEIGHT(self) -> int:
        return self.GRID_HEIGHT * self.TILE_SIZE

@dataclass(frozen=True)
class DisplayConfig:
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
    SAVE_FILE: str = ".user_data.bin"
    PREFS_FILE: str = "settings.json"
    IMG_DIR: str = "img"
    ICON_FILE: str = "logo.png"
    AUD_DIR: str = "aud"
    FONT_DIR: str = "fonts"
    LOG_DIR: str = "logs"          
    LOG_FILE: str = "game.log"

@dataclass(frozen=True)
class TetrominoConfig:
    SPAWN_X: int = 3
    SPAWN_Y: int = 0

@dataclass(frozen=True)
class SRSConfig:
    JLSTZ_KICKS: Dict[str, List[Tuple[int, int]]] = field(default_factory=lambda: {
        "0->1": [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
        "1->0": [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
        "1->2": [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
        "2->1": [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
        "2->3": [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
        "3->2": [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
        "3->0": [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
        "0->3": [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    })
    
    I_KICKS: Dict[str, List[Tuple[int, int]]] = field(default_factory=lambda: {
        "0->1": [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
        "1->0": [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
        "1->2": [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
        "2->1": [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
        "2->3": [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
        "3->2": [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
        "3->0": [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
        "0->3": [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
    })

@dataclass(frozen=True)
class GameplayConfig:
    USE_BAG_SYSTEM: bool = True
    LOCK_DELAY: float = 0.5
    DAS_DELAY: float = 0.133
    ARR_DELAY: float = 0.033

@dataclass(frozen=True)
class UITypographyConfig:
    FONT_NAME: str = "PressStart2P-Regular.ttf"
    TINY: int = 8
    SMALL: int = 12
    BODY: int = 16
    LARGE: int = 20
    TITLE: int = 24
    DISPLAY: int = 32
    
    @property
    def all_sizes(self) -> Tuple[int, ...]:
        from dataclasses import fields
        return tuple(
            getattr(self, f.name) 
            for f in fields(self) 
            if f.type == int
        )

@dataclass(frozen=True)
class AssetConfig:
    IMAGE_EXTENSIONS: Tuple[str, ...] = ('.png',)
    SFX_EXTENSIONS: Tuple[str, ...] = ('.wav',)
    MUSIC_EXTENSIONS: Tuple[str, ...] = ('.ogg',)

@dataclass(frozen=True)
class UIThemeConfig:
    TEXT_PRIMARY: Color = (248, 248, 242)
    TEXT_MUTED: Color = (98, 114, 164)
    CYAN: Color = (139, 233, 253)
    GREEN: Color = (80, 250, 123)
    ORANGE: Color = (255, 184, 108)
    PINK: Color = (255, 121, 198)
    PURPLE: Color = (189, 147, 249)
    RED: Color = (255, 85, 85)
    YELLOW: Color = (241, 250, 140)
    BG_DARKER: Color = (30, 32, 40)
    BG_DARK: Color = (40, 42, 54)
    BG_MEDIUM: Color = (68, 71, 90)
    BG_LIGHT: Color = (98, 114, 164)
    WHITE: Color = (255, 255, 255)
    GRAY_DARK: Color = (68, 71, 90)

@dataclass(frozen=True)
class LoadingLayoutConfig:
    SPLASH_SIZE_MULTIPLIER: int = 15
    BLOCK_SCALE_MULTIPLIER: float = 1.33
    PROGRESS_BAR_HEIGHT_RATIO: float = 2.0 / 3.0
    PROGRESS_BAR_WIDTH_MULTIPLIER: float = 13.33
    BORDER_WIDTH: int = 2

@dataclass(frozen=True)
class LoadingAnimationConfig:
    ANIMATION_CYCLE_TIME: float = 4.0
    FRAME_DELAY: int = 3
    MIN_DISPLAY_TIME_RATIO: float = 0.5
    PROGRESS_THRESHOLD: float = 0.995
    FRAME_BUDGET_RATIO: float = 0.5
    
    @property
    def MIN_DISPLAY_TIME(self) -> float:
        return self.ANIMATION_CYCLE_TIME * self.MIN_DISPLAY_TIME_RATIO
    
    @property
    def PROGRESS_SMOOTH_SPEED(self) -> float:
        import math
        return -math.log(1 - self.PROGRESS_THRESHOLD) / self.MIN_DISPLAY_TIME

@dataclass(frozen=True)
class NetworkConfig:
    CONNECTION_TIMEOUT: float = 5.0
    DEFAULT_TIMEOUT: float = 3.0
    SERVER_SELECTION_TIMEOUT_MS: int = 2000
    HEARTBEAT_INTERVAL_S: int = 30
    SCORES_COLLECTION: str = "scores"

@dataclass(frozen=True)
class SecurityConfig:
    KEYRING_SERVICE: str = "bloquinhos"
    KEYRING_ACCOUNT: str = "fernet-key"
    FALLBACK_KEY_FILE: str = ".key.bin"
    DPAPI_KEY_FILE: str = ".key.dpapi"
      
@dataclass(frozen=True)
class LoadingMessagesConfig:
    SERVICES: str = "Warming up the engines..."
    PREFERENCES: str = "Applying player preferences..."
    NETWORK: str = "Establishing uplink..."
    GAME: str = "Spawning first piece..."
    SCREENS: str = "Building the playfield..."
    IDENTITY: str = "Checking player identity..."
    ASSETS: str = "Coloring the blocks..."

@dataclass(frozen=True)
class ScreenNames:
    LOADING: str = "loading"
    IDENTITY_ENTRY: str = "identity_entry"
    MENU: str = "menu"
    GAME: str = "game"
    GAME_OVER: str = "game_over"
    PAUSE: str = "pause"
    RANKING: str = "ranking"
    QUIT: str = "quit"

@dataclass(frozen=True)
class Settings:
    GRID: GridConfig = field(default_factory=GridConfig)
    DISPLAY: DisplayConfig = field(default_factory=DisplayConfig)
    DIFFICULTY: DifficultyConfig = field(default_factory=DifficultyConfig)
    SCORING: ScoringConfig = field(default_factory=ScoringConfig)
    PATHS: PathConfig = field(default_factory=PathConfig)
    TILEMAP: TilemapConfig = field(default_factory=TilemapConfig)
    TILE_COLORS: TileColorConfig = field(default_factory=TileColorConfig)
    TETROMINO: TetrominoConfig = field(default_factory=TetrominoConfig)
    SRS: SRSConfig = field(default_factory=SRSConfig)
    GAMEPLAY: GameplayConfig = field(default_factory=GameplayConfig)
    UI_TYPOGRAPHY: UITypographyConfig = field(default_factory=UITypographyConfig)
    ASSETS: AssetConfig = field(default_factory=AssetConfig)
    LOADING_LAYOUT: LoadingLayoutConfig = field(default_factory=LoadingLayoutConfig)
    LOADING_ANIMATION: LoadingAnimationConfig = field(default_factory=LoadingAnimationConfig)
    LOADING_MESSAGES: LoadingMessagesConfig = field(default_factory=LoadingMessagesConfig)
    UI_THEME: UIThemeConfig = field(default_factory=UIThemeConfig)
    NETWORK: NetworkConfig = field(default_factory=NetworkConfig)
    SCREEN_NAMES: ScreenNames = field(default_factory=ScreenNames)
    SECURITY: SecurityConfig = field(default_factory=SecurityConfig)
    APP_NAME: str = "Bloquinhos"

SETTINGS = Settings()

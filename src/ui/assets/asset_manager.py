import os
from typing import Dict, Optional, Callable
import pygame
from engine.tile import Tile, Tetromino
from settings import SETTINGS
from utils.path_manager import PathManager
from utils.logger import log
from ui.assets.progress_tracker import ProgressTracker
from ui.assets.loaders import ImageLoader, AudioLoader, FontLoader, TileLoader

class AssetManager:
    def __init__(self):
        if pygame.mixer.get_init():
            pygame.mixer.quit()
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=2048)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(32)
        
        self._image_loader = ImageLoader(PathManager.get_image_path())
        self._audio_loader = AudioLoader(PathManager.get_audio_path())
        self._font_loader = FontLoader(PathManager.get_font_path())
        self._tile_loader = TileLoader()
    
    def load_all_assets(
        self, 
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> Dict[str, int]:
        log.debug("Scanning asset directories")
        
        img_dir = PathManager.get_image_path()
        aud_dir = PathManager.get_audio_path()
        
        img_files = [f for f in os.listdir(img_dir) if f.endswith(SETTINGS.ASSETS.IMAGE_EXTENSIONS)]
        aud_files = os.listdir(aud_dir)
        wav_files = [f for f in aud_files if f.endswith(SETTINGS.ASSETS.SFX_EXTENSIONS)]
        ogg_files = [f for f in aud_files if f.endswith(SETTINGS.ASSETS.MUSIC_EXTENSIONS)]
        font_sizes = list(SETTINGS.UI_TYPOGRAPHY.all_sizes)
        tile_count = len(list(Tetromino))
        
        total_items = len(img_files) + len(wav_files) + len(ogg_files) + len(font_sizes) + tile_count
        
        log.info(f"Loading {total_items} game assets ({len(img_files)} images, {len(wav_files)} SFX, {len(ogg_files)} music, {len(font_sizes)} fonts, {tile_count} tiles)")
        
        progress_tracker = ProgressTracker(total_items, progress_callback)
        
        img_count = self._image_loader.load(img_files, progress_tracker)
        sfx_count, music_count = self._audio_loader.load_audio(wav_files, ogg_files, progress_tracker)
        font_count = self._font_loader.load(font_sizes, progress_tracker)
        
        tilemap_key = SETTINGS.TILEMAP.FILENAME
        tilemap = self._image_loader.get_image(tilemap_key)
        tiles_loaded = self._tile_loader.load_tiles(tilemap, progress_tracker)
        
        return {
            "images": img_count,
            "sfx": sfx_count,
            "music": music_count,
            "fonts": font_count,
            "tiles": tiles_loaded
        }
    
    def get_image(self, filename: str) -> pygame.Surface:
        return self._image_loader.get_image(filename)
    
    def get_sfx(self, filename: str) -> pygame.mixer.Sound:
        return self._audio_loader.get_sfx(filename)
    
    def get_music(self, filename: str) -> str:
        return self._audio_loader.get_music(filename)
    
    def get_font(self, size: int) -> pygame.font.Font:
        return self._font_loader.get_font(size)
    
    def get_tile_surface(self, tile: Tile) -> pygame.Surface:
        return self._tile_loader.get_tile_surface(tile)

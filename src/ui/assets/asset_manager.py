import os
from typing import Dict, List, TypedDict

import pygame
from engine.tile import Tile, Tetromino
from settings import SETTINGS
from utils.path_manager import PathManager
from ui.assets.loaders import ImageLoader, AudioLoader, FontLoader, TileLoader

class AssetFileMap(TypedDict):
    images: List[str]
    sfx: List[str]
    music: List[str]
    fonts: List[int]
    tiles: List[Tetromino]

class AssetManager:
    def __init__(self):
        self._image_loader = ImageLoader(PathManager.get_image_path())
        self._audio_loader = AudioLoader(PathManager.get_audio_path())
        self._font_loader = FontLoader(PathManager.get_font_path())
        self._tile_loader = TileLoader()

    def list_asset_files(self) -> AssetFileMap:
        img_dir = PathManager.get_image_path()
        aud_dir = PathManager.get_audio_path()

        img_files = [f for f in os.listdir(img_dir) if f.endswith(SETTINGS.ASSETS.IMAGE_EXTENSIONS)]
        aud_files = os.listdir(aud_dir)
        wav_files = [f for f in aud_files if f.endswith(SETTINGS.ASSETS.SFX_EXTENSIONS)]
        ogg_files = [f for f in aud_files if f.endswith(SETTINGS.ASSETS.MUSIC_EXTENSIONS)]
        font_sizes = list(SETTINGS.UI_TYPOGRAPHY.all_sizes)
        tiles = list(Tetromino)

        return {
            "images": img_files,
            "sfx": wav_files,
            "music": ogg_files,
            "fonts": font_sizes,
            "tiles": tiles,
        }
    
    def get_image(self, filename: str) -> pygame.Surface:
        return self._image_loader.get_image(filename)

    def register_preloaded_image(self, name: str, surface: pygame.Surface) -> None:
        cached_surface = surface.convert_alpha() if pygame.display.get_surface() else surface
        self._image_loader.register_image(name, cached_surface)

    def load_and_register_image(self, filename: str) -> None:
        image_path = os.path.join(PathManager.get_image_path(), filename)
        surface = pygame.image.load(image_path)
        if pygame.display.get_surface():
            surface = surface.convert_alpha()
        name = filename.rsplit('.', 1)[0]
        self._image_loader.register_image(name, surface)
    
    def get_sfx(self, filename: str) -> pygame.mixer.Sound:
        return self._audio_loader.get_sfx(filename)

    def load_and_register_sfx(self, filename: str) -> None:
        sfx_path = os.path.join(PathManager.get_audio_path(), filename)
        sound = pygame.mixer.Sound(sfx_path)
        name = filename.rsplit('.', 1)[0]
        self._audio_loader.register_sfx(name, sound)
    
    def get_music(self, filename: str) -> str:
        return self._audio_loader.get_music(filename)

    def register_music_path(self, filename: str) -> None:
        music_path = os.path.join(PathManager.get_audio_path(), filename)
        name = filename.rsplit('.', 1)[0]
        self._audio_loader.register_music(name, music_path)
    
    def get_font(self, size: int) -> pygame.font.Font:
        return self._font_loader.get_font(size)

    def register_preloaded_fonts(self, fonts: Dict[int, pygame.font.Font]) -> None:
        for size, font in fonts.items():
            self._font_loader.register_font(size, font)

    def load_and_register_font(self, size: int) -> None:
        font_path = os.path.join(PathManager.get_font_path(), SETTINGS.UI_TYPOGRAPHY.FONT_NAME)
        font = pygame.font.Font(font_path, size)
        self._font_loader.register_font(size, font)
    
    def get_tile_surface(self, tile: Tile) -> pygame.Surface:
        return self._tile_loader.get_tile_surface(tile)

    def load_and_register_tile(self, tetromino: Tetromino) -> None:
        tile = tetromino.tile
        tilemap = self._image_loader.get_image(SETTINGS.TILEMAP.FILENAME)
        scaled_tile = self._tile_loader.create_scaled_tile(tilemap, tile)
        self._tile_loader.register_tile(tile, scaled_tile)

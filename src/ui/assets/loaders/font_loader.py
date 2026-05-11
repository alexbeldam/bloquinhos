import os
from typing import Dict
import pygame
from ui.assets.loaders.base_loader import BaseLoader
from settings import SETTINGS
from utils.logger import log

class FontLoader(BaseLoader):
    def __init__(self, directory: str):
        super().__init__(directory, "🔤", "fonts")
        self._fonts: Dict[int, pygame.font.Font] = {}
        self._font_path = os.path.join(directory, SETTINGS.ASSETS.FONT_NAME)
    
    def _load_single(self, size: int) -> bool:
        font = pygame.font.Font(self._font_path, size)
        self._fonts[size] = font
        return True
    
    def _format_item(self, item: int) -> str:
        return f"font size {item}"
    
    def get_font(self, size: int) -> pygame.font.Font:
        if size not in self._fonts:
            log.debug(f"🔧 Font size {size} not cached, creating dynamically...")
            try:
                font = pygame.font.Font(self._font_path, size)
                self._fonts[size] = font
            except Exception as e:
                log.error(f"❌ Failed to create font size {size}: {e}")
                raise
        return self._fonts[size]

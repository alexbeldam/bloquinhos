import os
from typing import Dict
import pygame
from ui.assets.loaders.base_loader import BaseLoader

class ImageLoader(BaseLoader):
    def __init__(self, directory: str):
        super().__init__(directory, "images")
        self._images: Dict[str, pygame.Surface] = {}
    
    def _load_single(self, filename: str) -> bool:
        img_path = os.path.join(self._directory, filename)
        surface = pygame.image.load(img_path)
        
        if pygame.display.get_surface():
            surface = surface.convert_alpha()
        
        name = filename.rsplit('.', 1)[0]
        self._images[name] = surface
        return True
    
    def _format_item(self, item: str) -> str:
        return item
    
    def get_image(self, filename: str) -> pygame.Surface:
        if filename not in self._images:
            raise KeyError(f"Image '{filename}' not found in loaded assets")
        return self._images[filename]
    
    @property
    def images(self) -> Dict[str, pygame.Surface]:
        return self._images

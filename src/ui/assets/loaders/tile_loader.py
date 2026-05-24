from typing import Dict
import pygame
from engine.tile import Tile, Tetromino
from settings import SETTINGS
from utils.logger import log
from ui.assets.progress_tracker import ProgressTracker

class TileLoader:
    def __init__(self):
        self._tiles: Dict[Tile, pygame.Surface] = {}
    
    def load_tiles(
        self, 
        tilemap: pygame.Surface, 
        progress_tracker: ProgressTracker
    ) -> int:
        log.info("Loading tiles...")
        count = 0
        
        tiles_to_load = [t.tile for t in Tetromino]
        
        for tile in tiles_to_load:
            log.debug(f"Loading tile: {tile.name}")
            try:
                scaled_tile = self.create_scaled_tile(tilemap, tile)
                self._tiles[tile] = scaled_tile
                count += 1
            except Exception as e:
                log.error(f"Failed to load tile {tile.name}: {e}")
            
            progress_tracker.update(f"Loading tile: {tile.name}")
        
        log.info(f"Loaded {count} tiles.")
        return count
    
    def get_tile_surface(self, tile: Tile) -> pygame.Surface:
        if tile not in self._tiles:
            raise KeyError(f"Tile '{tile.name}' not found in loaded assets")
        return self._tiles[tile]

    def register_tile(self, tile: Tile, surface: pygame.Surface) -> None:
        self._tiles[tile] = surface

    def create_scaled_tile(self, tilemap: pygame.Surface, tile: Tile) -> pygame.Surface:
        tile_info = SETTINGS.TILE_COLORS.get_tile_info(tile)
        index = tile_info.index

        tile_width = tilemap.get_width() // SETTINGS.TILEMAP.COLUMNS
        tile_height = tilemap.get_height() // SETTINGS.TILEMAP.ROWS
        row = index // SETTINGS.TILEMAP.COLUMNS
        col = index % SETTINGS.TILEMAP.COLUMNS

        x = col * tile_width
        y = row * tile_height
        tile_surface = tilemap.subsurface((x, y, tile_width, tile_height))
        tile_size = SETTINGS.GRID.TILE_SIZE
        return pygame.transform.scale(tile_surface, (tile_size, tile_size))

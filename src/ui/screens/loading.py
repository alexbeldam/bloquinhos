import threading
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Tuple

import pygame

from engine.shapes import get_shape_coordinates
from engine.tile import Tetromino
from settings import SETTINGS
from ui.assets import AssetManager
from ui.screen import Screen

if TYPE_CHECKING:
    from service_container import ServiceContainer


class MorphingEngine:
    def __init__(self, total_loop_time: float = 5.0):
        self.tetromino_order = [
            Tetromino.T,
            Tetromino.S,
            Tetromino.Z,
            Tetromino.O,
            Tetromino.I,
            Tetromino.J,
            Tetromino.L,
        ]
        
        self.colors = [
            SETTINGS.TILE_COLORS.get_tile_info(tetromino.tile).color
            for tetromino in self.tetromino_order
        ]
        
        self.current_idx = 0
        self.next_idx = 1
        
        initial_coords = get_shape_coordinates(self.tetromino_order[0])
        self.active_pos = [[float(x), float(y)] for x, y in initial_coords]
        self.current_color = list(self.colors[0])
        
        self.anim_timer = 0.0
        num_shapes = len(self.tetromino_order)
        self.anim_interval = (total_loop_time * 1000) / num_shapes
        
        base_speed = 0.15
        reference_interval = 800
        speed_multiplier = reference_interval / self.anim_interval
        unclamped_speed = base_speed * speed_multiplier
        self.morph_speed = max(0.1, min(0.6, unclamped_speed))

    def update(self, dt: float) -> None:
        dt_ms = dt * 1000
        
        target_coords = get_shape_coordinates(self.tetromino_order[self.next_idx])
        target_color = self.colors[self.next_idx]

        # Smoothly interpolate block positions toward target shape
        num_blocks = 4
        coord_dimensions = 2  # x and y
        for block_idx in range(num_blocks):
            for coord_idx in range(coord_dimensions):
                current_value = self.active_pos[block_idx][coord_idx]
                target_value = target_coords[block_idx][coord_idx]
                delta = target_value - current_value
                self.active_pos[block_idx][coord_idx] += delta * self.morph_speed

        # Smoothly interpolate RGB color values
        rgb_channels = 3
        for channel_idx in range(rgb_channels):
            current_channel = self.current_color[channel_idx]
            target_channel = target_color[channel_idx]
            delta = target_channel - current_channel
            self.current_color[channel_idx] += delta * self.morph_speed

        # Cycle to next shape when timer expires
        self.anim_timer += dt_ms
        if self.anim_timer >= self.anim_interval:
            self.anim_timer = 0.0
            self.current_idx = self.next_idx
            num_shapes = len(self.tetromino_order)
            self.next_idx = (self.next_idx + 1) % num_shapes

    def draw(self, surface: pygame.Surface, center_x: int, center_y: int, scale: int) -> None:
        # Calculate center of mass for all blocks
        num_blocks = 4
        total_x = sum(pos[0] for pos in self.active_pos)
        total_y = sum(pos[1] for pos in self.active_pos)
        avg_x = total_x / num_blocks
        avg_y = total_y / num_blocks
        
        draw_color = tuple(map(int, self.current_color))

        # Draw each block relative to center of mass
        for x, y in self.active_pos:
            # Calculate position relative to center
            rel_x = (x - avg_x) * scale
            rel_y = (y - avg_y) * scale
            
            # Convert to screen coordinates
            half_block = scale / 2
            draw_x = round(center_x + rel_x - half_block)
            draw_y = round(center_y + rel_y - half_block)
            
            block_rect = pygame.Rect(draw_x, draw_y, scale, scale)
            
            # Fill block with color
            pygame.draw.rect(surface, draw_color, block_rect)
            
            # Draw highlight lines (top and left)
            top_left = (draw_x, draw_y)
            top_right = (draw_x + scale - 1, draw_y)
            bottom_left = (draw_x, draw_y + scale - 1)
            pygame.draw.line(surface, SETTINGS.UI_THEME.WHITE, top_left, top_right, 1)
            pygame.draw.line(surface, SETTINGS.UI_THEME.WHITE, top_left, bottom_left, 1)

            # Draw border
            border_width = SETTINGS.LOADING_LAYOUT.BORDER_WIDTH
            pygame.draw.rect(surface, SETTINGS.UI_THEME.GRAY_DARK, block_rect, border_width)


class LoadingScreen(Screen):
    def __init__(
        self, 
        assets: Optional[AssetManager] = None,
        on_complete: Optional[Callable[[], None]] = None,
        init_callbacks: Optional[Dict[str, Callable[[], None]]] = None,
        services: Optional['ServiceContainer'] = None
    ) -> None:
        super().__init__(assets)
        
        animation_cycle_time = SETTINGS.LOADING_ANIMATION.ANIMATION_CYCLE_TIME
        self.engine = MorphingEngine(animation_cycle_time)
        
        scale_multiplier = SETTINGS.LOADING_LAYOUT.BLOCK_SCALE_MULTIPLIER
        self.block_scale = int(SETTINGS.GRID.TILE_SIZE * scale_multiplier)
        
        self.progress = 0
        self.total = 0
        self.visual_progress = 0.0
        
        self.current_message = ""
        self.actual_loading_complete = False
        self.loading_complete = False
        self.loading_started = False
        self.animation_started = False
        
        self._progress_lock = threading.Lock()
        
        self.on_complete = on_complete
        self.init_callbacks = init_callbacks or {}
        self.services = services

    def update_progress(self, message: str, current: int, total: int) -> None:
        with self._progress_lock:
            self.current_message = message
            self.progress = current
            self.total = total
            
            if current >= total:
                self.actual_loading_complete = True

    def handle_events(self, events: List[pygame.event.Event]) -> Optional[str]:
        for event in events:
            if event.type == pygame.QUIT:
                return SETTINGS.SCREEN_NAMES.QUIT
            if event.type == pygame.KEYDOWN and self.loading_complete:
                if self.on_complete:
                    self.on_complete()
                return SETTINGS.SCREEN_NAMES.MENU
        return None

    def update(self, delta_time: float) -> Optional[str]:
        if not self.loading_started:
            self.loading_started = True
            from utils.logger import log
            
            def run_initialization():
                
                try:
                    if 'services' in self.init_callbacks:
                        self.update_progress(SETTINGS.LOADING_MESSAGES.SERVICES, 0, 100)
                        log.debug("Starting services initialization phase")
                        self.init_callbacks['services']()
                        if self.services and not self.assets:
                            try:
                                self.assets = self.services.asset_manager
                            except RuntimeError:
                                pass
                        self.update_progress(SETTINGS.LOADING_MESSAGES.SERVICES, 10, 100)
                    else:
                        self.update_progress(SETTINGS.LOADING_MESSAGES.SERVICES, 10, 100)
                    
                    if 'network' in self.init_callbacks:
                        self.update_progress(SETTINGS.LOADING_MESSAGES.NETWORK, 10, 100)
                        log.debug("Starting network initialization phase")
                        self.init_callbacks['network']()
                        self.update_progress(SETTINGS.LOADING_MESSAGES.NETWORK, 25, 100)
                    else:
                        self.update_progress(SETTINGS.LOADING_MESSAGES.NETWORK, 25, 100)
                    
                    if 'game' in self.init_callbacks:
                        self.update_progress(SETTINGS.LOADING_MESSAGES.GAME, 25, 100)
                        log.debug("Starting game initialization phase")
                        self.init_callbacks['game']()
                        self.update_progress(SETTINGS.LOADING_MESSAGES.GAME, 35, 100)
                    else:
                        self.update_progress(SETTINGS.LOADING_MESSAGES.GAME, 35, 100)
                    
                    if 'screens' in self.init_callbacks:
                        self.update_progress(SETTINGS.LOADING_MESSAGES.SCREENS, 35, 100)
                        log.debug("Starting screen creation phase")
                        self.init_callbacks['screens']()
                        self.update_progress(SETTINGS.LOADING_MESSAGES.SCREENS, 45, 100)
                    else:
                        self.update_progress(SETTINGS.LOADING_MESSAGES.SCREENS, 45, 100)
                    
                    if self.assets is not None:
                        self.update_progress(SETTINGS.LOADING_MESSAGES.ASSETS, 45, 100)
                        log.debug("Starting asset loading phase")
                        asset_stats = self.assets.load_all_assets(self._asset_progress_callback)
                        log.info(
                            f"All assets loaded successfully - "
                            f"{asset_stats['images']} images, {asset_stats['sfx']} SFX, {asset_stats['music']} music tracks, "
                            f"{asset_stats['fonts']} fonts, {asset_stats['tiles']} tile sprites"
                        )
                    
                    log.info("All initialization phases completed successfully")
                    
                except Exception as e:
                    log.error(f"Error during initialization: {e}", exc_info=True)
                    with self._progress_lock:
                        self.actual_loading_complete = True
            
            loading_thread = threading.Thread(target=run_initialization, daemon=True)
            loading_thread.start()
        
        with self._progress_lock:
            current_total = self.total
            current_progress = self.progress
            is_complete = self.actual_loading_complete
        
        if current_total > 0:
            actual_progress = current_progress / current_total
            progress_delta = actual_progress - self.visual_progress
            smooth_speed = SETTINGS.LOADING_ANIMATION.PROGRESS_SMOOTH_SPEED
            self.visual_progress += progress_delta * smooth_speed * delta_time
            self.visual_progress = min(self.visual_progress, 1.0)
        
        visual_progress_threshold = SETTINGS.LOADING_ANIMATION.PROGRESS_THRESHOLD
        if is_complete and self.visual_progress >= visual_progress_threshold:
            self.loading_complete = True
        
        if self.animation_started:
            self.engine.update(delta_time)
        
        return None
    
    def _asset_progress_callback(self, message: str, current: int, total: int) -> None:
        if total > 0:
            asset_fraction = current / total
            mapped_progress = 45 + int(asset_fraction * 55)
        else:
            mapped_progress = 45
        
        with self._progress_lock:
            self.current_message = SETTINGS.LOADING_MESSAGES.ASSETS
            self.progress = mapped_progress
            self.total = 100
            
            if current >= total:
                self.actual_loading_complete = True

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(SETTINGS.UI_THEME.BG_DARKER)
        
        screen_center_x = surface.get_width() // 2
        screen_center_y = surface.get_height() // 2
        animation_offset_y = 60
        animation_y = screen_center_y - animation_offset_y
        
        self.engine.draw(surface, screen_center_x, animation_y, self.block_scale)
        
        if not self.animation_started:
            self.animation_started = True
        
        ui_element_y = animation_y + 140
        if self.loading_complete:
            self._draw_text(
                surface,
                "Press any key to continue",
                SETTINGS.UI_TYPOGRAPHY.BODY,
                SETTINGS.UI_THEME.YELLOW,
                (screen_center_x, ui_element_y),
            )
        else:
            self._draw_progress_bar(surface, screen_center_x, ui_element_y)
            
            with self._progress_lock:
                display_message = self.current_message
            
            if display_message:
                message_y = ui_element_y + 40
                self._draw_text(
                    surface,
                    display_message,
                    SETTINGS.UI_TYPOGRAPHY.SMALL,
                    SETTINGS.UI_THEME.TEXT_MUTED,
                    (screen_center_x, message_y),
                )

    def _draw_progress_bar(self, surface: pygame.Surface, center_x: int, center_y: int) -> None:
        # Calculate bar dimensions
        tile_size = SETTINGS.GRID.TILE_SIZE
        bar_width = int(tile_size * SETTINGS.LOADING_LAYOUT.PROGRESS_BAR_WIDTH_MULTIPLIER)
        bar_height = int(tile_size * SETTINGS.LOADING_LAYOUT.PROGRESS_BAR_HEIGHT_RATIO)
        border_radius = bar_height // 2
        
        # Position bar centered on screen
        bar_x = center_x - bar_width // 2
        bar_y = center_y - bar_height // 2
        
        # Draw background
        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(surface, SETTINGS.UI_THEME.BG_MEDIUM, bg_rect, border_radius=border_radius)
        
        # Draw progress fill
        if self.visual_progress > 0:
            fill_width = int(bar_width * self.visual_progress)
            fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
            pygame.draw.rect(surface, SETTINGS.UI_THEME.PURPLE, fill_rect, border_radius=border_radius)
        
        # Draw border
        border_width = SETTINGS.LOADING_LAYOUT.BORDER_WIDTH
        pygame.draw.rect(surface, SETTINGS.UI_THEME.GRAY_DARK, bg_rect, border_width, border_radius=border_radius)

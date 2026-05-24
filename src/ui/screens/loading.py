import threading
import time
from typing import TYPE_CHECKING, Callable, Dict, List, Optional

import pygame

from settings import SETTINGS
from ui.assets import AssetManager
from ui.screen import Screen
from ui.screens.loading_animation import MorphingEngine
from ui.screens.loading_pipeline import LoadingPipeline
from utils.logger import log

if TYPE_CHECKING:
    from service_container import ServiceContainer


class LoadingScreen(Screen):
    def __init__(
        self, 
        assets: Optional[AssetManager] = None,
        on_complete: Optional[Callable[[], None]] = None,
        init_callbacks: Optional[Dict[str, Callable[[], None]]] = None,
        services: Optional['ServiceContainer'] = None,
        ui_fonts: Optional[Dict[int, pygame.font.Font]] = None,
        preloaded_icon: Optional[pygame.Surface] = None,
    ) -> None:
        super().__init__(assets)
        self._ui_fonts: Dict[int, pygame.font.Font] = ui_fonts or {}
        self._preloaded_icon = preloaded_icon
        
        self.engine = MorphingEngine()
        
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
        
        self.error_state = False
        self.error_message = ""
        self._queue_drain_logged = False
        self._visual_completion_logged = False
        self._preloaded_fonts_registered = False

        self._pipeline = LoadingPipeline()
        self._progress_lock = threading.Lock()
        
        self.on_complete = on_complete
        self.init_callbacks = init_callbacks or {}
        self.services = services

    def _font(self, size: int) -> pygame.font.Font:
        if self.assets is not None:
            if self._ui_fonts and not self._preloaded_fonts_registered:
                self.assets.register_preloaded_fonts(self._ui_fonts)
                self._preloaded_fonts_registered = True
            try:
                return self.assets.get_font(size)
            except (KeyError, FileNotFoundError, pygame.error):
                pass
        if size in self._ui_fonts:
            return self._ui_fonts[size]
        return pygame.font.Font(None, size)

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
            if event.type == pygame.KEYDOWN:
                if self.error_state and event.key == pygame.K_ESCAPE:
                    return SETTINGS.SCREEN_NAMES.QUIT
                elif self.loading_complete and not self.error_state:
                    if self.on_complete:
                        self.on_complete()
                    return SETTINGS.SCREEN_NAMES.MENU
        return None

    def update(self, delta_time: float) -> Optional[str]:
        if not self.loading_started:
            self.loading_started = True
            
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
                        log.debug("Preparing asset loading work items")
                        self._prepare_asset_work_items()
                    
                    log.info("Background initialization completed, asset loading queued")
                except Exception as e:
                    log.error(f"Error during initialization: {e}", exc_info=True)
                    with self._progress_lock:
                        self.error_state = True
                        self.error_message = str(e)
                        self.progress = 100
                        self.total = 100
                        self.actual_loading_complete = True
            
            loading_thread = threading.Thread(target=run_initialization, daemon=True)
            loading_thread.start()
        
        target_frame_time = 1.0 / SETTINGS.DISPLAY.FPS
        effective_delta = max(delta_time, target_frame_time)
        frame_budget = effective_delta * SETTINGS.LOADING_ANIMATION.FRAME_BUDGET_RATIO
        frame_start = time.perf_counter()

        with self._progress_lock:
            has_error = self.error_state

        processed_items = 0
        while not has_error and self._pipeline.has_pending_work():
            if processed_items > 0 and time.perf_counter() - frame_start >= frame_budget:
                break
            try:
                work_item = self._pipeline.get_next_work_item()
                self._pipeline.process_work_item(work_item, self.services, self.assets)
                processed_items += 1
                
                with self._progress_lock:
                    self.progress = work_item.progress_value
            except Exception as e:
                log.error(f"Failed to process work item: {e}", exc_info=True)
                with self._progress_lock:
                    self.error_state = True
                    self.error_message = str(e)
                    self.progress = 100
                    self.total = 100
                    self.actual_loading_complete = True
                    has_error = True
                break
        
        with self._progress_lock:
            current_total = self.total
            current_progress = self.progress
            is_complete = self.actual_loading_complete
            has_error = self.error_state

        if is_complete and not has_error and not self._pipeline.has_pending_work() and not self._queue_drain_logged:
            self._queue_drain_logged = True
            log.info("Asset queue drained")
        
        if current_total > 0:
            actual_progress = current_progress / current_total
            progress_delta = actual_progress - self.visual_progress
            smooth_speed = SETTINGS.LOADING_ANIMATION.PROGRESS_SMOOTH_SPEED
            self.visual_progress += progress_delta * smooth_speed * delta_time
            self.visual_progress = min(self.visual_progress, 1.0)
        
        visual_progress_threshold = SETTINGS.LOADING_ANIMATION.PROGRESS_THRESHOLD
        if is_complete and self.visual_progress >= visual_progress_threshold:
            self.loading_complete = True
            if not has_error and not self._visual_completion_logged:
                self._visual_completion_logged = True
                log.info("Loading visual threshold reached")
        
        if self.animation_started:
            self.engine.update(delta_time)
        
        return None
    
    def _prepare_asset_work_items(self) -> None:
        if self._ui_fonts and not self._preloaded_fonts_registered:
            self.assets.register_preloaded_fonts(self._ui_fonts)
            self._preloaded_fonts_registered = True

        skip_image_files: set[str] = set()
        if self._preloaded_icon is not None:
            self.assets.register_preloaded_image("logo", self._preloaded_icon)
            skip_image_files.add(SETTINGS.PATHS.ICON_FILE)

        self._pipeline = LoadingPipeline(
            skip_font_sizes=set(self._ui_fonts.keys()),
            skip_image_files=skip_image_files,
        )
        total_assets = self._pipeline.prepare_asset_work_items(self.assets)
        log.info(f"Queuing {total_assets} assets for loading")

        with self._progress_lock:
            self.total = 100
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
        
        if self.error_state:
            self._draw_text(
                surface,
                "Loading Failed",
                SETTINGS.UI_TYPOGRAPHY.TITLE,
                SETTINGS.UI_THEME.RED,
                (screen_center_x, ui_element_y),
            )
            
            error_msg_y = ui_element_y + 50
            max_error_width = int(surface.get_width() * 0.8)
            self._draw_wrapped_text(
                surface,
                self.error_message,
                SETTINGS.UI_TYPOGRAPHY.SMALL,
                SETTINGS.UI_THEME.TEXT_MUTED,
                (screen_center_x, error_msg_y),
                max_error_width,
            )
            
            quit_msg_y = error_msg_y + 60
            self._draw_text(
                surface,
                "Press ESC to quit",
                SETTINGS.UI_TYPOGRAPHY.BODY,
                SETTINGS.UI_THEME.YELLOW,
                (screen_center_x, quit_msg_y),
            )
        
        elif self.loading_complete:
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

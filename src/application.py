import os
from typing import TYPE_CHECKING, Dict, Optional

import pygame

from game_initializer import GameInitializer
from service_container import ServiceContainer
from settings import SETTINGS
from ui.screen_factory import ScreenFactory
from utils.path_manager import PathManager
import utils.env_manager as env
from utils.logger import log

if TYPE_CHECKING:
    from engine import GameController, GameSession


class Application:
    def __init__(self):
        self.services: ServiceContainer = ServiceContainer()
        self.game_initializer: Optional[GameInitializer] = None
        self.game_controller: Optional['GameController'] = None
        self.game_session: Optional['GameSession'] = None
        self.initialized: bool = False
    
    def run(self) -> None:
        try:
            self._load_environment()
            self._initialize_pygame()
            icon = self._load_icon()
            ui_fonts = self._preload_ui_fonts()
            self._create_splash_window(icon)
            pygame.event.pump()
            
            init_callbacks = {
                'services': self._init_services,
                'network': self._init_network_connection,
                'game': self._init_game,
                'screens': self._init_screens
            }
            
            loading_screen = ScreenFactory.create_loading_screen(
                self.services,
                init_callbacks=init_callbacks,
                ui_fonts=ui_fonts,
                preloaded_icon=icon,
            )
            self.services.screen_manager.register_screen(
                SETTINGS.SCREEN_NAMES.LOADING,
                loading_screen
            )
            
            self.services.screen_manager.switch_to(SETTINGS.SCREEN_NAMES.LOADING)

            if self.services.screen_manager.current_screen:
                self.services.screen_manager.current_screen.render(self.services.screen_manager.surface)
                pygame.display.flip()
            
            log.info("Starting loading screen")
            
            self.services.screen_manager.run()
            
        finally:
            self._cleanup()
    
    def _load_environment(self) -> None:
        env.load_env_vars()
        log.debug("Environment configuration loaded")
    
    def _initialize_pygame(self) -> None:
        pygame.display.init()
        pygame.font.init()
        log.debug(f"Pygame {pygame.version.ver} initialized")
    
    def _preload_ui_fonts(self) -> Dict[int, pygame.font.Font]:
        font_path = os.path.join(PathManager.get_font_path(), SETTINGS.UI_TYPOGRAPHY.FONT_NAME)
        sizes = [SETTINGS.UI_TYPOGRAPHY.SMALL, SETTINGS.UI_TYPOGRAPHY.BODY, SETTINGS.UI_TYPOGRAPHY.TITLE]
        try:
            fonts = {size: pygame.font.Font(font_path, size) for size in sizes}
            log.debug(f"Pre-loaded {len(fonts)} UI fonts for loading screen")
            return fonts
        except Exception as e:
            log.warning(f"Could not pre-load UI fonts: {e}")
            return {}
    
    def _load_icon(self) -> Optional[pygame.Surface]:
        try:
            icon_path = PathManager.get_icon_path()

            if os.path.exists(icon_path):
                icon = pygame.image.load(icon_path)
                log.debug("Loaded application icon")
                return icon
        except (FileNotFoundError, pygame.error) as e:
            log.debug(f"Could not load icon: {e}")
        return None
    
    def _create_splash_window(self, icon: Optional[pygame.Surface] = None) -> None:
        splash_size = SETTINGS.GRID.TILE_SIZE * SETTINGS.LOADING_LAYOUT.SPLASH_SIZE_MULTIPLIER

        log.debug(f"Creating splash screen ({splash_size}x{splash_size})")

        self.services.initialize_screen_manager(
            width=splash_size,
            height=splash_size,
            decorated=False,
            icon=icon
        )
    
    def _init_services(self) -> None:
        log.debug("Initializing services")
        self.services.initialize_assets()
        self.services.initialize_audio()
        self.services.initialize_network()
    
    def _init_network_connection(self) -> None:
        log.debug("Waiting for database connection...")
        if not self.services.network_manager.wait_for_connection(timeout=SETTINGS.NETWORK.CONNECTION_TIMEOUT):
            log.warning(f"Database connection timeout after {SETTINGS.NETWORK.CONNECTION_TIMEOUT}s - running offline mode")
    
    def _init_game(self) -> None:
        log.debug("Initializing game controller and session...")
        self.game_initializer = GameInitializer(self.services)
        self.game_controller, self.game_session = self.game_initializer.initialize()
        self.initialized = True
        log.debug("Game initialization complete")
    
    def _init_screens(self) -> None:
        log.debug("Creating game screens...")
        game_screens = ScreenFactory.create_game_screens(
            self.game_controller,
            self.game_session,
            self.services
        )
        ScreenFactory.register_screens(self.services.screen_manager, game_screens)
        log.debug(f"Registered {len(game_screens)} game screens")
    
    def _cleanup(self) -> None:
        log.debug("Shutting down application")
        pygame.quit()
        log.info("Application closed")

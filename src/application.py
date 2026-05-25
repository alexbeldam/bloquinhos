import os
from typing import TYPE_CHECKING, Dict, Optional

import pygame

from game_initializer import GameInitializer
from security.identity_manager import IdentityStatus
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
                'preferences': self._init_preferences,
                'network': self._init_network_connection,
                'game': self._init_game,
                'screens': self._init_screens,
                'identity': self._init_identity,
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
        self.services.screen_manager.set_transition_guard(self._guard_identity_transition)
    
    def _init_services(self) -> None:
        log.debug("Initializing services")
        self.services.initialize_assets()
        self.services.initialize_settings_manager()
        self.services.initialize_audio()

    def _init_preferences(self) -> None:
        settings_manager = self.services.settings_manager
        settings_manager.load()

        self._apply_audio_preferences()
        self._bind_runtime_settings_observers()

    def _apply_audio_preferences(self) -> None:
        settings_manager = self.services.settings_manager

        audio_settings = settings_manager.get("audio")
        master_settings = audio_settings.get("master", {})
        music_settings = audio_settings.get("music", {})
        sfx_settings = audio_settings.get("sfx", {})

        audio_manager = self.services.audio_manager
        audio_manager.set_master_volume(float(master_settings.get("volume", 0.7)))
        audio_manager.set_bgm_volume(float(music_settings.get("volume", 0.7)))
        audio_manager.set_sfx_volume(float(sfx_settings.get("volume", 0.8)))

        audio_manager.set_master_muted(bool(master_settings.get("muted", False)))
        audio_manager.set_bgm_muted(bool(music_settings.get("muted", False)))
        audio_manager.set_sfx_muted(bool(sfx_settings.get("muted", False)))

    def _bind_runtime_settings_observers(self) -> None:
        settings_manager = self.services.settings_manager

        def on_audio_setting_changed(path: str, _old_value, new_value) -> None:
            audio_manager = self.services.audio_manager

            if path == "audio.master.volume":
                audio_manager.set_master_volume(float(new_value))
            elif path == "audio.music.volume":
                audio_manager.set_bgm_volume(float(new_value))
            elif path == "audio.sfx.volume":
                audio_manager.set_sfx_volume(float(new_value))
            elif path == "audio.master.muted":
                audio_manager.set_master_muted(bool(new_value))
            elif path == "audio.music.muted":
                audio_manager.set_bgm_muted(bool(new_value))
            elif path == "audio.sfx.muted":
                audio_manager.set_sfx_muted(bool(new_value))

        settings_manager.subscribe("audio.*", on_audio_setting_changed)
    
    def _init_network_connection(self) -> None:
        start_offline = self.services.settings_manager.get_bool("network.start_offline")
        reconnect_policy = self.services.settings_manager.get("network.reconnect_policy")
        if not isinstance(reconnect_policy, str):
            reconnect_policy = "auto"

        network_manager = self.services.initialize_network(
            start_offline=start_offline,
            reconnect_policy=reconnect_policy,
        )
        self.services.initialize_identity_manager()
        network_manager.add_reconnect_listener(self._on_network_reconnected)

        if start_offline:
            log.info("Network startup configured for offline mode")
            return

        log.debug("Waiting for database connection...")
        if not network_manager.wait_for_connection(timeout=SETTINGS.NETWORK.CONNECTION_TIMEOUT):
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

    def _init_identity(self) -> str:
        log.debug("Checking stored player identity...")
        identity_manager = self.services.identity_manager
        result = identity_manager.inspect_identity()
        if result.status == IdentityStatus.VALID:
            return SETTINGS.SCREEN_NAMES.MENU
        self.services.set_identity_entry_context(
            result.status.value,
            return_screen=SETTINGS.SCREEN_NAMES.MENU,
            rename_required=True,
        )
        return SETTINGS.SCREEN_NAMES.IDENTITY_ENTRY

    def _on_network_reconnected(self) -> None:
        identity_manager = self.services.identity_manager
        result = identity_manager.revalidate_pending_identity()
        if result.status == IdentityStatus.CONFLICT:
            self.services.mark_identity_rename_required(result.status.value)
            log.warning("Identity rename deferred to the next safe transition")

    def _guard_identity_transition(self, next_screen: str) -> str:
        if next_screen in (SETTINGS.SCREEN_NAMES.QUIT, SETTINGS.SCREEN_NAMES.IDENTITY_ENTRY):
            return next_screen
        if not self.services.identity_rename_required:
            return next_screen

        safe_sources = {
            SETTINGS.SCREEN_NAMES.LOADING,
            SETTINGS.SCREEN_NAMES.MENU,
            SETTINGS.SCREEN_NAMES.RANKING,
            SETTINGS.SCREEN_NAMES.GAME_OVER,
        }
        current_screen = self.services.screen_manager.current_name
        if current_screen not in safe_sources:
            log.debug("Identity rename remains deferred until a safe transition")
            return next_screen

        self.services.set_identity_entry_context(
            self.services.identity_entry_reason,
            return_screen=next_screen,
            rename_required=True,
        )
        log.info("Identity rename required before continuing")
        return SETTINGS.SCREEN_NAMES.IDENTITY_ENTRY
    
    def _cleanup(self) -> None:
        log.debug("Shutting down application")
        try:
            self.services.settings_manager.save_on_exit()
        except RuntimeError:
            pass
        pygame.quit()
        log.info("Application closed")

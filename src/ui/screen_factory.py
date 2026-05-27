from typing import Callable, Dict, Optional

from engine import GameController, GameSession
from service_container import ServiceContainer
from settings import SETTINGS
from ui.screen import Screen
from ui.screens import (
    GameOverScreen,
    GameScreen,
    IdentityEntryScreen,
    LoadingScreen,
    MenuScreen,
    PauseScreen,
    RankingScreen,
)


class ScreenFactory:
    @staticmethod
    def create_loading_screen(
        services: ServiceContainer,
        init_callbacks: Optional[Dict[str, Callable[[], Optional[str]]]] = None,
        ui_fonts: Optional[Dict[int, 'pygame.font.Font']] = None,
        preloaded_icon: Optional['pygame.Surface'] = None,
    ) -> LoadingScreen:
        from utils.logger import log
        
        def on_loading_complete() -> None:
            try:
                icon = services.asset_manager.get_image("logo")
            except (KeyError, FileNotFoundError) as e:
                log.debug(f"Could not load icon for main window: {e}")
                icon = None
            
            screen_width = SETTINGS.GRID.GAME_WIDTH + SETTINGS.GRID.SIDEBAR_WIDTH
            screen_height = SETTINGS.GRID.GAME_HEIGHT
            services.screen_manager.reconfigure_window(
                screen_width,
                screen_height,
                SETTINGS.APP_NAME,
                icon,
                decorated=True
            )
            services.screen_manager.distribute_assets(services.asset_manager)
        
        try:
            asset_manager = services.asset_manager
        except RuntimeError:
            asset_manager = None
        
        return LoadingScreen(
            assets=asset_manager,
            on_complete=on_loading_complete,
            init_callbacks=init_callbacks,
            services=services,
            ui_fonts=ui_fonts,
            preloaded_icon=preloaded_icon,
        )
    
    @staticmethod
    def create_game_screens(
        game: GameController,
        session: GameSession,
        services: ServiceContainer
    ) -> Dict[str, Screen]:
        game_screen = GameScreen(game, session, assets=None, audio_manager=services.audio_manager)
        synchronizer = services.data_synchronizer
        
        return {
            SETTINGS.SCREEN_NAMES.IDENTITY_ENTRY: IdentityEntryScreen(
                identity_manager=services.identity_manager,
                reason_provider=lambda: services.identity_entry_reason,
                return_screen_provider=services.consume_identity_return_screen,
                assets=None,
                audio_manager=services.audio_manager,
            ),
            SETTINGS.SCREEN_NAMES.MENU: MenuScreen(assets=None, audio_manager=services.audio_manager),
            SETTINGS.SCREEN_NAMES.RANKING: RankingScreen(assets=None, audio_manager=services.audio_manager),
            SETTINGS.SCREEN_NAMES.GAME: game_screen,
            SETTINGS.SCREEN_NAMES.PAUSE: PauseScreen(game_screen, assets=None, audio_manager=services.audio_manager),
            SETTINGS.SCREEN_NAMES.GAME_OVER: GameOverScreen(
                game_screen,
                synchronizer=synchronizer,
                assets=None,
                audio_manager=services.audio_manager,
            ),
        }
    
    @staticmethod
    def register_screens(
        screen_manager,
        screens: Dict[str, Screen]
    ) -> None:
        for name, screen in screens.items():
            screen_manager.register_screen(name, screen)

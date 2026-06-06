from typing import Callable, Dict, Optional

from engine import GameController, GameSession
from service_container import ServiceContainer
from settings import SETTINGS
from ui.screen import Screen
from ui.screens import (
    CreditsScreen,
    GameOverScreen,
    GameScreen,
    IdentityEntryScreen,
    LoadingScreen,
    MenuScreen,
    PauseScreen,
    RankingScreen,
    SettingsScreen,
)
from utils.localization import tr


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
                tr("app.name"),
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
        game_screen = GameScreen(
            game,
            session,
            assets=None,
            audio_manager=services.audio_manager,
            settings_manager=services.settings_manager,
        )
        synchronizer = services.data_synchronizer

        def get_settings_return_screen() -> str:
            previous = services.screen_manager.previous_name
            if previous in (SETTINGS.SCREEN_NAMES.MENU, SETTINGS.SCREEN_NAMES.PAUSE):
                return previous
            return SETTINGS.SCREEN_NAMES.MENU

        settings_screen = SettingsScreen(
            return_screen_provider=get_settings_return_screen,
            assets=None,
            audio_manager=services.audio_manager,
            settings_manager=services.settings_manager,
        )

        leaderboard_manager = services.initialize_leaderboard_manager()

        screens = {
            SETTINGS.SCREEN_NAMES.IDENTITY_ENTRY: IdentityEntryScreen(
                identity_manager=services.identity_manager,
                synchronizer=synchronizer,
                reason_provider=lambda: services.identity_entry_reason,
                return_screen_provider=services.consume_identity_return_screen,
                assets=None,
                audio_manager=services.audio_manager,
            ),
            SETTINGS.SCREEN_NAMES.MENU: MenuScreen(assets=None, audio_manager=services.audio_manager),
            SETTINGS.SCREEN_NAMES.RANKING: RankingScreen(
                leaderboard_manager=leaderboard_manager,
                assets=None,
                audio_manager=services.audio_manager,
            ),
            SETTINGS.SCREEN_NAMES.GAME: game_screen,
            SETTINGS.SCREEN_NAMES.PAUSE: PauseScreen(game_screen, assets=None, audio_manager=services.audio_manager),
            SETTINGS.SCREEN_NAMES.GAME_OVER: GameOverScreen(
                game_screen,
                leaderboard_manager=leaderboard_manager,
                synchronizer=synchronizer,
                assets=None,
                audio_manager=services.audio_manager,
            ),
            SETTINGS.SCREEN_NAMES.SETTINGS: settings_screen,
            SETTINGS.SCREEN_NAMES.CREDITS: CreditsScreen(assets=None, audio_manager=services.audio_manager),
        }

        for screen_name in (
            SETTINGS.SCREEN_NAMES.MENU,
            SETTINGS.SCREEN_NAMES.IDENTITY_ENTRY,
            SETTINGS.SCREEN_NAMES.RANKING,
            SETTINGS.SCREEN_NAMES.SETTINGS,
        ):
            screens[screen_name].bind_network_manager(services.network_manager)

        return screens
    
    @staticmethod
    def register_screens(
        screen_manager,
        screens: Dict[str, Screen]
    ) -> None:
        for name, screen in screens.items():
            screen_manager.register_screen(name, screen)
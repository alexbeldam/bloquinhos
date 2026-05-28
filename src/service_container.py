import threading
from typing import TYPE_CHECKING, Optional

import pygame

from settings import SETTINGS

if TYPE_CHECKING:
    from security.identity_manager import IdentityManager
    from network.connection_manager import NetworkManager
    from network.data_synchronizer import DataSynchronizer
    from network.leaderboard_manager import LeaderboardManager
    from network.user_data_dao import UserDataDAO
    from ui.assets import AssetManager
    from ui.audio import AudioManager
    from ui.screen_manager import ScreenManager
    from utils.settings_manager import SettingsManager


class ServiceContainer:
    def __init__(self):
        self._asset_manager: Optional['AssetManager'] = None
        self._audio_manager: Optional['AudioManager'] = None
        self._network_manager: Optional['NetworkManager'] = None
        self._screen_manager: Optional['ScreenManager'] = None
        self._identity_manager: Optional['IdentityManager'] = None
        self._data_synchronizer: Optional['DataSynchronizer'] = None
        self._settings_manager: Optional['SettingsManager'] = None
        self._leaderboard_manager: Optional['LeaderboardManager'] = None
        self._identity_context_lock = threading.Lock()
        self._identity_entry_reason = "missing"
        self._identity_return_screen = SETTINGS.SCREEN_NAMES.MENU
        self._identity_rename_required = False
    
    def initialize_assets(self) -> 'AssetManager':
        if self._asset_manager is None:
            from ui.assets import AssetManager
            self._asset_manager = AssetManager()
        return self._asset_manager
    
    def initialize_audio(self) -> 'AudioManager':
        if self._audio_manager is None:
            from ui.audio import AudioManager
            if self._asset_manager is None:
                raise RuntimeError("AssetManager must be initialized before AudioManager")
            self._audio_manager = AudioManager(self._asset_manager)
        return self._audio_manager
    
    def initialize_network(self, start_offline: bool = False, reconnect_policy: str = "auto") -> 'NetworkManager':
        if self._network_manager is None:
            from network.connection_manager import NetworkManager
            self._network_manager = NetworkManager(
                start_offline=start_offline,
                reconnect_policy=reconnect_policy,
            )
        return self._network_manager

    def initialize_identity_manager(self) -> 'IdentityManager':
        if self._identity_manager is None:
            from security.identity_manager import IdentityManager

            network_manager = self.initialize_network()
            self._identity_manager = IdentityManager(network_manager=network_manager)
        return self._identity_manager

    def initialize_synchronizer(self) -> 'DataSynchronizer':
        if self._data_synchronizer is None:
            from network.data_synchronizer import DataSynchronizer
            from network.user_data_dao import UserDataDAO

            dao = UserDataDAO()
            network = self.initialize_network()
            self._data_synchronizer = DataSynchronizer(dao, network)
        return self._data_synchronizer

    def initialize_leaderboard_manager(self) -> 'LeaderboardManager':
        if self._leaderboard_manager is None:
            from network.leaderboard_manager import LeaderboardManager
            from network.user_data_dao import UserDataDAO

            dao = UserDataDAO()
            network = self.initialize_network()
            self._leaderboard_manager = LeaderboardManager(network, dao)
        return self._leaderboard_manager

    def initialize_settings_manager(self) -> 'SettingsManager':
        if self._settings_manager is None:
            from utils.settings_manager import SettingsManager
            self._settings_manager = SettingsManager()
        return self._settings_manager
    
    def initialize_screen_manager(
        self,
        width: int,
        height: int,
        decorated: bool = True,
        icon: Optional[pygame.Surface] = None
    ) -> 'ScreenManager':
        if self._screen_manager is None:
            from ui.screen_manager import ScreenManager
            self._screen_manager = ScreenManager(width, height, decorated, icon)
        return self._screen_manager
    
    @property
    def asset_manager(self) -> 'AssetManager':
        if self._asset_manager is None:
            raise RuntimeError("AssetManager not initialized. Call initialize_assets() first.")
        return self._asset_manager
    
    @property
    def audio_manager(self) -> 'AudioManager':
        if self._audio_manager is None:
            raise RuntimeError("AudioManager not initialized. Call initialize_audio() first.")
        return self._audio_manager
    
    @property
    def network_manager(self) -> 'NetworkManager':
        if self._network_manager is None:
            raise RuntimeError("NetworkManager not initialized. Call initialize_network() first.")
        return self._network_manager
    
    @property
    def screen_manager(self) -> 'ScreenManager':
        if self._screen_manager is None:
            raise RuntimeError("ScreenManager not initialized. Call initialize_screen_manager() first.")
        return self._screen_manager

    @property
    def identity_manager(self) -> 'IdentityManager':
        if self._identity_manager is None:
            raise RuntimeError("IdentityManager not initialized. Call initialize_identity_manager() first.")
        return self._identity_manager

    @property
    def data_synchronizer(self) -> 'DataSynchronizer':
        if self._data_synchronizer is None:
            raise RuntimeError("DataSynchronizer not initialized. Call initialize_synchronizer() first.")
        return self._data_synchronizer

    @property
    def leaderboard_manager(self) -> 'LeaderboardManager':
        if self._leaderboard_manager is None:
            raise RuntimeError("LeaderboardManager not initialized. Call initialize_leaderboard_manager() first.")
        return self._leaderboard_manager

    @property
    def settings_manager(self) -> 'SettingsManager':
        if self._settings_manager is None:
            raise RuntimeError("SettingsManager not initialized. Call initialize_settings_manager() first.")
        return self._settings_manager

    def set_identity_entry_context(
        self,
        reason: str,
        return_screen: Optional[str] = None,
        rename_required: bool = True,
    ) -> None:
        with self._identity_context_lock:
            self._identity_entry_reason = reason
            self._identity_return_screen = return_screen or SETTINGS.SCREEN_NAMES.MENU
            self._identity_rename_required = rename_required

    def mark_identity_rename_required(self, reason: str) -> None:
        with self._identity_context_lock:
            self._identity_entry_reason = reason
            self._identity_rename_required = True

    def clear_identity_rename_required(self) -> None:
        with self._identity_context_lock:
            self._identity_rename_required = False
            self._identity_entry_reason = "missing"
            self._identity_return_screen = SETTINGS.SCREEN_NAMES.MENU

    @property
    def identity_entry_reason(self) -> str:
        with self._identity_context_lock:
            return self._identity_entry_reason

    @property
    def identity_rename_required(self) -> bool:
        with self._identity_context_lock:
            return self._identity_rename_required

    def consume_identity_return_screen(self) -> str:
        with self._identity_context_lock:
            return_screen = self._identity_return_screen
            self._identity_return_screen = SETTINGS.SCREEN_NAMES.MENU
            self._identity_rename_required = False
            self._identity_entry_reason = "missing"
            return return_screen
import threading
from typing import TYPE_CHECKING, Optional

import pygame

from settings import SETTINGS

if TYPE_CHECKING:
    from security.identity_manager import IdentityManager
    from network.connection_manager import NetworkManager
    from ui.assets import AssetManager
    from ui.audio import AudioManager
    from ui.screen_manager import ScreenManager


class ServiceContainer:
    def __init__(self):
        self._asset_manager: Optional['AssetManager'] = None
        self._audio_manager: Optional['AudioManager'] = None
        self._network_manager: Optional['NetworkManager'] = None
        self._screen_manager: Optional['ScreenManager'] = None
        self._identity_manager: Optional['IdentityManager'] = None
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
    
    def initialize_network(self) -> 'NetworkManager':
        if self._network_manager is None:
            from network.connection_manager import NetworkManager
            self._network_manager = NetworkManager()
        return self._network_manager

    def initialize_identity_manager(self) -> 'IdentityManager':
        if self._identity_manager is None:
            from security.identity_manager import IdentityManager

            network_manager = self.initialize_network()
            self._identity_manager = IdentityManager(network_manager=network_manager)
        return self._identity_manager
    
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

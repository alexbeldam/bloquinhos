from typing import Optional

import pygame

from engine import GameController
from ui.assets.asset_manager import AssetManager
from utils.logger import log


class AudioManager:
    # Volume normalization targets (relative to mix level)
    # Adjust these based on your audio mastering
    BGM_VOLUME = 0.7      # Background music level
    SFX_VOLUME = 0.8      # Sound effects level (slightly louder for clarity)
    
    # SFX fallback map: maps requested SFX to alternative if primary doesn't exist
    SFX_FALLBACK = {
        "nav": None,           # No fallback - silent if missing
        "select": "position",  # Use position SFX if select doesn't exist
        "cancel": "position",  # Use position SFX if cancel doesn't exist
        "open": None,          # No fallback - silent if missing
    }

    def __init__(self, asset_loader: AssetManager) -> None:
        self.asset_loader = asset_loader
        self.master_volume: float = 1.0
        self.bgm_volume: float = self.BGM_VOLUME
        self.sfx_volume: float = self.SFX_VOLUME

        self.master_muted: bool = False
        self.bgm_muted: bool = False
        self.sfx_muted: bool = False

        self.current_bgm: Optional[str] = None
        self._sfx_cache: dict[str, Optional[pygame.mixer.Sound]] = {}

    def initialize_mixer(self) -> None:
        if pygame.mixer.get_init():
            pygame.mixer.quit()
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=2048)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(32)
        log.debug("Audio mixer initialized")

    def play_bgm(self, name: str, loop: bool = True) -> None:
        if self.bgm_muted:
            return

        if self.current_bgm == name and pygame.mixer.music.get_busy():
            return

        try:
            filepath = self.asset_loader.get_music(name)
            pygame.mixer.music.load(filepath)
            loops = -1 if loop else 0
            pygame.mixer.music.play(loops=loops)
            self._update_bgm_volume()
            self.current_bgm = name
        except (KeyError, FileNotFoundError, pygame.error):
            pass

    def stop_bgm(self) -> None:
        pygame.mixer.music.stop()
        self.current_bgm = None

    def play_sfx(self, name: str) -> None:
        if self.master_muted or self.sfx_muted:
            return

        # Check cache first
        if name in self._sfx_cache:
            sound = self._sfx_cache[name]
            if sound is None:
                return  # Already tried and failed
            self._play_cached_sfx(sound)
            return

        try:
            sound = self.asset_loader.get_sfx(name)
            self._sfx_cache[name] = sound
            self._play_cached_sfx(sound)
        except (KeyError, FileNotFoundError, pygame.error):
            log.debug(f"SFX '{name}' not found, attempting fallback...")
            self._sfx_cache[name] = None
            self._try_fallback_sfx(name)

    def _play_cached_sfx(self, sound: pygame.mixer.Sound) -> None:
        vol = self.master_volume * self.sfx_volume
        if sound.get_volume() != vol:
            sound.set_volume(vol)
        sound.play()

    def _try_fallback_sfx(self, name: str) -> None:
        """Try playing a fallback SFX if primary doesn't exist."""
        fallback_name = self.SFX_FALLBACK.get(name)
        if fallback_name is None:
            return
        
        try:
            sound = self.asset_loader.get_sfx(fallback_name)
            self._play_cached_sfx(sound)
        except (KeyError, FileNotFoundError, pygame.error):
            log.debug(f"Fallback SFX '{fallback_name}' also not found for '{name}'")

    def set_master_volume(self, volume: float) -> None:
        self.master_volume = max(0.0, min(1.0, volume))
        self._update_bgm_volume()

    def set_bgm_volume(self, volume: float) -> None:
        self.bgm_volume = max(0.0, min(1.0, volume))
        self._update_bgm_volume()

    def set_sfx_volume(self, volume: float) -> None:
        self.sfx_volume = max(0.0, min(1.0, volume))

    def set_normalized_volumes(self, bgm_level: float = 0.7, sfx_level: float = 0.8) -> None:
        """
        Set normalized volume levels for BGM and SFX.
        Recommended: BGM ~0.7, SFX ~0.8 (to ensure UI feedback is audible)
        Both should be between 0.0 and 1.0.
        """
        self.bgm_volume = max(0.0, min(1.0, bgm_level))
        self.sfx_volume = max(0.0, min(1.0, sfx_level))
        self._update_bgm_volume()

    def _update_bgm_volume(self) -> None:
        if pygame.mixer.get_init():
            if self.master_muted or self.bgm_muted:
                pygame.mixer.music.set_volume(0.0)
            else:
                pygame.mixer.music.set_volume(self.master_volume * self.bgm_volume)

    def set_master_muted(self, muted: bool) -> None:
        self.master_muted = muted
        self._update_bgm_volume()

    def set_bgm_muted(self, muted: bool) -> None:
        self.bgm_muted = muted
        if pygame.mixer.get_init():
            if muted and pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
            elif not muted and self.current_bgm:
                pygame.mixer.music.unpause()
        self._update_bgm_volume()

    def set_sfx_muted(self, muted: bool) -> None:
        self.sfx_muted = muted

    def register_events(self, controller: GameController) -> None:
        def handle_piece_locked(piece) -> None:
            if not getattr(controller, "is_game_over", False):
                self.play_sfx("blockfall")

        controller.on_piece_locked(handle_piece_locked)
        
        def handle_line_clear(lines: int) -> None:
            self.play_sfx("rc_complete")
                
        controller.on_line_clear(handle_line_clear)
        
        def handle_game_over() -> None:
            pygame.mixer.stop()  
            self.stop_bgm()
            self.play_sfx("gameover")
            
        controller.on_game_over(handle_game_over)

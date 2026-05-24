from typing import Optional

import pygame

from engine import GameController
from ui.assets.asset_manager import AssetManager
from utils.logger import log


class AudioManager:
    def __init__(self, asset_loader: AssetManager) -> None:
        self.asset_loader = asset_loader
        self.master_volume: float = 1.0
        self.bgm_volume: float = 1.0
        self.sfx_volume: float = 1.0

        self.bgm_enabled: bool = True
        self.sfx_enabled: bool = True

        self.current_bgm: Optional[str] = None

    def initialize_mixer(self) -> None:
        if pygame.mixer.get_init():
            pygame.mixer.quit()
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=2048)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(32)
        log.debug("Audio mixer initialized")

    def play_bgm(self, name: str, loop: bool = True) -> None:
        if not self.bgm_enabled:
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
        if not self.sfx_enabled:
            return

        try:
            sound = self.asset_loader.get_sfx(name)
            vol = self.master_volume * self.sfx_volume
            if sound.get_volume() != vol:
                sound.set_volume(vol)
            sound.play()
        except (KeyError, FileNotFoundError, pygame.error):
            pass

    def set_master_volume(self, volume: float) -> None:
        self.master_volume = max(0.0, min(1.0, volume))
        self._update_bgm_volume()

    def set_bgm_volume(self, volume: float) -> None:
        self.bgm_volume = max(0.0, min(1.0, volume))
        self._update_bgm_volume()

    def set_sfx_volume(self, volume: float) -> None:
        self.sfx_volume = max(0.0, min(1.0, volume))

    def _update_bgm_volume(self) -> None:
        pygame.mixer.music.set_volume(self.master_volume * self.bgm_volume)

    def toggle_bgm(self) -> bool:
        self.bgm_enabled = not self.bgm_enabled
        if not self.bgm_enabled:
            pygame.mixer.music.pause()
        else:
            if self.current_bgm:
                pygame.mixer.music.unpause()
        return self.bgm_enabled

    def toggle_sfx(self) -> bool:
        self.sfx_enabled = not self.sfx_enabled
        return self.sfx_enabled

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

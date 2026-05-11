import os
from typing import Dict, List, Tuple, Union
import pygame
from ui.assets.loaders.base_loader import BaseLoader
from ui.assets.progress_tracker import ProgressTracker
from utils.logger import log

class AudioLoader(BaseLoader):
    def __init__(self, directory: str):
        super().__init__(directory, "🔊", "audio")
        self._sfx: Dict[str, pygame.mixer.Sound] = {}
        self._music: Dict[str, str] = {}
    
    def load_audio(
        self, 
        wav_files: List[str], 
        ogg_files: List[str], 
        progress_tracker: ProgressTracker
    ) -> Tuple[int, int]:
        log.info(f"{self._emoji} Loading {self._category}...")
        
        sfx_count = self._load_sfx(wav_files, progress_tracker)
        music_count = self._load_music(ogg_files, progress_tracker)
        
        log.info(f"✅ Loaded {sfx_count} SFX and {music_count} music tracks.")
        return sfx_count, music_count
    
    def _load_sfx(self, wav_files: List[str], progress_tracker: ProgressTracker) -> int:
        count = 0
        for wav_file in wav_files:
            log.debug(f"🎵 Loading {wav_file}...")
            try:
                wav_path = os.path.join(self._directory, wav_file)
                sound = pygame.mixer.Sound(wav_path)
                name = wav_file.rsplit('.', 1)[0]
                self._sfx[name] = sound
                count += 1
            except Exception as e:
                log.error(f"❌ Failed to load SFX {wav_file}: {e}")
            
            progress_tracker.update(f"Loading {wav_file}")
        return count
    
    def _load_music(self, ogg_files: List[str], progress_tracker: ProgressTracker) -> int:
        count = 0
        for ogg_file in ogg_files:
            log.debug(f"🎶 Loading {ogg_file}...")
            try:
                ogg_path = os.path.join(self._directory, ogg_file)
                name = ogg_file.rsplit('.', 1)[0]
                self._music[name] = ogg_path
                count += 1
            except Exception as e:
                log.error(f"❌ Failed to load music {ogg_file}: {e}")
            
            progress_tracker.update(f"Loading {ogg_file}")
        return count
    
    def _load_single(self, item: Union[str, Tuple[str, str]]) -> bool:
        raise NotImplementedError("Use load_audio instead")
    
    def _format_item(self, item: Union[str, Tuple[str, str]]) -> str:
        raise NotImplementedError("Use load_audio instead")
    
    def get_sfx(self, filename: str) -> pygame.mixer.Sound:
        if filename not in self._sfx:
            raise KeyError(f"SFX '{filename}' not found in loaded assets")
        return self._sfx[filename]
    
    def get_music(self, filename: str) -> str:
        if filename not in self._music:
            raise KeyError(f"Music '{filename}' not found in loaded assets")
        return self._music[filename]

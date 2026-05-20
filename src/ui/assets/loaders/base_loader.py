from abc import ABC, abstractmethod
from typing import List, Any
from utils.logger import log
from ui.assets.progress_tracker import ProgressTracker

class BaseLoader(ABC):
    def __init__(self, directory: str, category: str):
        self._directory = directory
        self._category = category
    
    def load(self, items: List[Any], progress_tracker: ProgressTracker) -> int:
        log.info(f"Loading {self._category}...")
        count = 0
        
        for item in items:
            log.debug(f"Loading {self._format_item(item)}...")
            try:
                if self._load_single(item):
                    count += 1
            except Exception as e:
                log.error(f"Failed to load {self._format_item(item)}: {e}")
            
            progress_tracker.update(f"Loading {self._format_item(item)}")
        
        log.info(f"Loaded {count} {self._category}.")
        return count
    
    @abstractmethod
    def _load_single(self, item: Any) -> bool:
        pass
    
    @abstractmethod
    def _format_item(self, item: Any) -> str:
        pass

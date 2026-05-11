from typing import Optional, Callable, Dict

class ProgressTracker:
    def __init__(self, total: int, callback: Optional[Callable[[str, int, int], None]] = None):
        self._current: int = 0
        self._total: int = total
        self._callback: Optional[Callable[[str, int, int], None]] = callback
    
    def update(self, message: str) -> None:
        self._current += 1
        if self._callback:
            self._callback(message, self._current, self._total)
    
    @property
    def current(self) -> int:
        return self._current
    
    @property
    def total(self) -> int:
        return self._total
    
    def to_dict(self) -> Dict[str, int]:
        return {
            'current': self._current,
            'total': self._total
        }

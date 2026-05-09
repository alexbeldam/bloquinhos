from enum import IntEnum

class Tile(IntEnum):
    EMPTY = 0
    CYAN = 1
    BLUE = 2
    ORANGE = 3
    YELLOW = 4
    GREEN = 5
    PURPLE = 6
    RED = 7
    GHOST = 8
    
    @classmethod
    def from_piece(cls, piece: 'Tetromino') -> 'Tile':
        return cls(piece.value)

class Tetromino(IntEnum):
    I = 1
    J = 2
    L = 3
    O = 4
    S = 5
    T = 6
    Z = 7
    
    @property
    def tile(self) -> Tile:
        return Tile(self.value)

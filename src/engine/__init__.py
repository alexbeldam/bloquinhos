"""
Game engine module.

This module contains the core game logic including tile states,
tetromino mechanics, collision detection, and grid management.
"""

from .tile import Tile, Tetromino
from .shapes import get_shape, get_all_rotations, materialize_shape, get_occupied_cells

__all__ = ['Tile', 'Tetromino', 'get_shape', 'get_all_rotations', 'materialize_shape', 'get_occupied_cells']

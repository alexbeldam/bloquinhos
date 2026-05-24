import pygame

from engine.shapes import get_shape_coordinates
from engine.tile import Tetromino
from settings import SETTINGS


class MorphingEngine:
    def __init__(
        self,
        total_loop_time: float = SETTINGS.LOADING_ANIMATION.ANIMATION_CYCLE_TIME,
    ):
        self.tetromino_order = [
            Tetromino.T,
            Tetromino.S,
            Tetromino.Z,
            Tetromino.O,
            Tetromino.I,
            Tetromino.J,
            Tetromino.L,
        ]

        self.colors = [
            SETTINGS.TILE_COLORS.get_tile_info(tetromino.tile).color
            for tetromino in self.tetromino_order
        ]

        self.current_idx = 0
        self.next_idx = 1

        initial_coords = get_shape_coordinates(self.tetromino_order[0])
        self.active_pos = [[float(x), float(y)] for x, y in initial_coords]
        self.current_color = list(self.colors[0])

        self.anim_timer = 0.0
        num_shapes = len(self.tetromino_order)
        self.anim_interval = (total_loop_time * 1000) / num_shapes

        base_speed = 0.15
        reference_interval = 800
        speed_multiplier = reference_interval / self.anim_interval
        unclamped_speed = base_speed * speed_multiplier
        self.morph_speed = max(0.1, min(0.6, unclamped_speed))

    def update(self, dt: float) -> None:
        dt_ms = dt * 1000

        target_coords = get_shape_coordinates(self.tetromino_order[self.next_idx])
        target_color = self.colors[self.next_idx]

        # Smoothly interpolate block positions toward target shape
        num_blocks = 4
        coord_dimensions = 2  # x and y
        for block_idx in range(num_blocks):
            for coord_idx in range(coord_dimensions):
                current_value = self.active_pos[block_idx][coord_idx]
                target_value = target_coords[block_idx][coord_idx]
                delta = target_value - current_value
                self.active_pos[block_idx][coord_idx] += delta * self.morph_speed

        # Smoothly interpolate RGB color values
        rgb_channels = 3
        for channel_idx in range(rgb_channels):
            current_channel = self.current_color[channel_idx]
            target_channel = target_color[channel_idx]
            delta = target_channel - current_channel
            self.current_color[channel_idx] += delta * self.morph_speed

        # Cycle to next shape when timer expires
        self.anim_timer += dt_ms
        if self.anim_timer >= self.anim_interval:
            self.anim_timer = 0.0
            self.current_idx = self.next_idx
            num_shapes = len(self.tetromino_order)
            self.next_idx = (self.next_idx + 1) % num_shapes

    def draw(self, surface: pygame.Surface, center_x: int, center_y: int, scale: int) -> None:
        # Calculate center of mass for all blocks
        num_blocks = 4
        total_x = sum(pos[0] for pos in self.active_pos)
        total_y = sum(pos[1] for pos in self.active_pos)
        avg_x = total_x / num_blocks
        avg_y = total_y / num_blocks

        draw_color = tuple(map(int, self.current_color))

        # Draw each block relative to center of mass
        for x, y in self.active_pos:
            rel_x = (x - avg_x) * scale
            rel_y = (y - avg_y) * scale

            # Convert to screen coordinates
            half_block = scale / 2
            draw_x = round(center_x + rel_x - half_block)
            draw_y = round(center_y + rel_y - half_block)

            block_rect = pygame.Rect(draw_x, draw_y, scale, scale)

            pygame.draw.rect(surface, draw_color, block_rect)

            # Draw highlight lines (top and left)
            top_left = (draw_x, draw_y)
            top_right = (draw_x + scale - 1, draw_y)
            bottom_left = (draw_x, draw_y + scale - 1)
            pygame.draw.line(surface, SETTINGS.UI_THEME.WHITE, top_left, top_right, 1)
            pygame.draw.line(surface, SETTINGS.UI_THEME.WHITE, top_left, bottom_left, 1)

            # Draw border
            border_width = SETTINGS.LOADING_LAYOUT.BORDER_WIDTH
            pygame.draw.rect(surface, SETTINGS.UI_THEME.GRAY_DARK, block_rect, border_width)

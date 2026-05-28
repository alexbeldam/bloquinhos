from typing import Optional

import pygame

from settings import SETTINGS
from ui.styles import SETTINGS_STYLE
from ui.tabs.settings_tab import SettingsTab


class AudioTab(SettingsTab):
    CONTENT_PADDING = 30
    SLIDER_ROW_HEIGHT = 50
    SLIDER_ROW_GAP = 20
    SLIDER_HEIGHT = 6
    HANDLE_RADIUS = 8
    SLIDER_HITBOX_HEIGHT = HANDLE_RADIUS * 2 + 4  # 20px (handle diameter + 4px margin)
    ICON_SIZE = 28
    ICON_SPACING = 16

    SLIDERS = [
        ("Master Volume", "audio.master.volume", "audio.master.muted"),
        ("Music Volume", "audio.music.volume", "audio.music.muted"),
        ("SFX Volume", "audio.sfx.volume", "audio.sfx.muted"),
    ]

    def __init__(self) -> None:
        super().__init__(
            id="audio",
            title="Audio",
            icon_name="headphones",
            order=0,
            category="audio",
        )
        self._slider_hitboxes: list[tuple[str, pygame.Rect]] = []
        self._icon_hitboxes: list[tuple[str, pygame.Rect]] = []
        self._dragging_path: Optional[str] = None
        self.hovered_slider_path: Optional[str] = None
        self.hovered_icon_path: Optional[str] = None

    def render(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
    ) -> None:
        self._slider_hitboxes = []
        self._icon_hitboxes = []

        title_y, _, _ = self._draw_tab_background_and_title(
            surface,
            rect,
            self.title,
            self.CONTENT_PADDING,
        )

        sliders_start_y = title_y + 60
        row_font = self._font(SETTINGS.UI_TYPOGRAPHY.BODY)

        for index, (label, volume_path, mute_path) in enumerate(self.SLIDERS):
            row_y = sliders_start_y + index * (self.SLIDER_ROW_HEIGHT + self.SLIDER_ROW_GAP)
            
            volume = 1.0
            is_muted = False
            if self.settings_manager is not None:
                try:
                    volume = self.settings_manager.get_float(volume_path)
                except (KeyError, TypeError, ValueError):
                    volume = 1.0
                try:
                    is_muted = self.settings_manager.get_bool(mute_path)
                except (KeyError, TypeError, ValueError):
                    is_muted = False

            label_surface = self._render_text_surface(
                label,
                SETTINGS.UI_TYPOGRAPHY.BODY,
                SETTINGS.UI_THEME.TEXT_PRIMARY,
            )
            label_x = rect.x + self.CONTENT_PADDING
            label_y = row_y
            surface.blit(label_surface, (label_x, label_y))

            icon_x_relative = rect.width - self.CONTENT_PADDING - self.ICON_SIZE
            icon_y_relative = row_y - rect.y + (label_surface.get_height() - self.ICON_SIZE) // 2
            icon_rect = pygame.Rect(icon_x_relative, icon_y_relative, self.ICON_SIZE, self.ICON_SIZE)
            self._icon_hitboxes.append((mute_path, icon_rect))

            slider_x_relative = self.CONTENT_PADDING
            slider_y_relative = row_y - rect.y + label_surface.get_height() + 8
            slider_width = rect.width - self.CONTENT_PADDING * 2 - self.ICON_SIZE - self.ICON_SPACING
            slider_hitbox_y = slider_y_relative - (self.SLIDER_HITBOX_HEIGHT - self.SLIDER_HEIGHT) // 2
            slider_rect = pygame.Rect(slider_x_relative, slider_hitbox_y, slider_width, self.SLIDER_HITBOX_HEIGHT)
            self._slider_hitboxes.append((volume_path, slider_rect))

            slider_x_screen = rect.x + slider_x_relative
            slider_y_screen = rect.y + slider_y_relative
            icon_x_screen = rect.x + icon_x_relative
            icon_y_screen = rect.y + icon_y_relative

            bg_color = SETTINGS_STYLE.SLIDER_BG
            progress_color = SETTINGS_STYLE.SLIDER_MUTED if is_muted else SETTINGS.UI_THEME.PURPLE
            
            pygame.draw.rect(surface, bg_color, (slider_x_screen, slider_y_screen, slider_width, self.SLIDER_HEIGHT), border_radius=3)
            
            if volume > 0:
                progress_width = int(slider_width * volume)
                pygame.draw.rect(surface, progress_color, (slider_x_screen, slider_y_screen, progress_width, self.SLIDER_HEIGHT), border_radius=3)

            handle_x = slider_x_screen + int(slider_width * volume)
            handle_y = slider_y_screen + self.SLIDER_HEIGHT // 2
            pygame.draw.circle(
                surface,
                progress_color,
                (handle_x, handle_y),
                self.HANDLE_RADIUS
            )

            icon_name = self._get_volume_icon_name(volume, is_muted)
            icon = self._try_load_icon(icon_name)
            if icon:
                icon_scaled = pygame.transform.scale(icon, (self.ICON_SIZE, self.ICON_SIZE))
                is_icon_hovered = mute_path == self.hovered_icon_path
                if is_icon_hovered:
                    icon_scaled.set_alpha(200)
                surface.blit(icon_scaled, (icon_x_screen, icon_y_screen))
        
        reset_button_y = self._bottom_action_y(rect, self.CONTENT_PADDING, action_height=42)
        self.render_reset_button(surface, rect, reset_button_y)

    def handle_click(
        self,
        pos: tuple[int, int],
    ) -> None:
        if self.settings_manager is None:
            return

        for mute_path, icon_rect in self._icon_hitboxes:
            if icon_rect.collidepoint(pos):
                try:
                    current_mute = self.settings_manager.get_bool(mute_path)
                    self.settings_manager.set(mute_path, not current_mute)
                except (KeyError, TypeError, ValueError):
                    pass
                return

        for volume_path, slider_rect in self._slider_hitboxes:
            if slider_rect.collidepoint(pos):
                self._dragging_path = volume_path
                self._update_slider_value(pos, slider_rect, volume_path)
                return

    def handle_mouse_motion(self, pos: tuple[int, int]) -> None:
        self.hovered_slider_path = None
        self.hovered_icon_path = None
        
        for volume_path, slider_rect in self._slider_hitboxes:
            if slider_rect.collidepoint(pos):
                self.hovered_slider_path = volume_path
                break
        
        for mute_path, icon_rect in self._icon_hitboxes:
            if icon_rect.collidepoint(pos):
                self.hovered_icon_path = mute_path
                break

    def handle_mouse_button_down(self, pos: tuple[int, int]) -> None:
        self.handle_click(pos)

    def handle_mouse_button_up(self) -> None:
        self._dragging_path = None

    def handle_drag(self, pos: tuple[int, int]) -> None:
        if self._dragging_path is None or self.settings_manager is None:
            return

        for volume_path, slider_rect in self._slider_hitboxes:
            if volume_path == self._dragging_path:
                self._update_slider_value(pos, slider_rect, volume_path)
                return

    def _update_slider_value(
        self,
        pos: tuple[int, int],
        slider_rect: pygame.Rect,
        volume_path: str,
    ) -> None:
        if self.settings_manager is None:
            return

        relative_x = pos[0] - slider_rect.x
        volume = max(0.0, min(1.0, relative_x / slider_rect.width))
        try:
            self.settings_manager.set(volume_path, volume)
        except (KeyError, TypeError, ValueError):
            pass

    def _get_volume_icon_name(self, volume: float, is_muted: bool) -> str:
        if is_muted:
            return "mute"
        if volume == 0:
            return "volume-off"
        elif volume <= 0.33:
            return "volume-low"
        elif volume <= 0.66:
            return "volume-medium"
        else:
            return "volume-high"

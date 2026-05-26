from typing import Optional, TYPE_CHECKING

import pygame

from settings import SETTINGS
from ui.components import (
    bottom_action_y,
    draw_option_row,
    draw_row_value_right,
    draw_tab_background_and_title,
    draw_wrapped_text,
)
from ui.tabs.settings_tab import SettingsTab

if TYPE_CHECKING:
    from ui.assets import AssetManager
    from utils.settings_manager import SettingsManager


class ControlsTab(SettingsTab):
    CONTENT_PADDING = 30
    OPTION_ROW_HEIGHT = 44
    OPTION_ROW_GAP = 8
    FOOTER_RESERVED_SPACE = 50

    OPTIONS = [
        ("Move Left", "controls.left"),
        ("Move Right", "controls.right"),
        ("Soft Drop", "controls.soft_drop"),
        ("Hard Drop", "controls.hard_drop"),
        ("Rotate", "controls.rotate"),
        ("Hold", "controls.hold"),
        ("Pause", "controls.pause"),
    ]

    def __init__(self) -> None:
        super().__init__(
            id="controls",
            title="Controls",
            icon_name="gamepad",
            order=10,
            category="controls",
        )
        self._option_hitboxes: list[tuple[str, pygame.Rect]] = []
        self.hovered_option_path: Optional[str] = None
        self._pending_keybind_path: Optional[str] = None
        self._status_message: Optional[str] = None
        self._status_is_error: bool = False

    def render(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        assets: Optional["AssetManager"],
        settings_manager: Optional["SettingsManager"],
    ) -> None:
        self._option_hitboxes = []

        _, content_center_x, options_start_y = draw_tab_background_and_title(
            surface,
            rect,
            self.title,
            assets,
            self.CONTENT_PADDING,
        )
        row_x = rect.x + self.CONTENT_PADDING
        row_width = rect.width - self.CONTENT_PADDING * 2
        row_font = self._font(SETTINGS.UI_TYPOGRAPHY.MEDIUM, assets)

        for index, (label, path) in enumerate(self.OPTIONS):
            row_y = options_start_y + index * (self.OPTION_ROW_HEIGHT + self.OPTION_ROW_GAP)
            row_rect = pygame.Rect(row_x, row_y, row_width, self.OPTION_ROW_HEIGHT)
            self._option_hitboxes.append((path, row_rect))

            is_hovered = path == self.hovered_option_path
            draw_option_row(surface, row_rect, label, row_font, is_hovered=is_hovered)

            binding_text = "Unbound"
            if self._pending_keybind_path == path:
                binding_text = "Press key..."
            elif settings_manager is not None:
                try:
                    key_code = settings_manager.get(path)
                    if isinstance(key_code, int):
                        key_name = pygame.key.name(key_code)
                        binding_text = key_name.upper() if key_name else str(key_code)
                except (KeyError, TypeError, ValueError):
                    pass

            draw_row_value_right(
                surface,
                row_rect,
                binding_text,
                row_font,
                SETTINGS.UI_THEME.CYAN if self._pending_keybind_path == path else SETTINGS.UI_THEME.TEXT_PRIMARY,
            )

        help_text = "Click an action to rebind, then press any key. Right-click to cancel."
        help_y = rect.y + rect.height - self.CONTENT_PADDING - 8
        draw_wrapped_text(
            surface,
            help_text,
            SETTINGS.UI_TYPOGRAPHY.SMALL,
            SETTINGS.UI_THEME.TEXT_MUTED,
            row_width,
            line_spacing=2,
            assets=assets,
            x=content_center_x,
            y=help_y,
            align="center",
        )

        if self._status_message:
            status_color = SETTINGS.UI_THEME.RED if self._status_is_error else SETTINGS.UI_THEME.GREEN
            status_y = help_y - 40
            draw_wrapped_text(
                surface,
                self._status_message,
                SETTINGS.UI_TYPOGRAPHY.SMALL,
                status_color,
                row_width,
                line_spacing=2,
                assets=assets,
                x=content_center_x,
                y=status_y,
                align="center",
            )
        
        reset_button_y = bottom_action_y(
            rect,
            self.CONTENT_PADDING,
            action_height=42,
            reserve_space=self.FOOTER_RESERVED_SPACE,
        )
        self.render_reset_button(surface, rect, assets, reset_button_y)

    def handle_click(
        self,
        pos: tuple[int, int],
        settings_manager: Optional["SettingsManager"],
    ) -> None:
        for path, rect in self._option_hitboxes:
            if rect.collidepoint(pos):
                self._pending_keybind_path = path
                self._status_message = "Press any key to rebind. Right-click to cancel."
                self._status_is_error = False
                return

    def handle_key(
        self,
        event: pygame.event.Event,
        settings_manager: Optional["SettingsManager"],
    ) -> None:
        if self._pending_keybind_path is None:
            return

        if event.type != pygame.KEYDOWN:
            return

        if settings_manager is None:
            self._pending_keybind_path = None
            return

        try:
            conflict = self._find_binding_conflict(self._pending_keybind_path, int(event.key), settings_manager)
            if conflict is not None:
                self._status_message = f"Key already bound to {conflict}. Pick another key."
                self._status_is_error = True
                self._pending_keybind_path = None
                return

            settings_manager.set(self._pending_keybind_path, int(event.key))
            self._status_message = "Key binding updated."
            self._status_is_error = False
        except (KeyError, TypeError, ValueError):
            self._status_message = "Could not update key binding."
            self._status_is_error = True

        self._pending_keybind_path = None

    def handle_mouse_motion(self, pos: tuple[int, int]) -> None:
        self.hovered_option_path = None
        for path, rect in self._option_hitboxes:
            if rect.collidepoint(pos):
                self.hovered_option_path = path
                return

    def has_pending_keybind(self) -> bool:
        return self._pending_keybind_path is not None

    def cancel_keybind_capture(self) -> None:
        if self._pending_keybind_path is not None:
            self._pending_keybind_path = None
            self._status_message = "Key binding change canceled."
            self._status_is_error = False

    def clear_status(self) -> None:
        self._pending_keybind_path = None
        self._status_message = None
        self._status_is_error = False

    def _find_binding_conflict(
        self,
        target_path: str,
        new_key: int,
        settings_manager: "SettingsManager",
    ) -> Optional[str]:
        try:
            controls = settings_manager.get("controls")
        except (KeyError, TypeError, ValueError):
            return None

        if not isinstance(controls, dict):
            return None

        target_action = target_path.split(".")[-1]
        for action, key_code in controls.items():
            if action == target_action:
                continue
            if isinstance(key_code, int) and key_code == new_key:
                return action.replace("_", " ").title()
        return None

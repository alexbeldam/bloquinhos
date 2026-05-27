from typing import Optional, TYPE_CHECKING

import pygame

from settings import SETTINGS
from ui.tabs.settings_tab import SettingsTab

if TYPE_CHECKING:
    from utils.settings_manager import SettingsManager


class ControlsTab(SettingsTab):
    CONTENT_PADDING = 24
    OPTION_ROW_HEIGHT = 40
    OPTION_ROW_GAP = 6
    FOOTER_HELP_BOTTOM_GAP = 4
    FOOTER_HELP_TO_BUTTON_GAP = 8
    FOOTER_STATUS_TO_HELP_GAP = 6

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
    ) -> None:
        self._option_hitboxes = []

        _, content_center_x, options_start_y = self._draw_tab_background_and_title(
            surface,
            rect,
            self.title,
            self.CONTENT_PADDING,
        )
        row_x = rect.x + self.CONTENT_PADDING
        row_width = rect.width - self.CONTENT_PADDING * 2
        row_font = self._font(SETTINGS.UI_TYPOGRAPHY.BODY)

        for index, (label, path) in enumerate(self.OPTIONS):
            row_y = options_start_y + index * (self.OPTION_ROW_HEIGHT + self.OPTION_ROW_GAP)
            row_rect = pygame.Rect(row_x, row_y, row_width, self.OPTION_ROW_HEIGHT)
            self._option_hitboxes.append((path, row_rect))

            is_hovered = path == self.hovered_option_path
            self._draw_option_row(
                surface,
                row_rect,
                label,
                row_font,
                text_size=SETTINGS.UI_TYPOGRAPHY.BODY,
                is_hovered=is_hovered,
            )

            binding_text = "Unbound"
            if self._pending_keybind_path == path:
                binding_text = "Press key..."
            elif self.settings_manager is not None:
                try:
                    key_code = self.settings_manager.get(path)
                    if isinstance(key_code, int):
                        key_name = pygame.key.name(key_code)
                        binding_text = key_name.upper() if key_name else str(key_code)
                except (KeyError, TypeError, ValueError):
                    pass

            self._draw_row_value_right(
                surface,
                row_rect,
                binding_text,
                row_font,
                SETTINGS.UI_THEME.CYAN if self._pending_keybind_path == path else SETTINGS.UI_THEME.TEXT_PRIMARY,
                text_size=SETTINGS.UI_TYPOGRAPHY.BODY,
            )

        help_text = "Click an action to rebind, then press any key. Right-click to cancel."
        help_height = self._wrapped_text_height(
            help_text,
            SETTINGS.UI_TYPOGRAPHY.SMALL,
            row_width,
            line_spacing=2,
        )
        status_height = 0
        if self._status_message:
            status_height = self._wrapped_text_height(
                self._status_message,
                SETTINGS.UI_TYPOGRAPHY.SMALL,
                row_width,
                line_spacing=2,
            )

        footer_text_height = help_height
        if status_height > 0:
            footer_text_height += self.FOOTER_STATUS_TO_HELP_GAP + status_height

        reset_button_y = self._bottom_action_y(
            rect,
            self.CONTENT_PADDING,
            action_height=42,
            reserve_space=footer_text_height + self.FOOTER_HELP_TO_BUTTON_GAP + self.FOOTER_HELP_BOTTOM_GAP,
        )

        help_bottom = rect.y + rect.height - self.CONTENT_PADDING - self.FOOTER_HELP_BOTTOM_GAP
        help_top = help_bottom - help_height
        help_center_y = help_top + help_height // 2

        self._draw_wrapped_text(
            surface,
            help_text,
            SETTINGS.UI_TYPOGRAPHY.SMALL,
            SETTINGS.UI_THEME.TEXT_MUTED,
            row_width,
            line_spacing=2,
            x=content_center_x,
            y=help_center_y,
            align="center",
        )

        if self._status_message:
            status_top = help_top - self.FOOTER_STATUS_TO_HELP_GAP - status_height
            status_center_y = status_top + status_height // 2
            status_color = SETTINGS.UI_THEME.RED if self._status_is_error else SETTINGS.UI_THEME.GREEN

            self._draw_wrapped_text(
                surface,
                self._status_message,
                SETTINGS.UI_TYPOGRAPHY.SMALL,
                status_color,
                row_width,
                line_spacing=2,
                x=content_center_x,
                y=status_center_y,
                align="center",
            )

        self.render_reset_button(surface, rect, reset_button_y)

    def handle_click(
        self,
        pos: tuple[int, int],
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
    ) -> None:
        if self._pending_keybind_path is None:
            return

        if event.type != pygame.KEYDOWN:
            return

        if self.settings_manager is None:
            self._pending_keybind_path = None
            return

        try:
            conflict = self._find_binding_conflict(self._pending_keybind_path, int(event.key), self.settings_manager)
            if conflict is not None:
                self._status_message = f"Key already bound to {conflict}. Pick another key."
                self._status_is_error = True
                self._pending_keybind_path = None
                return

            self.settings_manager.set(self._pending_keybind_path, int(event.key))
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

    def _wrapped_text_height(
        self,
        text: str,
        font_size: int,
        max_width: int,
        *,
        line_spacing: int,
    ) -> int:
        font = self._font(font_size)
        words = text.split()
        if not words:
            return 0

        lines = 1
        current_line = words[0]
        for word in words[1:]:
            candidate = f"{current_line} {word}"
            if font.size(candidate)[0] <= max_width:
                current_line = candidate
            else:
                lines += 1
                current_line = word

        return lines * (font.get_height() + line_spacing) - line_spacing

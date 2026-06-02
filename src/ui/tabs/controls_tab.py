from typing import Optional, TYPE_CHECKING

import pygame

from settings import SETTINGS
from ui.tabs.settings_tab import SettingsTab
from utils.localization import tr

if TYPE_CHECKING:
    from utils.settings_manager import SettingsManager


class ControlsTab(SettingsTab):
    CONTENT_PADDING = 24
    OPTION_ROW_HEIGHT = 40
    OPTION_ROW_GAP = 2
    TITLE_TO_OPTIONS_GAP = 0
    FOOTER_HELP_BOTTOM_GAP = 2
    FOOTER_HELP_TO_BUTTON_GAP = 4
    FOOTER_STATUS_TO_HELP_GAP = 2
    LABEL_LEFT_PADDING = 16
    VALUE_RIGHT_PADDING = 16
    MIN_LABEL_VALUE_GAP = 16
    ROW_VERTICAL_PADDING = 8
    LABEL_LINE_SPACING = 2
    LABEL_WIDTH_RATIO = 0.55

    OPTIONS = [
        ("controls.actions.left", "controls.left"),
        ("controls.actions.right", "controls.right"),
        ("controls.actions.soft_drop", "controls.soft_drop"),
        ("controls.actions.hard_drop", "controls.hard_drop"),
        ("controls.actions.rotate", "controls.rotate"),
        ("controls.actions.hold", "controls.hold"),
        ("controls.actions.pause", "controls.pause"),
    ]

    def __init__(self) -> None:
        super().__init__(
            id="controls",
            icon_name="gamepad",
            order=10,
            category="controls",
            title_key="settings.tabs.controls",
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

        title_y, content_center_x, _ = self._draw_tab_background_and_title(
            surface,
            rect,
            self.get_title(),
            self.CONTENT_PADDING,
        )
        
        title_surface = self._render_text_surface(
            self.get_title(),
            SETTINGS.UI_TYPOGRAPHY.TITLE,
            SETTINGS.UI_THEME.CYAN,
        )
        options_start_y = title_y + title_surface.get_height() + self.TITLE_TO_OPTIONS_GAP
        
        row_x = rect.x + self.CONTENT_PADDING
        row_width = rect.width - self.CONTENT_PADDING * 2
        row_font = self._font(SETTINGS.UI_TYPOGRAPHY.BODY)

        available_text_width = (
            row_width 
            - self.LABEL_LEFT_PADDING 
            - self.VALUE_RIGHT_PADDING 
            - self.MIN_LABEL_VALUE_GAP
        )
        max_label_width = int(available_text_width * self.LABEL_WIDTH_RATIO)
        max_binding_width = available_text_width - max_label_width

        current_row_y = options_start_y
        for index, (label_key, path) in enumerate(self.OPTIONS):
            label_text = tr(label_key)
            
            binding_text = tr("controls.binding.unbound")
            if self._pending_keybind_path == path:
                binding_text = tr("controls.binding.press_key")
            elif self.settings_manager is not None:
                try:
                    key_code = self.settings_manager.get(path)
                    if isinstance(key_code, int):
                        key_name = pygame.key.name(key_code)
                        binding_text = key_name.upper() if key_name else str(key_code)
                except (KeyError, TypeError, ValueError):
                    pass
            
            label_height = self._wrapped_text_height(
                label_text,
                SETTINGS.UI_TYPOGRAPHY.BODY,
                max_label_width,
                line_spacing=self.LABEL_LINE_SPACING,
            )
            binding_height = self._wrapped_text_height(
                binding_text,
                SETTINGS.UI_TYPOGRAPHY.BODY,
                max_binding_width,
                line_spacing=self.LABEL_LINE_SPACING,
            )
            
            text_height = max(label_height, binding_height)
            row_height = max(self.OPTION_ROW_HEIGHT, text_height + self.ROW_VERTICAL_PADDING)
            row_rect = pygame.Rect(row_x, current_row_y, row_width, row_height)
            self._option_hitboxes.append((path, row_rect))

            is_hovered = path == self.hovered_option_path
            self._draw_binding_row(
                surface,
                row_rect,
                label_text,
                binding_text,
                row_font,
                max_label_width,
                max_binding_width,
                is_hovered=is_hovered,
                is_pending=self._pending_keybind_path == path,
            )

            current_row_y += row_height + self.OPTION_ROW_GAP

        help_text = tr("controls.binding.help")
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

        # Anchor footer to bottom
        reset_button_height = 42
        reset_button_y = rect.y + rect.height - self.CONTENT_PADDING - reset_button_height
        
        help_bottom = reset_button_y - self.FOOTER_HELP_TO_BUTTON_GAP
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
            status_bottom = help_top - self.FOOTER_STATUS_TO_HELP_GAP
            status_top = status_bottom - status_height
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
                self._status_message = tr("controls.binding.prompt")
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
                self._status_message = tr("controls.binding.conflict", action=conflict)
                self._status_is_error = True
                self._pending_keybind_path = None
                return

            self.settings_manager.set(self._pending_keybind_path, int(event.key))
            self._status_message = tr("controls.binding.updated")
            self._status_is_error = False
        except (KeyError, TypeError, ValueError):
            self._status_message = tr("controls.binding.failed")
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
            self._status_message = tr("controls.binding.canceled")
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

        action_label_keys = {
            "left": "controls.actions.left",
            "right": "controls.actions.right",
            "soft_drop": "controls.actions.soft_drop",
            "hard_drop": "controls.actions.hard_drop",
            "rotate": "controls.actions.rotate",
            "hold": "controls.actions.hold",
            "pause": "controls.actions.pause",
        }

        target_action = target_path.split(".")[-1]
        for action, key_code in controls.items():
            if action == target_action:
                continue
            if isinstance(key_code, int) and key_code == new_key:
                key = action_label_keys.get(action)
                if key is None:
                    return action.replace("_", " ").title()
                return tr(key)
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

    def _draw_binding_row(
        self,
        surface: pygame.Surface,
        row_rect: pygame.Rect,
        label_text: str,
        binding_text: str,
        font: pygame.font.Font,
        max_label_width: int,
        max_binding_width: int,
        *,
        is_hovered: bool,
        is_pending: bool,
    ) -> None:
        from ui.styles.settings import SETTINGS_STYLE
        
        bg_color = SETTINGS_STYLE.ROW_BG_HOVER if is_hovered else SETTINGS_STYLE.ROW_BG
        pygame.draw.rect(surface, bg_color, row_rect, border_radius=10)

        label_height = self._wrapped_text_height(
            label_text,
            SETTINGS.UI_TYPOGRAPHY.BODY,
            max_label_width,
            line_spacing=self.LABEL_LINE_SPACING,
        )
        binding_height = self._wrapped_text_height(
            binding_text,
            SETTINGS.UI_TYPOGRAPHY.BODY,
            max_binding_width,
            line_spacing=self.LABEL_LINE_SPACING,
        )
        
        label_start_y = row_rect.centery - label_height // 2
        binding_start_y = row_rect.centery - binding_height // 2
        
        self._draw_wrapped_text(
            surface,
            label_text,
            SETTINGS.UI_TYPOGRAPHY.BODY,
            SETTINGS.UI_THEME.TEXT_PRIMARY,
            max_label_width,
            line_spacing=self.LABEL_LINE_SPACING,
            x=row_rect.left + self.LABEL_LEFT_PADDING,
            y=label_start_y,
            align="left",
        )

        binding_color = SETTINGS.UI_THEME.CYAN if is_pending else SETTINGS.UI_THEME.TEXT_PRIMARY
        binding_x = row_rect.right - self.VALUE_RIGHT_PADDING
        self._draw_wrapped_text(
            surface,
            binding_text,
            SETTINGS.UI_TYPOGRAPHY.BODY,
            binding_color,
            max_binding_width,
            line_spacing=self.LABEL_LINE_SPACING,
            x=binding_x,
            y=binding_start_y,
            align="right",
        )

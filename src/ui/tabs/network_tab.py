from typing import Optional

import pygame

from settings import SETTINGS
from ui.styles import SETTINGS_STYLE
from ui.tabs.settings_tab import SettingsTab


class NetworkTab(SettingsTab):
    CONTENT_PADDING = 30
    SECTION_GAP = 20
    OPTION_ROW_HEIGHT = 44
    OPTION_ROW_GAP = 12
    DROPDOWN_HEIGHT = 40
    DROPDOWN_OPTION_HEIGHT = 36

    POLICY_LABELS = {
        "auto": "Automatic",
        "manual": "Manual",
        "always": "Always",
    }

    POLICY_DESCRIPTIONS = {
        "auto": "Reconnect automatically when connection is lost",
        "manual": "Require user action to reconnect",
        "always": "Keep trying to reconnect indefinitely",
    }

    def __init__(self) -> None:
        super().__init__(
            id="network",
            title="Network",
            icon_name="router",
            order=30,
            category="network",
        )
        self._checkbox_hitboxes: list[tuple[str, pygame.Rect]] = []
        self._dropdown_hitbox: Optional[pygame.Rect] = None
        self._dropdown_open: bool = False
        self._dropdown_option_hitboxes: list[tuple[str, pygame.Rect]] = []
        self.hovered_checkbox_path: Optional[str] = None
        self.hovered_dropdown_option: Optional[str] = None
        self._keyboard_selected_index: int = 0
        self._options_list: list[str] = ["auto", "manual", "always"]

    def render(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
    ) -> None:
        self._checkbox_hitboxes = []
        self._dropdown_option_hitboxes = []

        _, _, current_y = self._draw_tab_background_and_title(
            surface,
            rect,
            self.title,
            self.CONTENT_PADDING,
        )

        start_offline = False
        reconnect_policy = "auto"
        if self.settings_manager is not None:
            try:
                start_offline = self.settings_manager.get_bool("network.start_offline")
            except (KeyError, TypeError, ValueError):
                start_offline = False
            try:
                reconnect_policy = str(self.settings_manager.get("network.reconnect_policy"))
            except (KeyError, TypeError, ValueError):
                reconnect_policy = "auto"

        current_y = self._render_checkbox_option(
            surface,
            rect,
            "Start Offline",
            "network.start_offline",
            start_offline,
            current_y,
        )
        
        help_text = "Launch the game without connecting to the server"
        current_y = self._render_help_text(
            surface,
            rect,
            help_text,
            current_y,
        )

        current_y += self.SECTION_GAP

        current_y = self._render_dropdown_option(
            surface,
            rect,
            "Reconnection Policy",
            reconnect_policy,
            current_y,
        )
        
        display_option = reconnect_policy
        if self._dropdown_open and self.hovered_dropdown_option:
            display_option = self.hovered_dropdown_option
        elif self._dropdown_open:
            display_option = self._options_list[self._keyboard_selected_index]
        
        description = self.POLICY_DESCRIPTIONS.get(display_option, "")
        if description:
            current_y = self._render_help_text(surface, rect, description, current_y)
        
        reset_button_y = self._bottom_action_y(rect, self.CONTENT_PADDING, action_height=42)
        self.render_reset_button(surface, rect, reset_button_y)

    def _render_checkbox_option(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        label: str,
        path: str,
        checked: bool,
        y_pos: int,
    ) -> int:
        row_font = self._font(SETTINGS.UI_TYPOGRAPHY.BODY)
        row_x = rect.x + self.CONTENT_PADDING
        row_width = rect.width - self.CONTENT_PADDING * 2
        row_rect = pygame.Rect(row_x, y_pos, row_width, self.OPTION_ROW_HEIGHT)
        self._checkbox_hitboxes.append((path, row_rect))

        is_hovered = path == self.hovered_checkbox_path
        self._draw_option_row(surface, row_rect, label, row_font, is_hovered=is_hovered)

        checkbox_checked = self._try_load_icon("checkbox-marked")
        checkbox_empty = self._try_load_icon("checkbox-blank")
        icon = checkbox_checked if checked else checkbox_empty
        self._draw_row_icon_right(surface, row_rect, icon)

        return y_pos + self.OPTION_ROW_HEIGHT + self.OPTION_ROW_GAP

    def _render_dropdown_option(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        label: str,
        current_value: str,
        y_pos: int,
    ) -> int:
        label_font = self._font(SETTINGS.UI_TYPOGRAPHY.BODY)
        option_font = self._font(SETTINGS.UI_TYPOGRAPHY.BODY)
        
        label_row_x = rect.x + self.CONTENT_PADDING
        label_row_width = rect.width - self.CONTENT_PADDING * 2
        label_row_rect = pygame.Rect(label_row_x, y_pos, label_row_width, self.OPTION_ROW_HEIGHT)
        
        label_surface = label_font.render(label, True, SETTINGS.UI_THEME.TEXT_PRIMARY)
        label_rect = label_surface.get_rect(midleft=(label_row_rect.left + 16, label_row_rect.centery))
        surface.blit(label_surface, label_rect)

        dropdown_y = y_pos + self.OPTION_ROW_HEIGHT + self.OPTION_ROW_GAP
        dropdown_x = rect.x + self.CONTENT_PADDING
        dropdown_width = rect.width - self.CONTENT_PADDING * 2
        dropdown_rect = pygame.Rect(dropdown_x, dropdown_y, dropdown_width, self.DROPDOWN_HEIGHT)
        self._dropdown_hitbox = pygame.Rect(
            self.CONTENT_PADDING,
            dropdown_y - rect.y,
            dropdown_width,
            self.DROPDOWN_HEIGHT
        )

        bg_color = SETTINGS_STYLE.DROPDOWN_BG
        border_color = SETTINGS.UI_THEME.PURPLE if self._dropdown_open else SETTINGS_STYLE.DROPDOWN_BORDER
        pygame.draw.rect(surface, bg_color, dropdown_rect, border_radius=8)
        pygame.draw.rect(surface, border_color, dropdown_rect, width=2, border_radius=8)

        value_text = self.POLICY_LABELS.get(current_value, current_value.capitalize())
        value_surface = option_font.render(value_text, True, SETTINGS.UI_THEME.TEXT_PRIMARY)
        value_rect = value_surface.get_rect(midleft=(dropdown_rect.left + 16, dropdown_rect.centery))
        surface.blit(value_surface, value_rect)

        arrow_icon = self._try_load_icon("chevron-down" if not self._dropdown_open else "chevron-up")
        if arrow_icon:
            arrow_scaled = pygame.transform.scale(arrow_icon, (20, 20))
            arrow_rect = arrow_scaled.get_rect(midright=(dropdown_rect.right - 12, dropdown_rect.centery))
            surface.blit(arrow_scaled, arrow_rect)

        next_y = dropdown_y + self.DROPDOWN_HEIGHT

        if self._dropdown_open:
            next_y += 4
            actual_idx = 0
            for idx, option in enumerate(self._options_list):
                option_y = next_y + actual_idx * (self.DROPDOWN_OPTION_HEIGHT + 2)
                option_rect = pygame.Rect(dropdown_x, option_y, dropdown_width, self.DROPDOWN_OPTION_HEIGHT)
                option_rect_relative = pygame.Rect(
                    self.CONTENT_PADDING,
                    option_y - rect.y,
                    dropdown_width,
                    self.DROPDOWN_OPTION_HEIGHT
                )
                self._dropdown_option_hitboxes.append((option, option_rect_relative))

                is_current = option == current_value
                is_hovered = option == self.hovered_dropdown_option
                is_keyboard_selected = idx == self._keyboard_selected_index
                
                if is_current:
                    option_bg_color = SETTINGS_STYLE.DROPDOWN_OPTION_BG_SELECTED
                    text_color = SETTINGS.UI_THEME.CYAN
                elif is_hovered or is_keyboard_selected:
                    option_bg_color = SETTINGS_STYLE.DROPDOWN_OPTION_BG_HOVER
                    text_color = SETTINGS.UI_THEME.TEXT_PRIMARY
                else:
                    option_bg_color = SETTINGS_STYLE.DROPDOWN_OPTION_BG
                    text_color = SETTINGS.UI_THEME.TEXT_PRIMARY

                pygame.draw.rect(surface, option_bg_color, option_rect, border_radius=6)

                option_label = self.POLICY_LABELS.get(option, option.capitalize())
                option_surface = option_font.render(option_label, True, text_color)
                option_text_rect = option_surface.get_rect(midleft=(option_rect.left + 16, option_rect.centery))
                surface.blit(option_surface, option_text_rect)

                if is_current:
                    check_icon = self._try_load_icon("check")
                    if check_icon:
                        check_scaled = pygame.transform.scale(check_icon, (18, 18))
                        check_rect = check_scaled.get_rect(midright=(option_rect.right - 12, option_rect.centery))
                        surface.blit(check_scaled, check_rect)

                actual_idx += 1

            next_y += len(self._options_list) * (self.DROPDOWN_OPTION_HEIGHT + 2) + 4
        else:
            next_y += self.OPTION_ROW_GAP

        return next_y

    def _render_help_text(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        text: str,
        y_pos: int,
    ) -> int:
        max_width = rect.width - self.CONTENT_PADDING * 2
        next_y = self._draw_wrapped_text(
            surface,
            text,
            SETTINGS.UI_TYPOGRAPHY.SMALL,
            SETTINGS.UI_THEME.TEXT_MUTED,
            max_width,
            line_spacing=2,
            x=rect.x + self.CONTENT_PADDING,
            y=y_pos + 4,
            align="left",
        )
        return next_y + 6

    def handle_click(
        self,
        pos: tuple[int, int],
    ) -> None:
        if self.settings_manager is None:
            return

        for path, rect in self._checkbox_hitboxes:
            if rect.collidepoint(pos):
                try:
                    current = self.settings_manager.get_bool(path)
                    self.settings_manager.set(path, not current)
                except (KeyError, TypeError, ValueError):
                    pass
                return

        if self._dropdown_hitbox and self._dropdown_hitbox.collidepoint(pos):
            self._dropdown_open = not self._dropdown_open
            if self._dropdown_open and self.settings_manager is not None:
                try:
                    current = self.settings_manager.get("network.reconnect_policy")
                    self._keyboard_selected_index = self._options_list.index(current)
                except (KeyError, TypeError, ValueError):
                    self._keyboard_selected_index = 0
            return

        if self._dropdown_open:
            for option, rect in self._dropdown_option_hitboxes:
                if rect.collidepoint(pos):
                    try:
                        current = self.settings_manager.get("network.reconnect_policy")
                        if option != current:
                            self.settings_manager.set("network.reconnect_policy", option)
                        self._dropdown_open = False
                    except (KeyError, TypeError, ValueError):
                        self._dropdown_open = False
                    return

    def handle_mouse_motion(self, pos: tuple[int, int]) -> None:
        self.hovered_checkbox_path = None
        self.hovered_dropdown_option = None

        for path, rect in self._checkbox_hitboxes:
            if rect.collidepoint(pos):
                self.hovered_checkbox_path = path
                return

        if self._dropdown_open:
            for idx, (option, rect) in enumerate(self._dropdown_option_hitboxes):
                if rect.collidepoint(pos):
                    self.hovered_dropdown_option = option
                    self._keyboard_selected_index = idx
                    return

    def handle_key(
        self,
        event: pygame.event.Event,
    ) -> None:
        if not self._dropdown_open or event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_UP, pygame.K_w):
            self._keyboard_selected_index = (self._keyboard_selected_index - 1) % len(self._options_list)
            self.hovered_dropdown_option = None
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self._keyboard_selected_index = (self._keyboard_selected_index + 1) % len(self._options_list)
            self.hovered_dropdown_option = None
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.settings_manager is not None:
                selected_option = self._options_list[self._keyboard_selected_index]
                try:
                    self.settings_manager.set("network.reconnect_policy", selected_option)
                except (KeyError, TypeError, ValueError):
                    pass
            self._dropdown_open = False
        elif event.key == pygame.K_ESCAPE:
            self._dropdown_open = False

    def has_dropdown_open(self) -> bool:
        return self._dropdown_open

from typing import Callable, List, Optional, TYPE_CHECKING

import pygame

from settings import SETTINGS
from ui.assets import AssetManager
from ui.screen import Screen
from ui.styles import SETTINGS_STYLE
from ui.tabs import SettingsTab, SettingsTabRegistry
from utils.localization import tr

if TYPE_CHECKING:
    from ui.audio import AudioManager
    from utils.settings_manager import SettingsManager


class SettingsScreen(Screen):
    SIDEBAR_WIDTH = 88
    TAB_ICON_SIZE = 34
    TAB_CELL_SIZE = 56
    TAB_GAP = 14
    TAB_START_Y = 24
    RESET_ALL_BUTTON_SIZE = 44
    RESET_ALL_FOOTER_MARGIN = 20
    RESET_ALL_CONFIRM_MS = 2200

    def __init__(
        self,
        return_screen_provider: Callable[[], str],
        assets: Optional[AssetManager] = None,
        audio_manager: Optional["AudioManager"] = None,
        settings_manager: Optional["SettingsManager"] = None,
    ) -> None:
        super().__init__(assets, audio_manager)
        self.return_screen_provider = return_screen_provider
        self.registry = SettingsTabRegistry()
        self.registry.distribute_assets(self.assets)
        self.settings_manager = settings_manager
        self.active_tab_id: Optional[str] = None
        self.hovered_tab_id: Optional[str] = None
        self._tab_hitboxes: dict[str, pygame.Rect] = {}
        self._tooltip: Optional[tuple[str, tuple[int, int]]] = None
        self._mouse_button_down: bool = False
        self._reset_all_hitbox: Optional[pygame.Rect] = None
        self._reset_all_hovered: bool = False
        self._reset_all_armed_until_ms: int = 0

    @property
    def assets(self) -> Optional[AssetManager]:
        return getattr(self, "_assets", None)

    @assets.setter
    def assets(self, value: Optional[AssetManager]) -> None:
        self._assets = value
        if hasattr(self, "registry"):
            self.registry.distribute_assets(value)

    @property
    def settings_manager(self) -> Optional["SettingsManager"]:
        return getattr(self, "_settings_manager", None)

    @settings_manager.setter
    def settings_manager(self, value: Optional["SettingsManager"]) -> None:
        self._settings_manager = value
        if hasattr(self, "registry"):
            self.registry.distribute_settings_manager(value)

    def _ensure_active_tab(self) -> None:
        if self.active_tab_id is not None:
            return
        tabs = self.registry.get_all()
        if tabs:
            self.active_tab_id = tabs[0].id

    def _select_adjacent_tab(self, direction: int) -> None:
        tabs = self.registry.get_all()
        if not tabs:
            return

        self._ensure_active_tab()
        if self.active_tab_id is None:
            return

        current_tab = self._get_active_tab()
        if current_tab is not None and hasattr(current_tab, 'clear_status'):
            current_tab.clear_status()

        current_index = 0
        for index, tab in enumerate(tabs):
            if tab.id == self.active_tab_id:
                current_index = index
                break

        next_index = (current_index + direction) % len(tabs)
        self.active_tab_id = tabs[next_index].id

    def handle_events(self, events: List[pygame.event.Event]) -> Optional[str]:
        self._ensure_active_tab()
        active_tab = self._get_active_tab()
        tab_is_capturing = active_tab is not None and hasattr(active_tab, 'has_pending_keybind') and active_tab.has_pending_keybind()
        dropdown_is_open = active_tab is not None and hasattr(active_tab, 'has_dropdown_open') and active_tab.has_dropdown_open()

        for event in events:
            if event.type == pygame.QUIT:
                return SETTINGS.SCREEN_NAMES.QUIT

            if self._handle_network_status_event(event, enabled=self.active_tab_id == "network"):
                continue

            if event.type == pygame.KEYDOWN:
                if tab_is_capturing or dropdown_is_open:
                    if active_tab is not None:
                        active_tab.handle_key(event)
                    continue

                if event.key == pygame.K_ESCAPE:
                    return self.return_screen_provider()
                if event.key in (pygame.K_UP, pygame.K_w):
                    self._select_adjacent_tab(-1)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self._select_adjacent_tab(1)

            if event.type == pygame.MOUSEMOTION:
                if self._mouse_button_down:
                    active_tab = self._get_active_tab()
                    if active_tab is not None and hasattr(active_tab, 'handle_drag'):
                        content_rect = self._get_content_rect(pygame.display.get_surface())
                        adjusted_pos = (event.pos[0] - content_rect.x, event.pos[1] - content_rect.y)
                        active_tab.handle_drag(adjusted_pos)
                self._handle_mouse_motion(event.pos)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self._reset_all_hitbox and self._reset_all_hitbox.collidepoint(event.pos):
                        now_ms = pygame.time.get_ticks()
                        if now_ms <= self._reset_all_armed_until_ms:
                            if self.settings_manager is not None:
                                self.settings_manager.reset_to_defaults()
                            self._reset_all_armed_until_ms = 0
                        else:
                            self._reset_all_armed_until_ms = now_ms + self.RESET_ALL_CONFIRM_MS
                        continue
                    
                    tab_clicked = False
                    for tab_id, rect in self._tab_hitboxes.items():
                        if rect.collidepoint(event.pos):
                            if tab_id != self.active_tab_id:
                                current_tab = self._get_active_tab()
                                if current_tab is not None and hasattr(current_tab, 'clear_status'):
                                    current_tab.clear_status()
                            self.active_tab_id = tab_id
                            tab_clicked = True
                            break
                    
                    if not tab_clicked:
                        active_tab = self._get_active_tab()
                        if active_tab is not None:
                            content_rect = self._get_content_rect(pygame.display.get_surface())
                            if content_rect.collidepoint(event.pos):
                                adjusted_pos = (event.pos[0] - content_rect.x, event.pos[1] - content_rect.y)
                                
                                if active_tab.check_reset_button_click(adjusted_pos):
                                    if self.settings_manager is not None:
                                        self.settings_manager.reset_subtree(active_tab.category)
                                    continue
                                
                                self._mouse_button_down = True
                                if hasattr(active_tab, 'handle_mouse_button_down'):
                                    active_tab.handle_mouse_button_down(adjusted_pos)
                                else:
                                    active_tab.handle_click(adjusted_pos)
                elif event.button == 3 and tab_is_capturing:
                    if active_tab is not None and hasattr(active_tab, 'cancel_keybind_capture'):
                        active_tab.cancel_keybind_capture()

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self._mouse_button_down = False
                    active_tab = self._get_active_tab()
                    if active_tab is not None and hasattr(active_tab, 'handle_mouse_button_up'):
                        active_tab.handle_mouse_button_up()

        return None

    def _handle_mouse_motion(self, pos: tuple[int, int]) -> None:
        self._tooltip = None
        self.hovered_tab_id = None
        self._reset_all_hovered = False
        
        if self._reset_all_hitbox and self._reset_all_hitbox.collidepoint(pos):
            self._reset_all_hovered = True
            is_armed = pygame.time.get_ticks() <= self._reset_all_armed_until_ms
            if is_armed:
                self._tooltip = (tr("settings.reset.confirm"), pos)
            else:
                self._tooltip = (tr("settings.reset.all"), pos)
            return

        for tab_id, rect in self._tab_hitboxes.items():
            if rect.collidepoint(pos):
                self.hovered_tab_id = tab_id
                tab = self.registry.get_by_id(tab_id)
                if tab is not None:
                    self._tooltip = (tab.get_title(), pos)
                break

        active_tab = self._get_active_tab()
        if active_tab is not None and hasattr(active_tab, 'handle_mouse_motion'):
            content_rect = self._get_content_rect(pygame.display.get_surface())
            adjusted_pos = (pos[0] - content_rect.x, pos[1] - content_rect.y)
            active_tab.set_reset_button_hovered(adjusted_pos)
            active_tab.handle_mouse_motion(adjusted_pos)
        elif active_tab is not None:
            active_tab.set_reset_button_hovered((-1, -1))

    def update(self, _delta_time: float) -> Optional[str]:
        if self._reset_all_armed_until_ms > 0 and pygame.time.get_ticks() > self._reset_all_armed_until_ms:
            self._reset_all_armed_until_ms = 0
        return None

    def _get_active_tab(self) -> Optional[SettingsTab]:
        if self.active_tab_id is None:
            return None
        return self.registry.get_by_id(self.active_tab_id)

    def _get_content_rect(self, surface: pygame.Surface) -> pygame.Rect:
        return pygame.Rect(
            self.SIDEBAR_WIDTH,
            0,
            surface.get_width() - self.SIDEBAR_WIDTH,
            surface.get_height()
        )

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(SETTINGS_STYLE.SCREEN_BG)
        self._ensure_active_tab()
        self._tab_hitboxes = {}

        tabs = self.registry.get_all()

        if not tabs:
            self._render_empty_state(surface)
            return

        self._render_sidebar(surface, tabs)
        self._render_content(surface)
        self._render_reset_all_button(surface)
        self._render_network_status(surface, enabled=self.active_tab_id == "network")
        self._render_tooltip(surface)

    def _render_empty_state(self, surface: pygame.Surface) -> None:
        center_x = surface.get_width() // 2
        center_y = surface.get_height() // 2
        max_width = surface.get_width() - 60
        
        self._draw_text(
            surface,
            tr("settings.empty.title"),
            SETTINGS.UI_TYPOGRAPHY.TITLE,
            SETTINGS.UI_THEME.TEXT_MUTED,
            (center_x, center_y - 60)
        )
        
        self._draw_wrapped_text(
            surface,
            tr("settings.empty.description"),
            SETTINGS.UI_TYPOGRAPHY.BODY,
            SETTINGS.UI_THEME.TEXT_MUTED,
            (center_x, center_y),
            max_width
        )
    def _render_sidebar(self, surface: pygame.Surface, tabs: List[SettingsTab]) -> None:
        sidebar_rect = pygame.Rect(0, 0, self.SIDEBAR_WIDTH, surface.get_height())
        pygame.draw.rect(surface, SETTINGS_STYLE.SIDEBAR_BG, sidebar_rect)

        divider_x = self.SIDEBAR_WIDTH - 1
        pygame.draw.line(surface, SETTINGS_STYLE.DIVIDER, (divider_x, 0), (divider_x, surface.get_height()), 1)

        start_y = self.TAB_START_Y

        for index, tab in enumerate(tabs):
            tab_y = start_y + index * (self.TAB_CELL_SIZE + self.TAB_GAP)
            tab_x = (self.SIDEBAR_WIDTH - self.TAB_CELL_SIZE) // 2
            tab_rect = pygame.Rect(tab_x, tab_y, self.TAB_CELL_SIZE, self.TAB_CELL_SIZE)
            self._tab_hitboxes[tab.id] = tab_rect

            is_active = tab.id == self.active_tab_id
            is_hovered = tab.id == self.hovered_tab_id

            bg_color = SETTINGS_STYLE.TAB_BG
            if is_hovered:
                bg_color = SETTINGS_STYLE.TAB_BG_HOVER
            if is_active:
                bg_color = SETTINGS_STYLE.TAB_BG_ACTIVE
            pygame.draw.rect(surface, bg_color, tab_rect, border_radius=10)

            icon = self._try_load_icon(tab.icon_name)
            if icon:
                icon_scaled = pygame.transform.scale(icon, (self.TAB_ICON_SIZE, self.TAB_ICON_SIZE))
                icon_rect = icon_scaled.get_rect(center=tab_rect.center)
                surface.blit(icon_scaled, icon_rect)

            if is_active:
                underline_width = self.TAB_CELL_SIZE - 18
                underline_height = 3
                underline_rect = pygame.Rect(
                    tab_rect.centerx - underline_width // 2,
                    tab_rect.bottom - 7,
                    underline_width,
                    underline_height,
                )
                pygame.draw.rect(surface, SETTINGS.UI_THEME.PURPLE, underline_rect, border_radius=2)

        footer_top = surface.get_height() - self.RESET_ALL_BUTTON_SIZE - self.RESET_ALL_FOOTER_MARGIN - 12
        divider_y = footer_top - 10
        pygame.draw.line(
            surface,
            SETTINGS_STYLE.DIVIDER,
            (10, divider_y),
            (self.SIDEBAR_WIDTH - 10, divider_y),
            1,
        )

    def _render_content(self, surface: pygame.Surface) -> None:
        active_tab = self._get_active_tab()
        if active_tab is None:
            return

        content_rect = self._get_content_rect(surface)
        active_tab.render(surface, content_rect)

    def _render_reset_all_button(self, surface: pygame.Surface) -> None:
        button_size = self.RESET_ALL_BUTTON_SIZE
        button_x = (self.SIDEBAR_WIDTH - button_size) // 2
        button_y = surface.get_height() - button_size - self.RESET_ALL_FOOTER_MARGIN
        
        button_rect = pygame.Rect(button_x, button_y, button_size, button_size)
        self._reset_all_hitbox = button_rect

        is_armed = pygame.time.get_ticks() <= self._reset_all_armed_until_ms
        
        if is_armed:
            bg_color = SETTINGS_STYLE.RESET_BG_ARMED
            border_color = SETTINGS_STYLE.RESET_BORDER_ARMED
        elif self._reset_all_hovered:
            bg_color = SETTINGS_STYLE.RESET_BG_HOVER
            border_color = SETTINGS_STYLE.RESET_BORDER_HOVER
        else:
            bg_color = SETTINGS_STYLE.RESET_BG
            border_color = SETTINGS_STYLE.RESET_BORDER

        pygame.draw.rect(surface, bg_color, button_rect, border_radius=8)
        pygame.draw.rect(surface, border_color, button_rect, width=1, border_radius=8)
        
        icon_name = "cancel" if is_armed else "trash"
        icon = self._try_load_icon(icon_name)
        if icon:
            icon_scaled = pygame.transform.scale(icon, (22, 22))
            icon_rect = icon_scaled.get_rect(center=button_rect.center)
            surface.blit(icon_scaled, icon_rect)

    def _render_tooltip(
        self,
        surface: pygame.Surface,
        tooltip: Optional[tuple[str, tuple[int, int]]] = None,
    ) -> None:
        tooltip_to_render = tooltip or self._tooltip
        if tooltip_to_render is None:
            return

        super()._render_tooltip(surface, tooltip_to_render)

    def _try_load_icon(self, icon_name: str) -> Optional[pygame.Surface]:
        if not self.assets:
            return None
        try:
            return self.assets.get_image(icon_name)
        except (KeyError, FileNotFoundError):
            return None

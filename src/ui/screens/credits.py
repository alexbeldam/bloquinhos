from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple
import pygame

from settings import SETTINGS
from ui.screen import Screen
from ui.styles import CREDITS_STYLE
from utils.browser import open_url
from utils.localization import tr


@dataclass(frozen=True)
class CreditItem:
    base_path: str

    @property
    def name(self) -> str:
        return tr(f"{self.base_path}.name")

    @property
    def subtext(self) -> str:
        return tr(f"{self.base_path}.subtext")

    @property
    def url(self) -> Optional[str]:
        link = tr(f"{self.base_path}.url")

        if link and not link.startswith("credits."):
            return link
        return None

@dataclass(frozen=True)
class CreditCategory:
    role_key: str
    items: Sequence[CreditItem]

    @property
    def role(self) -> str:
        return tr(self.role_key)


class CreditsScreen(Screen):
    def __init__(self, assets: Optional[object] = None, audio_manager: Optional[object] = None) -> None:
        super().__init__(assets, audio_manager)
        
        self.credits_data: Sequence[CreditCategory] = (
            CreditCategory(
                role_key="credits.roles.developers",
                items=(
                    CreditItem("credits.alex"),
                    CreditItem("credits.bernardo"),
                )
            ),
            CreditCategory(
                role_key="credits.roles.typography",
                items=(
                    CreditItem("credits.font_asset"),
                )
            ),
            CreditCategory(
                role_key="credits.roles.art_assets",
                items=(
                    CreditItem("credits.icon_asset"),
                )
            ),
        )
        
        self._clickable_hitboxes: List[Tuple[pygame.Rect, str]] = []

    def handle_events(self, events: List[pygame.event.Event]) -> Optional[str]:
        for event in events:
            if event.type == pygame.QUIT:
                return SETTINGS.SCREEN_NAMES.QUIT
                
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_ESCAPE,
                pygame.K_RETURN,
                pygame.K_SPACE,
            ):
                return SETTINGS.SCREEN_NAMES.MENU
                
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for hitbox, url in self._clickable_hitboxes:
                    if hitbox.collidepoint(event.pos):
                        open_url(url)
                        return None
                        
        return None

    def update(self, _delta_time: float) -> Optional[str]:
        return None

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(SETTINGS.UI_THEME.BG_DARKER)
        
        center_x = surface.get_width() // 2
        mouse_pos = pygame.mouse.get_pos()
        self._clickable_hitboxes.clear()
        
        self._draw_text(
            surface,
            tr("credits.title"),
            SETTINGS.UI_TYPOGRAPHY.DISPLAY,
            SETTINGS.UI_THEME.PINK,
            (center_x, 75),
        )
        
        start_y = 170
        row_spacing = CREDITS_STYLE.ROW_SPACING
        
        left_edge_x = CREDITS_STYLE.CONTENT_PADDING
        right_edge_x = surface.get_width() - CREDITS_STYLE.CONTENT_PADDING
        row_width = right_edge_x - left_edge_x
        
        max_role_width = int(row_width * CREDITS_STYLE.LABEL_WIDTH_RATIO)
        max_details_width = row_width - max_role_width - CREDITS_STYLE.MIN_LABEL_VALUE_GAP
        
        current_y = start_y
        
        for category in self.credits_data:
            self._draw_wrapped_text(
                surface,
                category.role,
                SETTINGS.UI_TYPOGRAPHY.BODY,
                SETTINGS.UI_THEME.PURPLE,
                (left_edge_x, current_y),
                max_width=max_role_width,
                line_spacing=CREDITS_STYLE.LINE_SPACING,
                align="left",
                valign="top"
            )
            
            block_start_y = current_y
            
            for item in category.items:
                name_str = item.name
                url_str = item.url
                
                name_font = self._font(SETTINGS.UI_TYPOGRAPHY.BODY)
                name_width = min(max_details_width, name_font.size(name_str)[0])
                name_height = name_font.get_height()
                
                subtext_font = self._font(SETTINGS.UI_TYPOGRAPHY.SMALL)
                subtext_height = subtext_font.get_height()
                
                details_total_height = name_height + CREDITS_STYLE.LINE_SPACING + subtext_height
                
                name_left_x = right_edge_x - name_width
                name_rect = pygame.Rect(name_left_x, block_start_y, name_width, name_height)
                
                is_hovered = url_str is not None and name_rect.collidepoint(mouse_pos)
                text_color = SETTINGS.UI_THEME.CYAN if is_hovered else SETTINGS.UI_THEME.TEXT_PRIMARY
                
                if is_hovered and url_str:
                    self._clickable_hitboxes.append((name_rect, url_str))
                
                self._draw_wrapped_text(
                    surface,
                    name_str,
                    SETTINGS.UI_TYPOGRAPHY.BODY,
                    text_color,
                    (right_edge_x, block_start_y),
                    max_width=max_details_width,
                    line_spacing=CREDITS_STYLE.LINE_SPACING,
                    align="right",
                    valign="top"
                )
                
                if is_hovered and url_str:
                    pygame.draw.line(surface, SETTINGS.UI_THEME.CYAN, (name_rect.left, name_rect.bottom - 1), (name_rect.right, name_rect.bottom - 1), 1)
                
                subtext_start_y = block_start_y + name_height + CREDITS_STYLE.LINE_SPACING
                self._draw_wrapped_text(
                    surface,
                    item.subtext,
                    SETTINGS.UI_TYPOGRAPHY.SMALL,
                    SETTINGS.UI_THEME.TEXT_MUTED,
                    (right_edge_x, subtext_start_y),
                    max_width=max_details_width,
                    line_spacing=CREDITS_STYLE.LINE_SPACING,
                    align="right",
                    valign="top"
                )
                
                block_start_y += details_total_height + 8
            
            role_height = self._font(SETTINGS.UI_TYPOGRAPHY.BODY).get_height()
            total_block_height = max(role_height, block_start_y - current_y - 8)
            
            current_y += total_block_height + row_spacing

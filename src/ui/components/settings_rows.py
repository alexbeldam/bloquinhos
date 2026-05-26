from typing import Optional

import pygame

from settings import SETTINGS


def draw_option_row(
    surface: pygame.Surface,
    row_rect: pygame.Rect,
    label: str,
    font: pygame.font.Font,
    *,
    is_hovered: bool = False,
    is_selected: bool = False,
    label_left_padding: int = 16,
    border_radius: int = 10,
    normal_bg: tuple[int, int, int] = SETTINGS.UI_THEME.SETTINGS_ROW_BG,
    hover_bg: tuple[int, int, int] = SETTINGS.UI_THEME.SETTINGS_ROW_BG_HOVER,
    selected_bg: Optional[tuple[int, int, int]] = SETTINGS.UI_THEME.SETTINGS_ROW_BG_SELECTED,
    text_color: tuple[int, int, int] = SETTINGS.UI_THEME.TEXT_PRIMARY,
) -> None:
    if is_selected and selected_bg is not None:
        bg_color = selected_bg
    elif is_hovered:
        bg_color = hover_bg
    else:
        bg_color = normal_bg

    pygame.draw.rect(surface, bg_color, row_rect, border_radius=border_radius)

    label_surface = font.render(label, True, text_color)
    label_rect = label_surface.get_rect(midleft=(row_rect.left + label_left_padding, row_rect.centery))
    surface.blit(label_surface, label_rect)


def draw_row_icon_right(
    surface: pygame.Surface,
    row_rect: pygame.Rect,
    icon: Optional[pygame.Surface],
    *,
    icon_size: int = 28,
    right_padding: int = 16,
    alpha: Optional[int] = None,
) -> None:
    if icon is None:
        return

    icon_scaled = pygame.transform.scale(icon, (icon_size, icon_size))
    if alpha is not None:
        icon_scaled.set_alpha(alpha)
    icon_rect = icon_scaled.get_rect(midright=(row_rect.right - right_padding, row_rect.centery))
    surface.blit(icon_scaled, icon_rect)


def draw_row_value_right(
    surface: pygame.Surface,
    row_rect: pygame.Rect,
    value_text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    *,
    right_padding: int = 16,
) -> None:
    value_surface = font.render(value_text, True, color)
    value_rect = value_surface.get_rect(midright=(row_rect.right - right_padding, row_rect.centery))
    surface.blit(value_surface, value_rect)
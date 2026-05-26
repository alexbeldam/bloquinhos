from typing import TYPE_CHECKING, Literal, Optional

import pygame

from settings import SETTINGS

if TYPE_CHECKING:
    from ui.assets import AssetManager


def draw_centered_text(
    surface: pygame.Surface,
    text: str,
    size: int,
    color: tuple[int, int, int],
    center: tuple[int, int],
    assets: "AssetManager",
) -> None:
    rendered = assets.get_font(size).render(text, True, color)
    surface.blit(rendered, rendered.get_rect(center=center))


def draw_tab_background_and_title(
    surface: pygame.Surface,
    rect: pygame.Rect,
    title: str,
    assets: "AssetManager",
    content_padding: int,
) -> tuple[int, int, int]:
    pygame.draw.rect(surface, SETTINGS.UI_THEME.SETTINGS_CONTENT_BG, rect)

    title_y = rect.y + content_padding + 12
    content_center_x = rect.x + rect.width // 2
    draw_centered_text(
        surface,
        title,
        SETTINGS.UI_TYPOGRAPHY.TITLE,
        SETTINGS.UI_THEME.CYAN,
        (content_center_x, title_y),
        assets,
    )

    return title_y, content_center_x, title_y + 48


def draw_wrapped_text(
    surface: pygame.Surface,
    text: str,
    font_size: int,
    color: tuple[int, int, int],
    max_width: int,
    line_spacing: int,
    assets: "AssetManager",
    *,
    x: int,
    y: int,
    align: Literal["left", "center"] = "left",
) -> int:
    font = assets.get_font(font_size)
    words = text.split()
    lines: list[str] = []
    current_line: list[str] = []

    for word in words:
        test_line = " ".join(current_line + [word])
        if font.size(test_line)[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    if align == "left":
        current_y = y
        for line in lines:
            rendered = font.render(line, True, color)
            surface.blit(rendered, (x, current_y))
            current_y += rendered.get_height() + line_spacing
        return current_y

    total_height = len(lines) * (font.get_height() + line_spacing) - line_spacing if lines else 0
    start_y = y - total_height // 2
    for index, line in enumerate(lines):
        rendered = font.render(line, True, color)
        line_y = start_y + index * (font.get_height() + line_spacing)
        surface.blit(rendered, rendered.get_rect(center=(x, line_y)))
    return start_y + total_height


def bottom_action_y(
    rect: pygame.Rect,
    content_padding: int,
    *,
    action_height: int,
    bottom_gap: int = 16,
    reserve_space: int = 0,
) -> int:
    return rect.y + rect.height - content_padding - action_height - bottom_gap - reserve_space
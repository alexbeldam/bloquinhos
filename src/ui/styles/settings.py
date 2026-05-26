from dataclasses import dataclass

from settings import Color


@dataclass(frozen=True)
class SettingsStyle:
    SCREEN_BG: Color = (20, 24, 36)
    SIDEBAR_BG: Color = (24, 28, 42)
    DIVIDER: Color = (50, 56, 78)
    TAB_BG: Color = (29, 34, 48)
    TAB_BG_HOVER: Color = (40, 45, 64)
    TAB_BG_ACTIVE: Color = (48, 40, 66)
    RESET_BG: Color = (64, 44, 48)
    RESET_BORDER: Color = (96, 68, 74)
    RESET_BG_HOVER: Color = (74, 48, 52)
    RESET_BORDER_HOVER: Color = (112, 74, 80)
    RESET_BG_ARMED: Color = (94, 52, 52)
    RESET_BORDER_ARMED: Color = (130, 74, 74)
    TOOLTIP_BG: Color = (35, 39, 50)
    CONTENT_BG: Color = (33, 39, 58)
    SECTION_RESET_BG: Color = (50, 50, 64)
    SECTION_RESET_BG_HOVER: Color = (58, 58, 72)
    SECTION_RESET_BORDER: Color = (76, 76, 92)
    SECTION_RESET_BORDER_HOVER: Color = (90, 90, 108)
    DROPDOWN_BG: Color = (43, 50, 70)
    DROPDOWN_BORDER: Color = (60, 66, 85)
    DROPDOWN_OPTION_BG_SELECTED: Color = (60, 66, 85)
    DROPDOWN_OPTION_BG_HOVER: Color = (70, 76, 95)
    DROPDOWN_OPTION_BG: Color = (50, 56, 75)
    SLIDER_BG: Color = (50, 55, 70)
    SLIDER_MUTED: Color = (100, 100, 100)
    ROW_BG: Color = (34, 40, 57)
    ROW_BG_HOVER: Color = (43, 50, 70)
    ROW_BG_SELECTED: Color = (50, 56, 75)


SETTINGS_STYLE = SettingsStyle()

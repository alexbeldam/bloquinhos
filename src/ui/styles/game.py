from dataclasses import dataclass


@dataclass(frozen=True)
class GameStyle:
    SIDEBAR_LEFT_OFFSET: int = 24
    SIDEBAR_CENTER_X: int = 76
    HOLD_TITLE_Y: int = 40
    NEXT_TITLE_Y: int = 200
    SCORE_TITLE_Y: int = 350
    SCORE_VALUE_Y: int = 385
    LEVEL_TITLE_Y: int = 450
    LEVEL_VALUE_Y: int = 485
    LINES_TITLE_Y: int = 540
    LINES_VALUE_Y: int = 575
    PREVIEW_BOX_TOP_OFFSET: int = 24
    PREVIEW_PADDING: int = 6


GAME_STYLE = GameStyle()

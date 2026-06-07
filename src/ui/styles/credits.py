from dataclasses import dataclass


@dataclass(frozen=True)
class CreditsStyle:
    CONTENT_PADDING: int = 32
    ROW_SPACING: int = 24
    MIN_LABEL_VALUE_GAP: int = 24
    LABEL_WIDTH_RATIO: float = 0.40
    LINE_SPACING: int = 2


CREDITS_STYLE = CreditsStyle()

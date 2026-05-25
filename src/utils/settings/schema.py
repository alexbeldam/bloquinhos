from __future__ import annotations

import copy
from dataclasses import dataclass
from enum import Enum
from typing import Any

import pygame

from .serialization import key_name_to_code


class SettingType(str, Enum):
    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    ENUM = "enum"


@dataclass(frozen=True)
class SettingField:
    setting_type: SettingType
    default: Any
    minimum: float | int | None = None
    maximum: float | int | None = None
    enum_values: tuple[str, ...] | None = None


SchemaNode = dict[str, "SchemaNode | SettingField"]


def build_schema() -> SchemaNode:
    rotate_key = key_name_to_code("up") or pygame.K_UP
    left_key = key_name_to_code("left") or pygame.K_LEFT
    right_key = key_name_to_code("right") or pygame.K_RIGHT
    soft_drop_key = key_name_to_code("down") or pygame.K_DOWN
    hard_drop_key = key_name_to_code("space") or pygame.K_SPACE
    hold_key = key_name_to_code("c") or pygame.K_c
    pause_key = key_name_to_code("escape") or pygame.K_ESCAPE

    return {
        "audio": {
            "master": {
                "volume": SettingField(SettingType.FLOAT, 0.7, minimum=0.0, maximum=1.0),
                "muted": SettingField(SettingType.BOOL, False),
            },
            "sfx": {
                "volume": SettingField(SettingType.FLOAT, 0.8, minimum=0.0, maximum=1.0),
                "muted": SettingField(SettingType.BOOL, False),
            },
            "music": {
                "volume": SettingField(SettingType.FLOAT, 0.7, minimum=0.0, maximum=1.0),
                "muted": SettingField(SettingType.BOOL, False),
            },
        },
        "graphics": {
            "draw_grid": SettingField(SettingType.BOOL, True),
            "draw_ghost": SettingField(SettingType.BOOL, True),
            "animations": SettingField(SettingType.BOOL, True),
        },
        "localization": {
            "language": SettingField(SettingType.STRING, "en"),
            "region": SettingField(SettingType.STRING, "US"),
        },
        "network": {
            "start_offline": SettingField(SettingType.BOOL, False),
            "reconnect_policy": SettingField(
                SettingType.ENUM,
                "auto",
                enum_values=("auto", "manual", "always"),
            ),
        },
        "controls": {
            "rotate": SettingField(SettingType.INT, rotate_key),
            "left": SettingField(SettingType.INT, left_key),
            "right": SettingField(SettingType.INT, right_key),
            "soft_drop": SettingField(SettingType.INT, soft_drop_key),
            "hard_drop": SettingField(SettingType.INT, hard_drop_key),
            "hold": SettingField(SettingType.INT, hold_key),
            "pause": SettingField(SettingType.INT, pause_key),
        },
    }


def build_defaults(schema: SchemaNode) -> dict[str, Any]:
    defaults: dict[str, Any] = {}
    for key, value in schema.items():
        if isinstance(value, SettingField):
            defaults[key] = copy.deepcopy(value.default)
        else:
            defaults[key] = build_defaults(value)
    return defaults

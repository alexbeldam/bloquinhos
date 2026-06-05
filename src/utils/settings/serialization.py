from __future__ import annotations

import copy
from typing import Any

import pygame

from utils.localization import detect_system_locale, normalize_locale_code, resolve_preferred_locale


def key_name_to_code(name: str) -> int | None:
    try:
        return pygame.key.key_code(name.strip().lower())
    except (TypeError, ValueError):
        return None


def key_code_to_name(key_code: int) -> str | int:
    try:
        key_name = pygame.key.name(key_code)
    except (TypeError, ValueError):
        return key_code

    if key_name:
        return key_name
    return key_code


def deserialize_overrides(data: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(data)
    _migrate_localization_tree(result)
    controls = result.get("controls")
    if not isinstance(controls, dict):
        return result

    for action, raw_value in list(controls.items()):
        if isinstance(raw_value, str):
            key_code = key_name_to_code(raw_value)
            controls[action] = key_code if key_code is not None else raw_value

    return result


def serialize_tree_for_disk(data: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(data)
    controls = result.get("controls")
    if not isinstance(controls, dict):
        return result

    for action, raw_value in list(controls.items()):
        if isinstance(raw_value, int):
            controls[action] = key_code_to_name(raw_value)

    return result


def _migrate_localization_tree(data: dict[str, Any]) -> None:
    localization = data.get("localization")
    if not isinstance(localization, dict):
        return

    locale_value = localization.get("locale")
    normalized_locale = normalize_locale_code(locale_value)
    if normalized_locale is not None:
        localization["locale"] = resolve_preferred_locale(normalized_locale)
        localization.pop("language", None)
        localization.pop("region", None)
        return

    language = localization.get("language")
    region = localization.get("region")
    candidate = None
    if isinstance(language, str) and isinstance(region, str):
        candidate = normalize_locale_code(f"{language}-{region}")

    localization["locale"] = resolve_preferred_locale(candidate or detect_system_locale())
    localization.pop("language", None)
    localization.pop("region", None)

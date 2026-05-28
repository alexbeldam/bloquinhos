from __future__ import annotations

import copy
from typing import Any


def diff_tree(defaults: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    diff: dict[str, Any] = {}

    for key, current_value in current.items():
        default_value = defaults.get(key)

        if isinstance(current_value, dict) and isinstance(default_value, dict):
            nested_diff = diff_tree(default_value, current_value)
            if nested_diff:
                diff[key] = nested_diff
            continue

        if current_value != default_value:
            diff[key] = copy.deepcopy(current_value)

    return diff


def merge_deep(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)

    for key, override_value in overrides.items():
        base_value = merged.get(key)
        if isinstance(base_value, dict) and isinstance(override_value, dict):
            merged[key] = merge_deep(base_value, override_value)
        else:
            merged[key] = copy.deepcopy(override_value)

    return merged

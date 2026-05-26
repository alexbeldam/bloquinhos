from __future__ import annotations

import copy
from typing import Any, Callable

from .schema import SchemaNode, SettingField, SettingType


WarnInvalid = Callable[[str, Any, str], None]


def parse_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    return None


def apply_numeric_constraints(value: int | float, field: SettingField) -> int | float:
    constrained = value
    if field.minimum is not None:
        constrained = max(field.minimum, constrained)
    if field.maximum is not None:
        constrained = min(field.maximum, constrained)
    return constrained


def validate_field(value: Any, field: SettingField, path: str, warn_invalid: WarnInvalid) -> Any:
    default = copy.deepcopy(field.default)

    if field.setting_type == SettingType.BOOL:
        parsed = parse_bool(value)
        if parsed is None:
            warn_invalid(path, value, field.setting_type.value)
            return default
        return parsed

    if field.setting_type == SettingType.INT:
        if isinstance(value, bool):
            warn_invalid(path, value, field.setting_type.value)
            return default
        if isinstance(value, (int, float)):
            parsed_int = int(value)
            return apply_numeric_constraints(parsed_int, field)
        warn_invalid(path, value, field.setting_type.value)
        return default

    if field.setting_type == SettingType.FLOAT:
        if isinstance(value, bool):
            warn_invalid(path, value, field.setting_type.value)
            return default
        if isinstance(value, (int, float)):
            parsed_float = float(value)
            constrained = apply_numeric_constraints(parsed_float, field)
            if field.precision is not None:
                constrained = round(constrained, field.precision)
            return constrained
        warn_invalid(path, value, field.setting_type.value)
        return default

    if field.setting_type == SettingType.STRING:
        if isinstance(value, str):
            return value
        warn_invalid(path, value, field.setting_type.value)
        return default

    if field.setting_type == SettingType.ENUM:
        if isinstance(value, str) and field.enum_values and value in field.enum_values:
            return value
        warn_invalid(path, value, f"enum{field.enum_values}")
        return default

    warn_invalid(path, value, field.setting_type.value)
    return default


def validate_tree(
    candidate: dict[str, Any],
    schema: SchemaNode,
    warn_invalid: WarnInvalid,
    prefix: str = "",
) -> dict[str, Any]:
    validated: dict[str, Any] = {}

    for key, schema_value in schema.items():
        current_path = f"{prefix}.{key}" if prefix else key

        if isinstance(schema_value, SettingField):
            raw_value = candidate.get(key, schema_value.default)
            validated[key] = validate_field(raw_value, schema_value, current_path, warn_invalid)
            continue

        nested_candidate = candidate.get(key)
        if not isinstance(nested_candidate, dict):
            if key in candidate:
                warn_invalid(current_path, nested_candidate, "object")
            nested_candidate = {}
        validated[key] = validate_tree(nested_candidate, schema_value, warn_invalid, current_path)

    return validated

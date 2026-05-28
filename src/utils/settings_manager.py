from __future__ import annotations

import copy
import json
import threading
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable

from utils.path_manager import PathManager
from utils.settings import (
    SettingField,
    build_defaults,
    build_schema,
    deserialize_overrides,
    diff_tree,
    merge_deep,
    serialize_tree_for_disk,
    validate_field,
    validate_tree,
)


@dataclass(frozen=True)
class UserSettings:
    values: dict[str, Any] = field(default_factory=dict)


SchemaNode = dict[str, "SchemaNode | SettingField"]
SettingsObserver = Callable[[str, Any, Any], None]


class SettingsManager:
    DEFAULT_SAVE_DEBOUNCE_SECONDS = 0.2

    def __init__(self) -> None:
        self._schema: SchemaNode = build_schema()
        self._defaults: MappingProxyType[str, Any] = self._freeze_mapping(build_defaults(self._schema))
        self._exact_subscribers: dict[str, list[SettingsObserver]] = {}
        self._wildcard_subscribers: list[tuple[str, SettingsObserver]] = []
        self._runtime_tree: dict[str, Any] = {}
        self._dirty: bool = False
        self._debounce_seconds: float = self.DEFAULT_SAVE_DEBOUNCE_SECONDS
        self._pending_save_timer: threading.Timer | None = None
        self._save_lock = threading.RLock()
        self.load()

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    @staticmethod
    def normalize_path(path: str) -> str:
        if not path:
            raise ValueError("Settings path cannot be empty")

        normalized = path.strip().replace(" ", "")
        while ".." in normalized:
            normalized = normalized.replace("..", ".")

        normalized = normalized.strip(".")
        if not normalized:
            raise ValueError("Settings path cannot be empty")
        return normalized

    def list_paths(self) -> tuple[str, ...]:
        paths: list[str] = []

        def walk(node: SchemaNode, prefix: str = "") -> None:
            for key, value in node.items():
                current = f"{prefix}.{key}" if prefix else key
                if isinstance(value, SettingField):
                    paths.append(current)
                else:
                    walk(value, current)

        walk(self._schema)
        return tuple(sorted(paths))

    def get_schema(self) -> MappingProxyType[str, Any]:
        return self._freeze_mapping(self._schema)

    def get_default_tree(self) -> dict[str, Any]:
        return self._thaw_mapping(self._defaults)

    def get_default_value(self, path: str) -> Any:
        normalized = self.normalize_path(path)
        value: Any = self._defaults
        for key in normalized.split("."):
            if not isinstance(value, MappingProxyType) or key not in value:
                raise KeyError(f"Unknown setting path: {normalized}")
            value = value[key]
        if isinstance(value, MappingProxyType):
            raise KeyError(f"Path is not a leaf setting: {normalized}")
        return copy.deepcopy(value)

    def get_field(self, path: str) -> SettingField:
        normalized = self.normalize_path(path)
        node: Any = self._schema
        for key in normalized.split("."):
            if not isinstance(node, dict) or key not in node:
                raise KeyError(f"Unknown setting path: {normalized}")
            node = node[key]
        if not isinstance(node, SettingField):
            raise KeyError(f"Path is not a leaf setting: {normalized}")
        return node

    def reset_to_defaults(self) -> UserSettings:
        self.reset_subtree()
        return self.get_settings()

    def reset_key(self, path: str) -> bool:
        normalized = self.normalize_path(path)
        default_value = self.get_default_value(normalized)
        return self._set_value(normalized, default_value, schedule_save=True)

    def reset_subtree(self, path: str | None = None) -> int:
        normalized = "" if path is None else path.strip()

        if not normalized:
            leaf_paths = self.list_paths()
        else:
            normalized = self.normalize_path(normalized)
            schema_node = self._get_schema_node(normalized)
            if isinstance(schema_node, SettingField):
                return 1 if self.reset_key(normalized) else 0
            leaf_paths = self._list_leaf_paths(schema_node, normalized)

        changed = 0
        for leaf_path in leaf_paths:
            default_value = self.get_default_value(leaf_path)
            if self._set_value(leaf_path, default_value, schedule_save=False):
                changed += 1

        if changed > 0:
            self.schedule_save()

        return changed

    def validate_settings(self, settings: UserSettings) -> UserSettings:
        source_tree = self._user_settings_to_tree(settings)
        validated_tree = self._validate_tree(source_tree, self._schema)
        return self._tree_to_user_settings(validated_tree)

    def get_settings(self) -> UserSettings:
        return self._tree_to_user_settings(copy.deepcopy(self._runtime_tree))

    def get(self, path: str) -> Any:
        normalized = self.normalize_path(path)
        value = self._get_tree_value(self._runtime_tree, normalized)
        return copy.deepcopy(value)

    def get_float(self, path: str) -> float:
        value = self.get(path)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"Setting '{path}' is not a float")
        return float(value)

    def get_bool(self, path: str) -> bool:
        value = self.get(path)
        if not isinstance(value, bool):
            raise TypeError(f"Setting '{path}' is not a bool")
        return value

    def set(self, path: str, value: Any) -> bool:
        return self._set_value(path, value, schedule_save=True)

    def _set_value(self, path: str, value: Any, schedule_save: bool) -> bool:
        normalized = self.normalize_path(path)
        field = self.get_field(normalized)
        old_value = self._get_tree_value(self._runtime_tree, normalized)
        new_value = validate_field(value, field, normalized, self._warn_invalid)

        if old_value == new_value:
            return False

        self._set_tree_value(self._runtime_tree, normalized, new_value)
        self._dirty = True
        self._notify_subscribers(normalized, old_value, new_value)
        if schedule_save:
            self.schedule_save()
        return True

    def subscribe(self, key_pattern: str, callback: SettingsObserver) -> None:
        normalized_pattern = self.normalize_path(key_pattern)
        if "*" in normalized_pattern:
            self._wildcard_subscribers.append((normalized_pattern, callback))
            return

        self.get_field(normalized_pattern)
        self._exact_subscribers.setdefault(normalized_pattern, []).append(callback)

    def unsubscribe(self, key_pattern: str, callback: SettingsObserver) -> None:
        normalized_pattern = self.normalize_path(key_pattern)
        if "*" in normalized_pattern:
            self._wildcard_subscribers = [
                pair for pair in self._wildcard_subscribers
                if pair != (normalized_pattern, callback)
            ]
            return

        subscribers = self._exact_subscribers.get(normalized_pattern)
        if not subscribers:
            return
        self._exact_subscribers[normalized_pattern] = [fn for fn in subscribers if fn != callback]
        if not self._exact_subscribers[normalized_pattern]:
            del self._exact_subscribers[normalized_pattern]

    def get_settings_path(self) -> str:
        return PathManager.get_preferences_path()

    def load(self) -> UserSettings:
        defaults = self.get_default_tree()
        overrides = self._read_overrides_file()
        merged = merge_deep(defaults, overrides)
        validated = self._validate_tree(merged, self._schema)
        self._runtime_tree = copy.deepcopy(validated)
        self._dirty = False
        return self._tree_to_user_settings(validated)

    def save(self, settings: UserSettings) -> None:
        validated_tree = self._validate_tree(self._user_settings_to_tree(settings), self._schema)
        self._write_tree_to_disk(validated_tree)

    def save_runtime(self) -> None:
        with self._save_lock:
            validated_tree = self._validate_tree(copy.deepcopy(self._runtime_tree), self._schema)
            self._write_tree_to_disk(validated_tree)

    def schedule_save(self, delay_seconds: float | None = None) -> None:
        with self._save_lock:
            wait_time = self._debounce_seconds if delay_seconds is None else max(0.0, delay_seconds)
            if self._pending_save_timer is not None:
                self._pending_save_timer.cancel()

            self._pending_save_timer = threading.Timer(wait_time, self._save_timer_callback)
            self._pending_save_timer.daemon = True
            self._pending_save_timer.start()

    def flush(self) -> None:
        with self._save_lock:
            if self._pending_save_timer is not None:
                self._pending_save_timer.cancel()
                self._pending_save_timer = None

            if self._dirty:
                self.save_runtime()

    def save_on_exit(self) -> None:
        self.flush()

    def set_save_debounce(self, seconds: float) -> None:
        self._debounce_seconds = max(0.0, seconds)

    @classmethod
    def _freeze_mapping(cls, data: dict[str, Any]) -> MappingProxyType[str, Any]:
        frozen: dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, dict):
                frozen[key] = cls._freeze_mapping(value)
            elif isinstance(value, list):
                frozen[key] = tuple(value)
            elif isinstance(value, set):
                frozen[key] = frozenset(value)
            else:
                frozen[key] = value
        return MappingProxyType(frozen)

    @staticmethod
    def _thaw_mapping(data: MappingProxyType[str, Any] | dict[str, Any]) -> dict[str, Any]:
        thawed: dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, MappingProxyType):
                thawed[key] = SettingsManager._thaw_mapping(value)
            elif isinstance(value, dict):
                thawed[key] = SettingsManager._thaw_mapping(value)
            elif isinstance(value, tuple):
                thawed[key] = list(value)
            elif isinstance(value, frozenset):
                thawed[key] = set(value)
            else:
                thawed[key] = copy.deepcopy(value)
        return thawed

    def _validate_tree(self, candidate: dict[str, Any], schema: SchemaNode, prefix: str = "") -> dict[str, Any]:
        return validate_tree(candidate, schema, self._warn_invalid, prefix)

    @staticmethod
    def _user_settings_to_tree(settings: UserSettings) -> dict[str, Any]:
        return copy.deepcopy(settings.values)

    @staticmethod
    def _tree_to_user_settings(tree: dict[str, Any]) -> UserSettings:
        return UserSettings(values=copy.deepcopy(tree))

    @staticmethod
    def _warn_invalid(path: str, value: Any, expected: str) -> None:
        from utils.logger import log

        log.warning(f"Invalid settings value for '{path}': {value!r} (expected {expected})")

    def _read_overrides_file(self) -> dict[str, Any]:
        from utils.logger import log

        settings_path = self._get_settings_file_path()

        if not settings_path.exists():
            return {}

        try:
            with settings_path.open("r", encoding="utf-8") as stream:
                loaded = json.load(stream)
        except json.JSONDecodeError as exc:
            log.error(f"Invalid settings JSON in '{settings_path}': {exc}")
            return {}
        except OSError as exc:
            log.error(f"Could not read settings file '{settings_path}': {exc}")
            return {}

        if not isinstance(loaded, dict):
            log.warning("Settings file root must be an object; using defaults")
            return {}

        return self._deserialize_overrides(loaded)

    def _get_settings_file_path(self) -> Path:
        return Path(self.get_settings_path())

    def _get_schema_node(self, path: str) -> SchemaNode | SettingField:
        normalized = self.normalize_path(path)
        node: Any = self._schema

        for key in normalized.split("."):
            if not isinstance(node, dict) or key not in node:
                raise KeyError(f"Unknown setting path: {normalized}")
            node = node[key]

        return node

    def _list_leaf_paths(self, node: SchemaNode, prefix: str) -> tuple[str, ...]:
        paths: list[str] = []

        def walk(current_node: SchemaNode, current_prefix: str) -> None:
            for key, value in current_node.items():
                path = f"{current_prefix}.{key}" if current_prefix else key
                if isinstance(value, SettingField):
                    paths.append(path)
                else:
                    walk(value, path)

        walk(node, prefix)
        return tuple(paths)

    @staticmethod
    def _get_tree_value(tree: dict[str, Any], path: str) -> Any:
        value: Any = tree
        for key in path.split("."):
            if not isinstance(value, dict) or key not in value:
                raise KeyError(f"Unknown setting path: {path}")
            value = value[key]
        return value

    @staticmethod
    def _set_tree_value(tree: dict[str, Any], path: str, value: Any) -> None:
        parts = path.split(".")
        node = tree

        for key in parts[:-1]:
            candidate = node.get(key)
            if not isinstance(candidate, dict):
                candidate = {}
                node[key] = candidate
            node = candidate

        node[parts[-1]] = value

    def _notify_subscribers(self, path: str, old_value: Any, new_value: Any) -> None:
        for callback in self._exact_subscribers.get(path, []):
            callback(path, old_value, new_value)

        for pattern, callback in self._wildcard_subscribers:
            if fnmatchcase(path, pattern):
                callback(path, old_value, new_value)

    def _save_timer_callback(self) -> None:
        with self._save_lock:
            self._pending_save_timer = None
            if self._dirty:
                self.save_runtime()

    def _write_tree_to_disk(self, validated_tree: dict[str, Any]) -> None:
        from utils.logger import log

        target_path = self._get_settings_file_path()
        payload_internal = diff_tree(self.get_default_tree(), validated_tree)
        payload = self._serialize_tree_for_disk(payload_internal)

        temp_name = f".{target_path.name}.tmp"
        temp_path = target_path.with_name(temp_name)

        try:
            with temp_path.open("w", encoding="utf-8") as stream:
                json.dump(payload, stream, indent=2, ensure_ascii=True, sort_keys=True)
                stream.write("\n")

            temp_path.replace(target_path)
            self._dirty = False
        except OSError as exc:
            log.error(f"Could not write settings file '{target_path}': {exc}")
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except OSError:
                pass

    def _deserialize_overrides(self, data: dict[str, Any]) -> dict[str, Any]:
        return deserialize_overrides(data)

    def _serialize_tree_for_disk(self, data: dict[str, Any]) -> dict[str, Any]:
        return serialize_tree_for_disk(data)

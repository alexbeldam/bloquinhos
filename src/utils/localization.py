from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Any, Callable, Iterable

import i18n

from utils.path_manager import PathManager


DEFAULT_LOCALE = "en-US"
_LOCALE_PATTERN = re.compile(r"^[a-z]{2}-([A-Z]{2}|[0-9]{3})$")

@dataclass(frozen=True)
class LocaleMeta:
    display_name: str
    decimal_separator: str
    thousands_separator: str

class NumericFormatter:
    def __init__(self, locale_meta_provider: Callable[[], LocaleMeta]) -> None:
        self._locale_meta_provider = locale_meta_provider

    def format_int(self, value: int | float) -> str:
        integer_value = int(value)
        meta = self._locale_meta_provider()
        return self._apply_separators(f"{integer_value:,d}", meta)

    def format_float(self, value: float, precision: int = 2) -> str:
        meta = self._locale_meta_provider()
        return self._apply_separators(f"{value:,.{precision}f}", meta)

    def format_percent(self, value: float, precision: int = 0, is_fraction: bool = True) -> str:
        percentage = value * 100.0 if is_fraction else value
        return f"{self.format_float(percentage, precision)}%"

    @staticmethod
    def _apply_separators(value: str, meta: LocaleMeta) -> str:
        return (
            value.replace(",", "__THOUSANDS__")
            .replace(".", "__DECIMAL__")
            .replace("__THOUSANDS__", meta.thousands_separator)
            .replace("__DECIMAL__", meta.decimal_separator)
        )


class LocalizationManager:
    def __init__(self) -> None:
        self._available_locales: dict[str, LocaleMeta] = {
            DEFAULT_LOCALE: LocaleMeta(
                display_name="English",
                decimal_separator=".",
                thousands_separator=",",
            )
        }
        self._active_locale = DEFAULT_LOCALE
        self._formatter = NumericFormatter(self.get_locale_meta)
        self.refresh_locales()
        self._configure_i18n()
        self.set_locale(DEFAULT_LOCALE)

    @property
    def formatter(self) -> NumericFormatter:
        return self._formatter

    def refresh_locales(self) -> None:
        from utils.logger import log

        locales_path = Path(PathManager.get_locales_path())
        discovered: dict[str, LocaleMeta] = {}

        if locales_path.exists() and locales_path.is_dir():
            for file_path in sorted(locales_path.glob("*.json")):
                locale_code = file_path.stem
                if not self.is_valid_locale(locale_code):
                    log.warning(f"Ignoring locale file with invalid name: {file_path.name}")
                    continue

                try:
                    with file_path.open("r", encoding="utf-8") as stream:
                        content = json.load(stream)
                except (OSError, json.JSONDecodeError) as exc:
                    log.warning(f"Ignoring malformed locale file '{file_path.name}': {exc}")
                    continue

                if not isinstance(content, dict):
                    log.warning(f"Ignoring locale file '{file_path.name}': root must be an object")
                    continue

                meta = content.get("meta")
                if not isinstance(meta, dict):
                    log.warning(f"Ignoring locale file '{file_path.name}': missing meta object")
                    continue

                display_name = meta.get("display_name")
                if not isinstance(display_name, str) or not display_name.strip():
                    log.warning(f"Ignoring locale file '{file_path.name}': missing meta.display_name")
                    continue

                separators = meta.get("separators")
                if not isinstance(separators, dict):
                    log.warning(f"Ignoring locale file '{file_path.name}': missing meta.separators")
                    continue

                decimal_separator = separators.get("decimal")
                thousands_separator = separators.get("thousands")
                if not isinstance(decimal_separator, str) or not isinstance(thousands_separator, str):
                    log.warning(f"Ignoring locale file '{file_path.name}': invalid meta.separators")
                    continue

                discovered[locale_code] = LocaleMeta(
                    display_name=display_name.strip(),
                    decimal_separator=decimal_separator,
                    thousands_separator=thousands_separator
                )
        else:
            log.warning(f"Locale directory not found: {locales_path}")

        if DEFAULT_LOCALE not in discovered:
            discovered[DEFAULT_LOCALE] = LocaleMeta(
                display_name="English",
                decimal_separator=".",
                thousands_separator=","
            )

        self._available_locales = dict(
            sorted(discovered.items(), key=lambda item: item[1].display_name.casefold())
        )

    def available_locale_codes(self) -> tuple[str, ...]:
        return tuple(self._available_locales.keys())

    def available_locales(self) -> tuple[tuple[str, LocaleMeta], ...]:
        return tuple((code, self._available_locales[code]) for code in self.available_locale_codes())

    def display_name_for(self, locale_code: str) -> str:
        locale_meta = self._available_locales.get(locale_code)
        if locale_meta is None:
            return locale_code
        return locale_meta.display_name

    def get_locale_meta(self) -> LocaleMeta:
        return self._available_locales.get(self._active_locale, self._available_locales[DEFAULT_LOCALE])

    def get_locale(self) -> str:
        return self._active_locale

    def set_locale(self, locale_code: str) -> str:
        normalized = self.resolve_locale(locale_code)

        self._active_locale = normalized
        i18n.set("locale", normalized)
        return normalized

    def resolve_locale(self, locale_code: str | None) -> str:
        return resolve_preferred_locale(locale_code, self._available_locales.keys())

    def translate(self, key: str, **kwargs: Any) -> str:
        fallback_chain = self._get_fallback_chain(self._active_locale)
        
        for locale_code in fallback_chain:
            text = self._translate_from_locale(locale_code, key, **kwargs)
            if text is not None:
                return text
        
        return key

    @staticmethod
    def is_valid_locale(locale_code: str) -> bool:
        return bool(_LOCALE_PATTERN.fullmatch(locale_code))

    def _get_fallback_chain(self, locale_code: str) -> list[str]:
        chain = [locale_code]
        
        language = locale_code.split("-")[0]
        
        for available_code in self._available_locales:
            if available_code != locale_code and available_code.startswith(f"{language}-"):
                chain.append(available_code)
        
        if DEFAULT_LOCALE not in chain:
            chain.append(DEFAULT_LOCALE)
        
        return chain

    def _configure_i18n(self) -> None:
        locales_path = PathManager.get_locales_path()
        if locales_path not in i18n.load_path:
            i18n.load_path.append(locales_path)
        i18n.set("file_format", "json")
        i18n.set("filename_format", "{locale}.{format}")
        i18n.set("fallback", DEFAULT_LOCALE)
        i18n.set("skip_locale_root_data", True)
        i18n.set("enable_memoization", False)

    @staticmethod
    def _translate_from_locale(locale_code: str, key: str, **kwargs: Any) -> str | None:
        try:
            translated = i18n.t(key, locale=locale_code, **kwargs)
        except Exception:
            return None

        if isinstance(translated, str) and translated != key:
            return translated

        return None


def normalize_locale_code(locale_code: str | None) -> str | None:
    if not isinstance(locale_code, str):
        return None

    cleaned = locale_code.strip().replace("_", "-")
    parts = cleaned.split("-", maxsplit=1)
    if len(parts) != 2:
        return None

    language, region = parts[0].lower(), parts[1].upper()
    normalized = f"{language}-{region}"
    if LocalizationManager.is_valid_locale(normalized):
        return normalized

    return None


def _extract_language(locale_code: str | None) -> str | None:
    if not isinstance(locale_code, str):
        return None

    cleaned = locale_code.strip().replace("_", "-")
    if not cleaned:
        return None

    language = cleaned.split("-", maxsplit=1)[0].lower()
    if len(language) == 2 and language.isalpha():
        return language

    return None


def detect_system_locale() -> str | None:
    import locale
    
    try:
        system_locale = locale.getlocale()
        if system_locale:
            return normalize_locale_code(system_locale[0])
    except Exception:
        pass
    
    return None


def discover_available_locale_codes() -> tuple[str, ...]:
    locales_path = Path(PathManager.get_locales_path())
    codes: set[str] = set()

    if locales_path.exists() and locales_path.is_dir():
        for file_path in locales_path.glob("*.json"):
            locale_code = file_path.stem
            if LocalizationManager.is_valid_locale(locale_code):
                codes.add(locale_code)

    codes.add(DEFAULT_LOCALE)
    return tuple(sorted(codes))


def resolve_preferred_locale(
    locale_code: str | None,
    available_locale_codes: Iterable[str] | None = None,
) -> str:
    available = tuple(available_locale_codes) if available_locale_codes is not None else discover_available_locale_codes()
    available_set = set(available)
    available_set.add(DEFAULT_LOCALE)

    normalized = normalize_locale_code(locale_code)
    if normalized and normalized in available_set:
        return normalized

    language = _extract_language(locale_code)
    if language:
        for code in available:
            if code in available_set and code.startswith(f"{language}-"):
                return code
        for code in sorted(available_set):
            if code.startswith(f"{language}-"):
                return code

    return DEFAULT_LOCALE


_manager: LocalizationManager | None = None


def set_localization_manager(manager: LocalizationManager) -> None:
    global _manager
    _manager = manager


def get_localization_manager() -> LocalizationManager | None:
    return _manager


def tr(key: str, **kwargs: Any) -> str:
    if _manager is None:
        return key
    return _manager.translate(key, **kwargs)


def set_locale(locale_code: str) -> str:
    if _manager is None:
        return DEFAULT_LOCALE
    return _manager.set_locale(locale_code)


def get_locale() -> str:
    if _manager is None:
        return DEFAULT_LOCALE
    return _manager.get_locale()


def get_available_locales() -> tuple[tuple[str, LocaleMeta], ...]:
    if _manager is None:
        return ((
            DEFAULT_LOCALE,
            LocaleMeta(
                display_name="English",
                decimal_separator=".",
                thousands_separator=",",
            ),
        ),)
    return _manager.available_locales()


def format_int(value: int | float) -> str:
    if _manager is None:
        return str(int(value))
    return _manager.formatter.format_int(value)


def format_float(value: float, precision: int = 2) -> str:
    if _manager is None:
        return f"{float(value):.{precision}f}"
    return _manager.formatter.format_float(value, precision)


def format_percent(value: float, precision: int = 0, is_fraction: bool = True) -> str:
    if _manager is None:
        percentage = value * 100.0 if is_fraction else value
        return f"{percentage:.{precision}f}%"
    return _manager.formatter.format_percent(value, precision, is_fraction)

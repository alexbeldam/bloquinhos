"""
Utility module.

This module provides utility functions and classes for path management,
environment configuration, and logging.
"""

from .path_manager import PathManager
from .env_manager import load_env_vars, get_env
from .logger import log, update_log_level
from .localization import (
	DEFAULT_LOCALE,
	LocaleMeta,
	LocalizationManager,
	format_float,
	format_int,
	format_percent,
	get_available_locales,
	get_locale,
	get_localization_manager,
	set_locale,
	set_localization_manager,
	tr,
)
from .settings_manager import SettingsManager

__all__ = [
	'PathManager',
	'load_env_vars',
	'get_env',
	'log',
	'update_log_level',
	'DEFAULT_LOCALE',
	'LocaleMeta',
	'LocalizationManager',
	'format_float',
	'format_int',
	'format_percent',
	'get_available_locales',
	'get_locale',
	'get_localization_manager',
	'set_locale',
	'set_localization_manager',
	'tr',
	'SettingsManager',
]
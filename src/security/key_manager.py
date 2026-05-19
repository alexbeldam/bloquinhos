import os
import base64
import platform
from abc import ABC, abstractmethod
from typing import Optional

from utils.logger import log
from utils.path_manager import PathManager


class _KeyBackend(ABC):
    @abstractmethod
    def load(self) -> Optional[bytes]: ...

    @abstractmethod
    def store(self, key: bytes) -> bool: ...


class _WindowsBackend(_KeyBackend):
    def load(self) -> Optional[bytes]:
        try:
            import win32crypt
            key_path = PathManager.get_dpapi_key_path()
            if not os.path.exists(key_path):
                return None
            with open(key_path, "rb") as f:
                encrypted = f.read()
            key, _ = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)
            return key
        except Exception:
            log.warning("DPAPI key load failed", exc_info=True)
            return None

    def store(self, key: bytes) -> bool:
        try:
            import win32crypt
            encrypted = win32crypt.CryptProtectData(key, None, None, None, None, 0)
            key_path = PathManager.get_dpapi_key_path()
            with open(key_path, "wb") as f:
                f.write(encrypted)
            try:
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(key_path, 2)
            except Exception:
                log.debug("Could not set hidden attribute on key file")
            return True
        except Exception:
            log.warning("DPAPI key storage failed, using fallback", exc_info=True)
            return False


class _UnixBackend(_KeyBackend):
    def load(self) -> Optional[bytes]:
        try:
            import keyring
            from settings import SETTINGS
            value = keyring.get_password(SETTINGS.SECURITY.KEYRING_SERVICE, SETTINGS.SECURITY.KEYRING_ACCOUNT)
            return value.encode("utf-8") if value is not None else None
        except Exception:
            log.warning("Keyring load failed", exc_info=True)
            return None

    def store(self, key: bytes) -> bool:
        try:
            import keyring
            from settings import SETTINGS
            keyring.set_password(SETTINGS.SECURITY.KEYRING_SERVICE, SETTINGS.SECURITY.KEYRING_ACCOUNT, key.decode("utf-8"))
            return True
        except Exception:
            log.warning("Keyring storage failed, using fallback", exc_info=True)
            return False


class _NullBackend(_KeyBackend):
    def load(self) -> Optional[bytes]:
        return None

    def store(self, _key: bytes) -> bool:
        return False


class KeyManager:
    _BACKENDS: dict[str, type[_KeyBackend]] = {
        "windows": _WindowsBackend,
        "linux": _UnixBackend,
    }

    def __init__(self) -> None:
        backend_cls = self._BACKENDS.get(platform.system().lower(), _NullBackend)
        self._backend: _KeyBackend = backend_cls()

    def load_or_create_key(self) -> bytes:
        key = self._load_key()
        if key is not None:
            return key

        key = base64.urlsafe_b64encode(os.urandom(32))
        self._store_key(key)
        log.info("New encryption key generated")
        return key

    def _load_key(self) -> Optional[bytes]:
        key = self._backend.load()
        if key is not None:
            return key
        return self._load_key_fallback()

    def _store_key(self, key: bytes) -> None:
        if not self._backend.store(key):
            self._store_key_fallback(key)

    def _store_key_fallback(self, key: bytes) -> None:
        try:
            key_path = PathManager.get_fallback_key_path()
            with open(key_path, "wb") as f:
                f.write(key)
            os.chmod(key_path, 0o600)
            log.warning("Encryption key stored in local filesystem as fallback (not secure)")
        except Exception:
            log.error("Failed to persist encryption key", exc_info=True)

    def _load_key_fallback(self) -> Optional[bytes]:
        try:
            key_path = PathManager.get_fallback_key_path()
            if not os.path.exists(key_path):
                return None
            with open(key_path, "rb") as f:
                return f.read()
        except Exception:
            log.warning("Fallback key load failed", exc_info=True)
            return None

import os
import base64
import platform
from abc import ABC, abstractmethod
from typing import Optional

from cryptography.fernet import Fernet
from utils.logger import log
from utils.path_manager import PathManager


class _KeyBackend(ABC):
    @abstractmethod
    def load(self) -> Optional[bytes]: ...

    @abstractmethod
    def store(self, key: bytes) -> bool: ...

    @abstractmethod
    def secure_file(self, path: str) -> None: ...


class _WindowsBackend(_KeyBackend):
    def load(self) -> Optional[bytes]:
        try:
            import win32crypt

            key_path = PathManager.get_dpapi_key_path()
            if not os.path.exists(key_path):
                return None
            with open(key_path, "rb") as f:
                encrypted = f.read()
            _, key = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)
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
            self.secure_file(key_path)
            return True
        except Exception:
            log.warning("DPAPI key storage failed, using fallback", exc_info=True)
            return False

    def secure_file(self, path: str) -> None:
        try:
            import ctypes

            ctypes.windll.kernel32.SetFileAttributesW(path, 2)
        except Exception:
            log.warning("Could not set hidden attribute on key file", exc_info=True)


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

    def secure_file(self, path: str) -> None:
        os.chmod(path, 0o600)


class _NullBackend(_KeyBackend):
    def load(self) -> Optional[bytes]:
        return None

    def store(self, _key: bytes) -> bool:
        return False

    def secure_file(self, path: str) -> None:
        try:
            os.chmod(path, 0o600)
        except Exception:
            log.warning("Could not harden fallback key file permissions", exc_info=True)


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
        if not self._store_key(key):
            raise RuntimeError("Encryption key persistence failed")
        log.info("New encryption key generated")
        return key

    @staticmethod
    def _is_valid_fernet_key(key: bytes) -> bool:
        try:
            Fernet(key)
            return True
        except Exception:
            return False

    def _load_key(self) -> Optional[bytes]:
        key = self._backend.load()
        if key is not None:
            if self._is_valid_fernet_key(key):
                return key
            log.warning("Stored key is invalid, trying fallback")

        key = self._load_key_fallback()
        if key is not None:
            if self._is_valid_fernet_key(key):
                return key
            log.warning("Fallback key is invalid")

        return None

    def _store_key(self, key: bytes) -> bool:
        if self._backend.store(key):
            return True
        return self._store_key_fallback(key)

    def _store_key_fallback(self, key: bytes) -> bool:
        try:
            key_path = PathManager.get_fallback_key_path()
            with open(key_path, "wb") as f:
                f.write(key)
            self._backend.secure_file(key_path)
            log.warning("Encryption key stored in local filesystem as fallback (not secure)")
            return True
        except Exception:
            log.error("Failed to persist encryption key", exc_info=True)
            return False

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

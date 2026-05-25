import json
import os
import re
from dataclasses import dataclass
from typing import Callable, Optional, Protocol, TYPE_CHECKING

from settings import SETTINGS
from utils.logger import log
from utils.path_manager import PathManager
from .vault import Vault

if TYPE_CHECKING:
    from network.connection_manager import NetworkManager


USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,15}$")


class IdentityDAO(Protocol):
    def exists(self) -> bool: ...

    def load_name(self) -> Optional[str]: ...

    def save_name(self, name: str, pending_remote_validation: bool = False) -> None: ...

    def has_pending_remote_validation(self) -> bool: ...


class RemoteIdentityValidator(Protocol):
    def is_name_available(self, name: str) -> bool: ...


@dataclass(frozen=True)
class IdentityRecord:
    username: str
    pending_remote_validation: bool = False


class _EncryptedFileIdentityDAO:
    def __init__(self, vault: Optional[Vault] = None, save_path: Optional[str] = None) -> None:
        self._vault = vault or Vault()
        self._save_path = save_path or PathManager.get_user_save_path()

    def exists(self) -> bool:
        return os.path.exists(self._save_path)

    def load_name(self) -> Optional[str]:
        record = self._load_record()
        return record.username if record else None

    def save_name(self, name: str, pending_remote_validation: bool = False) -> None:
        record = {
            "username": name,
            "username_normalized": name.casefold(),
            "pending_remote_validation": pending_remote_validation,
        }
        encrypted = self._vault.encrypt(json.dumps(record))
        os.makedirs(os.path.dirname(self._save_path), exist_ok=True)
        with open(self._save_path, "wb") as file:
            file.write(encrypted)
        self._harden_file()

    def has_pending_remote_validation(self) -> bool:
        record = self._load_record()
        return bool(record and record.pending_remote_validation)

    def _load_record(self) -> Optional[IdentityRecord]:
        if not self.exists():
            return None

        with open(self._save_path, "rb") as file:
            raw = file.read()

        payload = json.loads(self._vault.decrypt(raw))
        username = payload.get("username")
        if not isinstance(username, str) or not username:
            return None

        return IdentityRecord(
            username=username,
            pending_remote_validation=bool(payload.get("pending_remote_validation", False)),
        )

    def _harden_file(self) -> None:
        try:
            os.chmod(self._save_path, 0o600)
            if os.name == "nt":
                import ctypes

                ctypes.windll.kernel32.SetFileAttributesW(self._save_path, 2)
        except Exception:
            log.warning("Could not harden identity file permissions", exc_info=True)


class _MongoIdentityValidator:
    def __init__(self, network_manager: "NetworkManager") -> None:
        self._network_manager = network_manager

    def is_name_available(self, name: str) -> bool:
        if not self._network_manager.is_online or self._network_manager.db is None:
            return True

        collection = self._network_manager.db[SETTINGS.NETWORK.SCORES_COLLECTION]
        existing_user = collection.find_one(
            {"name": {"$regex": f"^{re.escape(name)}$", "$options": "i"}}
        )
        return existing_user is None


class IdentityManager:
    def __init__(
        self,
        network_manager: Optional["NetworkManager"] = None,
        dao: Optional[IdentityDAO] = None,
        remote_validator: Optional[RemoteIdentityValidator] = None,
        prompt_provider: Optional[Callable[[Optional[str]], str]] = None,
    ) -> None:
        self._network_manager = network_manager
        self._dao = dao or _EncryptedFileIdentityDAO()
        self._remote_validator = remote_validator or (
            _MongoIdentityValidator(network_manager) if network_manager is not None else None
        )
        self._prompt_provider = prompt_provider
        self._prompt_error: Optional[str] = None

    def get_or_create_identity(self) -> str:
        current_name = self.get_existing_identity()
        if current_name:
            return current_name

        while True:
            name = self._prompt_for_name()

            if self.register_identity(name):
                return name

            self._prompt_error = (
                "Use 3-15 letras, numeros ou underscore. Nome deve ser unico."
            )

    def validate_name(self, name: str) -> bool:
        if not USERNAME_PATTERN.fullmatch(name):
            return False

        if self._remote_validator is None or not self._is_online():
            return True

        try:
            return self._remote_validator.is_name_available(name)
        except Exception:
            log.warning("Remote identity validation failed; allowing temporary offline identity", exc_info=True)
            return True

    def is_registered(self) -> bool:
        return self.get_existing_identity() is not None

    def get_existing_identity(self) -> Optional[str]:
        try:
            current_name = self._dao.load_name()
            if not current_name:
                return None

            if not self._dao.has_pending_remote_validation() or not self._is_online():
                return current_name

            if self.validate_name(current_name):
                self._dao.save_name(current_name, pending_remote_validation=False)
                return current_name

            log.warning("Stored offline identity conflicts with remote data")
            return None
        except Exception:
            log.warning("Stored identity is missing or unreadable", exc_info=True)
            return None

    def register_identity(self, name: str) -> bool:
        name = name.strip()
        if not self.validate_name(name):
            return False

        pending_remote_validation = not self._is_online()
        self._dao.save_name(name, pending_remote_validation=pending_remote_validation)
        return True

    def _prompt_for_name(self) -> str:
        if self._prompt_provider is not None:
            return self._prompt_provider(self._prompt_error).strip()

        raise RuntimeError("Identity prompt requires an injected prompt_provider.")

    def _is_online(self) -> bool:
        return bool(self._network_manager and self._network_manager.is_online)

import json
import os
from datetime import datetime, timezone
from json import JSONDecodeError
from typing import Any, Optional, TYPE_CHECKING

from cryptography.fernet import InvalidToken

from security.vault import Vault
from utils.logger import log
from utils.path_manager import PathManager

if TYPE_CHECKING:
    from engine import GameSession


class UserDataDAO:
    def __init__(self, vault: Optional[Vault] = None, save_path: Optional[str] = None) -> None:
        self._vault = vault or Vault()
        self._save_path = save_path or PathManager.get_user_save_path()

    def save(self, session: "GameSession", name: str) -> bool:
        current_data = self.load() or {}
        current_score = self._safe_int(current_data.get("score"))

        if current_data and session.score <= current_score:
            log.debug("User data save skipped because no new high score was reached")
            return False

        record = self._build_record(
            name=name,
            score=session.score,
            lines=session.total_lines,
            level=session.level,
            played_at=self._utc_now(),
            pending_remote_validation=bool(current_data.get("pending_remote_validation", False)),
        )

        return self._write(record)

    def load(self) -> Optional[dict[str, Any]]:
        try:
            with open(self._save_path, "rb") as file:
                encrypted_data = file.read()

            decrypted_data = self._vault.decrypt(encrypted_data)
            data = json.loads(decrypted_data)
            if not isinstance(data, dict):
                log.warning("User data payload is not a JSON object")
                return None

            return data
        except FileNotFoundError:
            log.debug("User data file not found")
            return None
        except InvalidToken:
            log.error("User data integrity check failed", exc_info=True)
            raise
        except JSONDecodeError:
            log.error("User data JSON is invalid", exc_info=True)
            return None
        except Exception:
            log.error("Unexpected failure while loading user data", exc_info=True)
            return None

    def exists(self) -> bool:
        return os.path.exists(self._save_path)

    def delete(self) -> None:
        try:
            os.remove(self._save_path)
            log.info("User data file deleted")
        except FileNotFoundError:
            log.debug("User data delete skipped because file does not exist")

    def load_name(self) -> Optional[str]:
        data = self.load()
        if data is None:
            return None

        name = data.get("name")
        if isinstance(name, str) and name:
            return name

        username = data.get("username")
        if isinstance(username, str) and username:
            return username

        return None

    def save_name(self, name: str, pending_remote_validation: bool = False) -> None:
        current_data = self.load() or {}
        record = self._build_record(
            name=name,
            score=self._safe_int(current_data.get("score")),
            lines=self._safe_int(current_data.get("lines")),
            level=self._safe_int(current_data.get("level")),
            played_at=self._safe_played_at(current_data.get("played_at")),
            pending_remote_validation=pending_remote_validation,
        )
        if not self._write(record):
            raise RuntimeError("User identity persistence failed")

    def has_pending_remote_validation(self) -> bool:
        data = self.load()
        return bool(data and data.get("pending_remote_validation", False))

    def _write(self, data: dict[str, Any]) -> bool:
        try:
            os.makedirs(os.path.dirname(self._save_path), exist_ok=True)
            encrypted_data = self._vault.encrypt(json.dumps(data))
            with open(self._save_path, "wb") as file:
                file.write(encrypted_data)
            self._harden_file()
            log.info("User data saved successfully")
            return True
        except Exception:
            log.error("Failed to persist user data", exc_info=True)
            return False

    def _build_record(
        self,
        name: str,
        score: int,
        lines: int,
        level: int,
        played_at: str,
        pending_remote_validation: bool = False,
    ) -> dict[str, Any]:
        record = {
            "name": name,
            "score": score,
            "lines": lines,
            "level": level,
            "played_at": played_at,
        }
        if pending_remote_validation:
            record["pending_remote_validation"] = True
        return record

    def _harden_file(self) -> None:
        try:
            os.chmod(self._save_path, 0o600)
            if os.name == "nt":
                import ctypes

                ctypes.windll.kernel32.SetFileAttributesW(self._save_path, 2)
        except Exception:
            log.warning("Could not harden user data file permissions", exc_info=True)

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _safe_int(value: Any) -> int:
        return value if isinstance(value, int) and value >= 0 else 0

    @staticmethod
    def _safe_played_at(value: Any) -> str:
        return value if isinstance(value, str) and value else UserDataDAO._utc_now()

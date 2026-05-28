from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, Optional, TYPE_CHECKING

from settings import SETTINGS
from utils.logger import log

if TYPE_CHECKING:
    from network.connection_manager import NetworkManager
    from network.user_data_dao import UserDataDAO


class SyncStatus(Enum):
    SUCCESS = auto()
    FAILURE = auto()
    NO_CHANGE = auto()
    OFFLINE = auto()


class SyncResult:
    def __init__(self, status: SyncStatus, message: str = "") -> None:
        self.status = status
        self.message = message

    def __repr__(self) -> str:
        return f"SyncResult(status={self.status.name}, message='{self.message}')"


class DataSynchronizer:
    def __init__(self, dao: "UserDataDAO", network: "NetworkManager") -> None:
        self._dao = dao
        self._network = network

    def sync(self, name: str) -> SyncResult:
        if not self._network.is_online:
            log.info("Sync skipped: network is offline")
            return SyncResult(SyncStatus.OFFLINE, "No network connection")

        local_data = self._dao.load()
        if local_data is None:
            log.info("Sync skipped: no local data found")
            return SyncResult(SyncStatus.NO_CHANGE, "No local data")

        try:
            remote_data = self._query_remote(name)
        except Exception as exc:
            log.error("Sync failed: could not query remote data", exc_info=True)
            return SyncResult(SyncStatus.FAILURE, str(exc))

        if remote_data is None:
            return self._upload_local(local_data)

        local_score = self._safe_int(local_data.get("score"))
        remote_score = self._safe_int(remote_data.get("score"))

        if local_score > remote_score:
            return self._upload_local(local_data)

        if remote_score > local_score:
            return self._download_remote(name, remote_data)

        return self._resolve_tie(local_data, remote_data)

    def compare_scores(self, local: Dict[str, Any], remote: Optional[Dict[str, Any]]) -> bool:
        if remote is None:
            return True

        local_score = self._safe_int(local.get("score"))
        remote_score = self._safe_int(remote.get("score"))

        if local_score > remote_score:
            return True

        if local_score < remote_score:
            return False

        return self._local_timestamp_wins(local, remote)

    def upload_if_higher(self, user_data: Dict[str, Any]) -> bool:
        if not self._network.is_online or self._network.db is None:
            return False

        name = user_data.get("name", "")
        if not name:
            return False

        try:
            remote_data = self._query_remote(name)

            if not self.compare_scores(user_data, remote_data):
                log.info(
                    "Upload skipped for '%s': local score (%s) is not higher than remote",
                    name,
                    user_data.get("score", 0),
                )
                return False

            collection = self._network.db[SETTINGS.NETWORK.SCORES_COLLECTION]
            collection.update_one(
                {"name": name},
                {
                    "$set": {
                        "score": self._safe_int(user_data.get("score")),
                        "lines": self._safe_int(user_data.get("lines")),
                        "level": self._safe_int(user_data.get("level")),
                        "played_at": self._parse_played_at(user_data.get("played_at")),
                    }
                },
                upsert=True,
            )
            log.info(
                "Uploaded data for '%s' (score=%s)",
                name,
                user_data.get("score", 0),
            )
            return True
        except Exception as exc:
            log.error("Upload failed for '%s'", name, exc_info=True)
            return False

    def download_if_higher(self, name: str) -> Optional[Dict[str, Any]]:
        if not self._network.is_online or self._network.db is None:
            return None

        try:
            remote_data = self._query_remote(name)
            if remote_data is None:
                return None

            if self._persist_remote_if_higher(remote_data):
                log.info(
                    "Downloaded remote data for '%s' (score=%s)",
                    name,
                    remote_data.get("score", 0),
                )
                return remote_data

            return None
        except Exception as exc:
            log.error("Download failed for '%s'", name, exc_info=True)
            return None

    def _persist_remote_if_higher(self, remote_data: Dict[str, Any]) -> bool:
        local_data = self._dao.load()

        if local_data is None or self._is_remote_higher(local_data, remote_data):
            return self._dao.save_dict(remote_data)

        return False

    def _query_remote(self, name: str) -> Optional[Dict[str, Any]]:
        if self._network.db is None:
            return None
        collection = self._network.db[SETTINGS.NETWORK.SCORES_COLLECTION]
        doc = collection.find_one({"name": name})
        if doc is None:
            return None
        return self._mongo_doc_to_dict(doc, name)

    def _mongo_doc_to_dict(self, doc: Dict[str, Any], name: str) -> Dict[str, Any]:
        return {
            "name": doc.get("name", name),
            "score": self._safe_int(doc.get("score")),
            "lines": self._safe_int(doc.get("lines")),
            "level": self._safe_int(doc.get("level")),
            "played_at": str(doc.get("played_at", self._utc_now())),
        }

    def _is_remote_higher(self, local: Dict[str, Any], remote: Dict[str, Any]) -> bool:
        return self._safe_int(remote.get("score")) > self._safe_int(local.get("score"))

    def _local_timestamp_wins(self, local: Dict[str, Any], remote: Dict[str, Any]) -> bool:
        local_ts = self._parse_played_at(local.get("played_at", ""))
        remote_ts = self._parse_played_at(remote.get("played_at", ""))

        diff = abs((local_ts - remote_ts).total_seconds())

        if diff < 1.0:
            return True

        return local_ts > remote_ts

    def _resolve_tie(
        self,
        local: Dict[str, Any],
        remote: Dict[str, Any],
    ) -> SyncResult:
        try:
            local_ts = self._parse_played_at(local.get("played_at", ""))
            remote_ts = self._parse_played_at(remote.get("played_at", ""))
        except (ValueError, TypeError):
            return SyncResult(SyncStatus.NO_CHANGE, "No remote score changes")

        diff = abs((local_ts - remote_ts).total_seconds())

        if diff < 1.0:
            return SyncResult(
                SyncStatus.NO_CHANGE,
                "No remote score changes",
            )

        if local_ts > remote_ts:
            return self._upload_local(local)

        if self._persist_remote_if_higher(remote):
            return SyncResult(SyncStatus.SUCCESS, "Remote data downloaded locally")

        return SyncResult(SyncStatus.NO_CHANGE, "No remote score changes")

    def _upload_local(self, local_data: Dict[str, Any]) -> SyncResult:
        success = self.upload_if_higher(local_data)
        if success:
            return SyncResult(SyncStatus.SUCCESS, "Local data uploaded to server")
        return SyncResult(SyncStatus.FAILURE, "Upload failed")

    def _download_remote(self, name: str, remote_data: Dict[str, Any]) -> SyncResult:
        try:
            self._dao.save_dict(remote_data)
            log.info(
                "Downloaded remote data for '%s' (score=%s)",
                name,
                remote_data.get("score", 0),
            )
            return SyncResult(SyncStatus.SUCCESS, "Remote data downloaded locally")
        except Exception as exc:
            log.error("Download failed for '%s': %s", name, exc, exc_info=True)
            return SyncResult(SyncStatus.FAILURE, str(exc))

    @staticmethod
    def _safe_int(value: Any) -> int:
        if isinstance(value, (int, float)) and value >= 0:
            return int(value)
        return 0

    @staticmethod
    def _utc_now() -> str:
        return (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

    @staticmethod
    def _parse_played_at(value: Any) -> datetime:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value
        cleaned = str(value).replace("Z", "+00:00").replace("z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
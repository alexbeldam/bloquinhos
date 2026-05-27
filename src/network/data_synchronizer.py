"""
Data Synchronizer module.

Handles bidirectional synchronization between the local encrypted save file
and the remote MongoDB leaderboard.
"""

from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, Optional, TYPE_CHECKING

from settings import SETTINGS
from utils.logger import log

if TYPE_CHECKING:
    from network.connection_manager import NetworkManager
    from network.user_data_dao import UserDataDAO


class SyncStatus(Enum):
    """Represents the possible outcomes of a sync operation."""
    SUCCESS = auto()
    FAILURE = auto()
    NO_CHANGE = auto()
    OFFLINE = auto()


class SyncResult:
    """Encapsulates the result of a sync operation."""

    def __init__(self, status: SyncStatus, message: str = "") -> None:
        self.status = status
        self.message = message

    def __repr__(self) -> str:
        return f"SyncResult(status={self.status.name}, message='{self.message}')"


class DataSynchronizer:
    """Manages bidirectional sync between local encrypted save and remote MongoDB."""

    def __init__(self, dao: "UserDataDAO", network: "NetworkManager") -> None:
        self._dao = dao
        self._network = network

    def sync(self, name: str) -> SyncResult:
        """Compare local vs remote data and sync accordingly.

        Args:
            name: The player name to sync data for.

        Returns:
            A SyncResult describing the outcome.
        """
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
            log.error(f"Sync failed: could not query remote data — {exc}", exc_info=True)
            return SyncResult(SyncStatus.FAILURE, str(exc))

        if remote_data is None:
            return self._upload_local(local_data)

        local_score = self._safe_int(local_data.get("score"))
        remote_score = self._safe_int(remote_data.get("score"))

        if local_score > remote_score:
            return self._upload_local(local_data)

        if remote_score > local_score:
            return self._download_remote(name, remote_data)

        # Scores are equal — resolve by timestamp
        return self._resolve_tie(local_data, remote_data)

    def compare_scores(self, local: Dict[str, Any], remote: Optional[Dict[str, Any]]) -> bool:
        """Return True if local score is greater than remote score.

        When scores are equal the timestamps are compared to break the tie.
        If remote is None (no remote record), local always wins.
        """
        if remote is None:
            return True

        local_score = self._safe_int(local.get("score"))
        remote_score = self._safe_int(remote.get("score"))

        if local_score > remote_score:
            return True

        if local_score < remote_score:
            return False

        # Scores equal — use timestamp tie-breaker
        return self._local_timestamp_wins(local, remote)

    def upload_if_higher(self, user_data: Dict[str, Any]) -> bool:
        """Upload local data to MongoDB if it beats the remote record.

        Args:
            user_data: The local user data dict to upload.

        Returns:
            True if the upload succeeded or was not needed, False on error.
        """
        if not self._network.is_online or self._network.db is None:
            return False

        name = user_data.get("name", "")
        if not name:
            return False

        try:
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
            log.error("Upload failed for '%s': %s", name, exc, exc_info=True)
            return False

    def download_if_higher(self, name: str) -> Optional[Dict[str, Any]]:
        """Download remote data if it beats the local record.

        Persists the remote data to the local encrypted file when the remote
        score is higher than the local one.

        Args:
            name: The player name to download data for.

        Returns:
            The downloaded data dict, or None if the remote data is not
            better / does not exist / an error occurred.
        """
        if not self._network.is_online or self._network.db is None:
            return None

        try:
            collection = self._network.db[SETTINGS.NETWORK.SCORES_COLLECTION]
            remote_doc = collection.find_one({"name": name})
            if remote_doc is None:
                return None

            remote_data = self._mongo_doc_to_dict(remote_doc, name)
            local_data = self._dao.load()

            if local_data is None or self._is_remote_higher(local_data, remote_data):
                self._dao.save_dict(remote_data)
                log.info(
                    "Downloaded remote data for '%s' (score=%s)",
                    name,
                    remote_data.get("score", 0),
                )
                return remote_data

            return None
        except Exception as exc:
            log.error("Download failed for '%s': %s", name, exc, exc_info=True)
            return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _query_remote(self, name: str) -> Optional[Dict[str, Any]]:
        """Query MongoDB for a document matching the given name."""
        if self._network.db is None:
            return None
        collection = self._network.db[SETTINGS.NETWORK.SCORES_COLLECTION]
        doc = collection.find_one({"name": name})
        if doc is None:
            return None
        return self._mongo_doc_to_dict(doc, name)

    def _mongo_doc_to_dict(self, doc: Dict[str, Any], name: str) -> Dict[str, Any]:
        """Convert a raw MongoDB document to a plain dict."""
        return {
            "name": doc.get("name", name),
            "score": self._safe_int(doc.get("score")),
            "lines": self._safe_int(doc.get("lines")),
            "level": self._safe_int(doc.get("level")),
            "played_at": str(doc.get("played_at", self._utc_now())),
        }

    def _is_remote_higher(self, local: Dict[str, Any], remote: Dict[str, Any]) -> bool:
        """Return True if the remote score is strictly greater than local."""
        return self._safe_int(remote.get("score")) > self._safe_int(local.get("score"))

    def _local_timestamp_wins(self, local: Dict[str, Any], remote: Dict[str, Any]) -> bool:
        """Resolve a timestamp tie — return True if local should be considered newer."""
        local_ts = self._parse_played_at(local.get("played_at", ""))
        remote_ts = self._parse_played_at(remote.get("played_at", ""))

        diff = abs((local_ts - remote_ts).total_seconds())

        # Timestamps within 1 second → keep local (no unnecessary sync)
        if diff < 1.0:
            return True

        return local_ts > remote_ts

    def _resolve_tie(
        self,
        local: Dict[str, Any],
        remote: Dict[str, Any],
    ) -> SyncResult:
        """Scores are equal — use the most recent timestamp to decide direction."""
        try:
            local_ts = self._parse_played_at(local.get("played_at", ""))
            remote_ts = self._parse_played_at(remote.get("played_at", ""))
        except (ValueError, TypeError):
            return SyncResult(SyncStatus.NO_CHANGE, "Scores equal, skipping sync")

        diff = abs((local_ts - remote_ts).total_seconds())

        # Timestamps very close → no action needed
        if diff < 1.0:
            return SyncResult(
                SyncStatus.NO_CHANGE,
                "Scores equal with close timestamps, no action",
            )

        if local_ts > remote_ts:
            return self._upload_local(local)

        return self._download_remote(local.get("name", ""), remote)

    def _upload_local(self, local_data: Dict[str, Any]) -> SyncResult:
        """Helper: upload local data and wrap result."""
        success = self.upload_if_higher(local_data)
        if success:
            return SyncResult(SyncStatus.SUCCESS, "Local data uploaded to server")
        return SyncResult(SyncStatus.FAILURE, "Upload failed")

    def _download_remote(self, name: str, remote_data: Dict[str, Any]) -> SyncResult:
        """Helper: download remote data and wrap result."""
        result = self.download_if_higher(name)
        if result is not None:
            return SyncResult(SyncStatus.SUCCESS, "Remote data downloaded locally")
        return SyncResult(SyncStatus.FAILURE, "Download failed")

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_int(value: Any) -> int:
        """Return value if it is a non-negative int, otherwise 0."""
        return value if isinstance(value, int) and value >= 0 else 0

    @staticmethod
    def _utc_now() -> str:
        """Return current UTC timestamp as ISO-8601 string (Z suffix)."""
        return (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

    @staticmethod
    def _parse_played_at(value: Any) -> datetime:
        """Parse a played_at value into a datetime object."""
        if isinstance(value, datetime):
            return value
        cleaned = str(value).replace("Z", "+00:00").replace("z", "+00:00")
        return datetime.fromisoformat(cleaned)
from dataclasses import dataclass
import time
from typing import Dict, List, Optional, TYPE_CHECKING

from settings import SETTINGS
from utils.logger import log

if TYPE_CHECKING:
    from network.connection_manager import NetworkManager
    from network.user_data_dao import UserDataDAO


@dataclass(frozen=True)
class LeaderboardEntry:
    rank: int
    name: str
    score: int

@dataclass(frozen=True)
class CachedUserRank:
    rank: Optional[int]
    cache_time: float


@dataclass(frozen=True)
class CachedTopEntries:
    entries: List[LeaderboardEntry]
    cache_time: float

@dataclass(frozen=True)
class UserRecord:
    name: str
    score: int
    rank: Optional[int] = None

@dataclass(frozen=True)
class LeaderboardSnapshot:
    top_entries: Optional[List[LeaderboardEntry]]
    local_record: Optional[UserRecord]

class LeaderboardManager:
    def __init__(self, network: "NetworkManager", dao: "UserDataDAO") -> None:
        self.network = network
        self.dao = dao
        self._cached_top_entries: Optional[CachedTopEntries] = None
        self._cached_user_ranks: Dict[str, CachedUserRank] = {}

    def _is_cache_valid(self, cache_time: float) -> bool:
        return (time.time() - cache_time) < SETTINGS.NETWORK.LEADERBOARD_CACHE_DURATION

    def _invalidate_rank_cache(self) -> None:
        self._cached_top_entries = None
        self._cached_user_ranks.clear()

    def _get_top_5(self, force_refresh: bool = False) -> Optional[List[LeaderboardEntry]]:
        cached_entries = self._cached_top_entries
        if (
            not force_refresh
            and cached_entries is not None
            and self._is_cache_valid(cached_entries.cache_time)
        ):
            return list(cached_entries.entries)

        if not self.network.is_online:
            return None

        try:
            collection = self.network.db["scores"]
            cursor = collection.find().sort("score", -1).limit(5)

            entries = []
            for rank, doc in enumerate(cursor, 1):
                entry = LeaderboardEntry(
                    rank=rank,
                    name=doc.get("name", "Desconhecido"),
                    score=int(doc.get("score", 0))
                )
                entries.append(entry)

            self._cached_top_entries = CachedTopEntries(entries=entries, cache_time=time.time())
            return list(entries)
        except Exception:
            log.error("Failed to fetch leaderboard", exc_info=True)
            return None

    def _get_user_rank(self, name: str, force_refresh: bool = False) -> Optional[int]:
        cached = self._cached_user_ranks.get(name)
        if (
            not force_refresh
            and cached is not None
            and self._is_cache_valid(cached.cache_time)
        ):
            return cached.rank

        if not self.network.is_online:
            return None

        try:
            collection = self.network.db["scores"]
            user_doc = collection.find_one({"name": name})

            if not user_doc:
                self._cached_user_ranks[name] = CachedUserRank(None, time.time())
                return None

            user_score = user_doc.get("score", 0)
            rank = collection.count_documents({"score": {"$gt": user_score}}) + 1

            self._cached_user_ranks[name] = CachedUserRank(rank, time.time())
            return rank
        except Exception:
            log.error("Failed to fetch user rank", exc_info=True)
            return None

    def submit_score(self, name: str, score: int, lines: int, level: int) -> bool:
        if not self.network.is_online or self.network.db is None:
            return False

        try:
            collection = self.network.db["scores"]
            existing = collection.find_one({"name": name})
            if existing and int(existing.get("score", 0)) >= score:
                return False
            collection.update_one(
                {"name": name},
                {"$set": {"score": score, "lines": lines, "level": level}},
                upsert=True,
            )
            self._invalidate_rank_cache()
            log.info("Score submitted for '%s' (score=%s)", name, score)
            return True
        except Exception:
            log.error("Failed to submit score", exc_info=True)
            return False

    def _get_local_record(self) -> Optional[UserRecord]:
        data = self.dao.load()
        if data is None:
            return None

        return UserRecord(
            name=data.get("name", "Desconhecido"),
            score=int(data.get("score", 0))
        )

    def get_snapshot(self, user_name: Optional[str] = None, force_refresh: bool = False) -> LeaderboardSnapshot:
        local_record = self._get_local_record()
        lookup_name = user_name or (local_record.name if local_record is not None else None)

        user_rank = (
            self._get_user_rank(lookup_name, force_refresh=force_refresh)
            if lookup_name is not None
            else None
        )

        if local_record is not None and lookup_name == local_record.name:
            local_record = UserRecord(
                name=local_record.name,
                score=local_record.score,
                rank=user_rank
            )

        return LeaderboardSnapshot(
            top_entries=self._get_top_5(force_refresh=force_refresh),
            local_record=local_record,
        )
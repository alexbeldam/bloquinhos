from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING

from utils.logger import log

if TYPE_CHECKING:
    from network.connection_manager import NetworkManager
    from network.user_data_dao import UserDataDAO


@dataclass
class LeaderboardEntry:
    rank: int
    name: str
    score: int


class LeaderboardManager:
    def __init__(self, network: "NetworkManager", dao: "UserDataDAO") -> None:
        self.network = network
        self.dao = dao
        self._cached_entries: Optional[List[LeaderboardEntry]] = None
        self._cache_time: float = 0.0

    def get_top_5(self) -> List[LeaderboardEntry]:
        if not self.network.is_online:
            return []

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
            
            return entries
        except Exception as e:
            log.error("Failed to fetch leaderboard", exc_info=True)
            return []

    def get_user_rank(self, name: str) -> Optional[int]:
        if not self.network.is_online:
            return None

        try:
            collection = self.network.db["scores"]
            user_doc = collection.find_one({"name": name})
            
            if not user_doc:
                return None
            
            user_score = user_doc.get("score", 0)
            rank = collection.count_documents({"score": {"$gt": user_score}}) + 1
            
            return rank
        except Exception as e:
            log.error("Failed to fetch user rank", exc_info=True)
            return None

    def get_local_record(self) -> Optional[dict]:
        data = self.dao.load()
        if data is None:
            return None
        
        return {
            "name": data.get("name", "Desconhecido"),
            "score": int(data.get("score", 0))
        }

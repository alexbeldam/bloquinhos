"""Unit tests for DataSynchronizer."""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest

from network.data_synchronizer import DataSynchronizer, SyncResult, SyncStatus
from network.user_data_dao import UserDataDAO


class TestDataSynchronizer:
    """Test suite for DataSynchronizer class."""

    @pytest.fixture
    def mock_dao(self) -> Mock:
        """Create a mock UserDataDAO."""
        return Mock(spec=UserDataDAO)

    @pytest.fixture
    def mock_network(self) -> Mock:
        """Create a mock NetworkManager."""
        network = Mock()
        network.is_online = True
        network.db = MagicMock()
        return network

    @pytest.fixture
    def synchronizer(self, mock_dao: Mock, mock_network: Mock) -> DataSynchronizer:
        """Create a DataSynchronizer instance with mocked dependencies."""
        return DataSynchronizer(mock_dao, mock_network)

    # =========================================================================
    # Tests for compare_scores()
    # =========================================================================

    def test_compare_scores_local_higher(self, synchronizer: DataSynchronizer) -> None:
        """Local score greater than remote should return True."""
        local = {"score": 100, "name": "player1"}
        remote = {"score": 50, "name": "player1"}
        assert synchronizer.compare_scores(local, remote) is True

    def test_compare_scores_local_lower(self, synchronizer: DataSynchronizer) -> None:
        """Local score less than remote should return False."""
        local = {"score": 50, "name": "player1"}
        remote = {"score": 100, "name": "player1"}
        assert synchronizer.compare_scores(local, remote) is False

    def test_compare_scores_remote_none(self, synchronizer: DataSynchronizer) -> None:
        """No remote record should return True (local wins)."""
        local = {"score": 50, "name": "player1"}
        assert synchronizer.compare_scores(local, None) is True

    def test_compare_scores_equal_local_newer(self, synchronizer: DataSynchronizer) -> None:
        """Equal scores with newer local timestamp should return True."""
        now = datetime.now(timezone.utc)
        local = {
            "score": 100,
            "name": "player1",
            "played_at": now.isoformat(),
        }
        remote = {
            "score": 100,
            "name": "player1",
            "played_at": (now - timedelta(minutes=5)).isoformat(),
        }
        assert synchronizer.compare_scores(local, remote) is True

    def test_compare_scores_equal_remote_newer(self, synchronizer: DataSynchronizer) -> None:
        """Equal scores with newer remote timestamp should return False."""
        now = datetime.now(timezone.utc)
        local = {
            "score": 100,
            "name": "player1",
            "played_at": (now - timedelta(minutes=5)).isoformat(),
        }
        remote = {
            "score": 100,
            "name": "player1",
            "played_at": now.isoformat(),
        }
        assert synchronizer.compare_scores(local, remote) is False

    def test_compare_scores_equal_timestamps_within_one_second(
        self, synchronizer: DataSynchronizer
    ) -> None:
        """Timestamps within 1 second should prefer local."""
        now = datetime.now(timezone.utc)
        local = {
            "score": 100,
            "name": "player1",
            "played_at": now.isoformat(),
        }
        remote = {
            "score": 100,
            "name": "player1",
            "played_at": (now - timedelta(milliseconds=500)).isoformat(),
        }
        assert synchronizer.compare_scores(local, remote) is True

    # =========================================================================
    # Tests for upload_if_higher()
    # =========================================================================

    def test_upload_if_higher_offline(
        self, synchronizer: DataSynchronizer, mock_network: Mock
    ) -> None:
        """Offline network should return False."""
        mock_network.is_online = False
        result = synchronizer.upload_if_higher({"name": "player1", "score": 100})
        assert result is False

    def test_upload_if_higher_no_name(
        self, synchronizer: DataSynchronizer
    ) -> None:
        """Missing name should return False."""
        result = synchronizer.upload_if_higher({"score": 100})
        assert result is False

    def test_upload_if_higher_local_wins(
        self,
        synchronizer: DataSynchronizer,
        mock_network: Mock,
        mock_dao: Mock,
    ) -> None:
        """Upload should succeed when local score is higher."""
        local_data = {
            "name": "player1",
            "score": 100,
            "lines": 5,
            "level": 2,
            "played_at": datetime.now(timezone.utc).isoformat(),
        }
        remote_data = {
            "score": 50,
            "lines": 2,
            "level": 1,
            "played_at": datetime.now(timezone.utc).isoformat(),
        }

        collection = MagicMock()
        mock_network.db = {"scores": collection}
        collection.find_one.return_value = remote_data

        result = synchronizer.upload_if_higher(local_data)
        assert result is True
        collection.update_one.assert_called_once()

    def test_upload_if_higher_local_not_higher(
        self,
        synchronizer: DataSynchronizer,
        mock_network: Mock,
    ) -> None:
        """Upload should be skipped when local score is not higher."""
        local_data = {
            "name": "player1",
            "score": 50,
            "lines": 2,
            "level": 1,
            "played_at": datetime.now(timezone.utc).isoformat(),
        }
        remote_data = {
            "score": 100,
            "lines": 5,
            "level": 2,
            "played_at": datetime.now(timezone.utc).isoformat(),
        }

        collection = MagicMock()
        mock_network.db = {"scores": collection}
        collection.find_one.return_value = remote_data

        result = synchronizer.upload_if_higher(local_data)
        assert result is False
        collection.update_one.assert_not_called()

    def test_upload_if_higher_new_player(
        self,
        synchronizer: DataSynchronizer,
        mock_network: Mock,
    ) -> None:
        """Upload should succeed for new player (no remote record)."""
        local_data = {
            "name": "newplayer",
            "score": 50,
            "lines": 2,
            "level": 1,
            "played_at": datetime.now(timezone.utc).isoformat(),
        }

        collection = MagicMock()
        mock_network.db = {"scores": collection}
        collection.find_one.return_value = None  # No remote record

        result = synchronizer.upload_if_higher(local_data)
        assert result is True
        collection.update_one.assert_called_once()

    # =========================================================================
    # Tests for download_if_higher()
    # =========================================================================

    def test_download_if_higher_offline(
        self, synchronizer: DataSynchronizer, mock_network: Mock
    ) -> None:
        """Offline network should return None."""
        mock_network.is_online = False
        result = synchronizer.download_if_higher("player1")
        assert result is None

    def test_download_if_higher_remote_not_found(
        self,
        synchronizer: DataSynchronizer,
        mock_network: Mock,
    ) -> None:
        """No remote record should return None."""
        collection = MagicMock()
        mock_network.db = {"scores": collection}
        collection.find_one.return_value = None

        result = synchronizer.download_if_higher("player1")
        assert result is None

    def test_download_if_higher_remote_wins(
        self,
        synchronizer: DataSynchronizer,
        mock_network: Mock,
        mock_dao: Mock,
    ) -> None:
        """Download should persist when remote score is higher."""
        local_data = {
            "name": "player1",
            "score": 50,
            "lines": 2,
            "level": 1,
            "played_at": datetime.now(timezone.utc).isoformat(),
        }
        remote_doc = {
            "_id": "123",
            "name": "player1",
            "score": 100,
            "lines": 5,
            "level": 2,
            "played_at": datetime.now(timezone.utc),
        }

        collection = MagicMock()
        mock_network.db = {"scores": collection}
        collection.find_one.return_value = remote_doc
        mock_dao.load.return_value = local_data
        mock_dao.save_dict.return_value = True

        result = synchronizer.download_if_higher("player1")
        assert result is not None
        assert result.get("score") == 100
        mock_dao.save_dict.assert_called_once()

    def test_download_if_higher_local_wins(
        self,
        synchronizer: DataSynchronizer,
        mock_network: Mock,
        mock_dao: Mock,
    ) -> None:
        """Download should be skipped when local score is higher."""
        local_data = {
            "name": "player1",
            "score": 100,
            "lines": 5,
            "level": 2,
            "played_at": datetime.now(timezone.utc).isoformat(),
        }
        remote_doc = {
            "_id": "123",
            "name": "player1",
            "score": 50,
            "lines": 2,
            "level": 1,
            "played_at": datetime.now(timezone.utc),
        }

        collection = MagicMock()
        mock_network.db = {"scores": collection}
        collection.find_one.return_value = remote_doc
        mock_dao.load.return_value = local_data
        mock_dao.save_dict.return_value = False

        result = synchronizer.download_if_higher("player1")
        assert result is None
        mock_dao.save_dict.assert_not_called()

    # =========================================================================
    # Tests for sync()
    # =========================================================================

    def test_sync_offline(
        self, synchronizer: DataSynchronizer, mock_network: Mock
    ) -> None:
        """Offline sync should return OFFLINE status."""
        mock_network.is_online = False
        result = synchronizer.sync("player1")
        assert result.status == SyncStatus.OFFLINE

    def test_sync_no_local_data(
        self, synchronizer: DataSynchronizer, mock_dao: Mock
    ) -> None:
        """No local data should return NO_CHANGE."""
        mock_dao.load.return_value = None
        result = synchronizer.sync("player1")
        assert result.status == SyncStatus.NO_CHANGE

    def test_sync_local_higher(
        self,
        synchronizer: DataSynchronizer,
        mock_network: Mock,
        mock_dao: Mock,
    ) -> None:
        """Local higher should upload."""
        local_data = {
            "name": "player1",
            "score": 100,
            "lines": 5,
            "level": 2,
            "played_at": datetime.now(timezone.utc).isoformat(),
        }
        remote_data = {
            "score": 50,
            "lines": 2,
            "level": 1,
            "played_at": datetime.now(timezone.utc).isoformat(),
        }

        collection = MagicMock()
        mock_network.db = {"scores": collection}
        mock_dao.load.return_value = local_data
        collection.find_one.return_value = remote_data

        result = synchronizer.sync("player1")
        assert result.status == SyncStatus.SUCCESS
        collection.update_one.assert_called_once()

    def test_sync_remote_higher(
        self,
        synchronizer: DataSynchronizer,
        mock_network: Mock,
        mock_dao: Mock,
    ) -> None:
        """Remote higher should download."""
        local_data = {
            "name": "player1",
            "score": 50,
            "lines": 2,
            "level": 1,
            "played_at": datetime.now(timezone.utc).isoformat(),
        }
        remote_doc = {
            "_id": "123",
            "name": "player1",
            "score": 100,
            "lines": 5,
            "level": 2,
            "played_at": datetime.now(timezone.utc),
        }

        collection = MagicMock()
        mock_network.db = {"scores": collection}
        mock_dao.load.return_value = local_data
        collection.find_one.return_value = remote_doc
        mock_dao.save_dict.return_value = True

        result = synchronizer.sync("player1")
        assert result.status == SyncStatus.SUCCESS
        mock_dao.save_dict.assert_called_once()

    def test_sync_equal_scores_local_newer(
        self,
        synchronizer: DataSynchronizer,
        mock_network: Mock,
        mock_dao: Mock,
    ) -> None:
        """Equal scores with newer local should upload."""
        now = datetime.now(timezone.utc)
        local_data = {
            "name": "player1",
            "score": 100,
            "lines": 5,
            "level": 2,
            "played_at": now.isoformat(),
        }
        remote_doc = {
            "_id": "123",
            "name": "player1",
            "score": 100,
            "lines": 5,
            "level": 2,
            "played_at": now - timedelta(minutes=5),
        }

        collection = MagicMock()
        mock_network.db = {"scores": collection}
        mock_dao.load.return_value = local_data
        collection.find_one.return_value = remote_doc

        result = synchronizer.sync("player1")
        assert result.status == SyncStatus.SUCCESS
        collection.update_one.assert_called_once()

    def test_sync_query_remote_error(
        self,
        synchronizer: DataSynchronizer,
        mock_network: Mock,
        mock_dao: Mock,
    ) -> None:
        """Remote query error should return FAILURE."""
        mock_dao.load.return_value = {"name": "player1", "score": 100}
        mock_network.db = None

        result = synchronizer.sync("player1")
        assert result.status == SyncStatus.FAILURE

    # =========================================================================
    # Utility method tests
    # =========================================================================

    def test_safe_int_valid_int(self, synchronizer: DataSynchronizer) -> None:
        """Valid int should return as-is."""
        assert synchronizer._safe_int(42) == 42

    def test_safe_int_valid_float(self, synchronizer: DataSynchronizer) -> None:
        """Valid float should be converted to int."""
        assert synchronizer._safe_int(42.5) == 42

    def test_safe_int_negative(self, synchronizer: DataSynchronizer) -> None:
        """Negative int should return 0."""
        assert synchronizer._safe_int(-10) == 0

    def test_safe_int_invalid_type(self, synchronizer: DataSynchronizer) -> None:
        """Invalid type should return 0."""
        assert synchronizer._safe_int("not a number") == 0

    def test_parse_played_at_iso_string(self, synchronizer: DataSynchronizer) -> None:
        """ISO-8601 string should parse correctly."""
        iso_str = "2026-05-27T10:30:00+00:00"
        result = synchronizer._parse_played_at(iso_str)
        assert isinstance(result, datetime)
        assert result.tzinfo is not None

    def test_parse_played_at_iso_z_suffix(self, synchronizer: DataSynchronizer) -> None:
        """ISO-8601 with Z suffix should parse correctly."""
        iso_str = "2026-05-27T10:30:00Z"
        result = synchronizer._parse_played_at(iso_str)
        assert isinstance(result, datetime)
        assert result.tzinfo is not None

    def test_parse_played_at_datetime_object(self, synchronizer: DataSynchronizer) -> None:
        """Datetime object should be returned with UTC timezone."""
        dt = datetime(2026, 5, 27, 10, 30, 0)
        result = synchronizer._parse_played_at(dt)
        assert result.tzinfo is not None

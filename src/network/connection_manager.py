import threading
import time
import urllib.parse
from dataclasses import dataclass
from typing import Callable, List

import certifi
from pymongo import MongoClient

from settings import SETTINGS
from utils.env_manager import get_env
from utils.logger import log


@dataclass(frozen=True)
class ConnectionStatusSnapshot:
    state: str
    is_online: bool
    can_retry: bool
    reconnect_policy: str

    @property
    def is_retrying(self) -> bool:
        return self.state == "retrying"


class NetworkManager:
    def __init__(self, start_offline: bool = False, reconnect_policy: str = "auto"):
        self._start_offline = start_offline
        self._reconnect_policy = self._normalize_reconnect_policy(reconnect_policy)
        self.is_online = False
        self.db = None
        self._use_tls = False
        self._ready_event = threading.Event()
        self._reconnect_listeners: List[Callable[[], None]] = []
        self._status_listeners: List[Callable[[ConnectionStatusSnapshot], None]] = []
        self._connect_request_event = threading.Event()
        self._state_lock = threading.Lock()
        self._auto_retries_remaining = SETTINGS.NETWORK.AUTO_MAX_RETRIES
        self._retry_attempt_counter = 0
        self._pending_attempt = False
        
        user = get_env("DB_USER") or ""
        password = urllib.parse.quote_plus(get_env("DB_PASSWORD", "") or "")
        host = (get_env("DB_HOST") or "").strip()
        port = get_env("DB_PORT") or ""
        self.db_name = get_env("DB_NAME") or ""

        if not host:
            self.mongo_uri = ""
            self._start_offline = True
            log.warning("Database host is not configured; starting in offline mode")
        elif ".net" in host.lower():
            self.mongo_uri = f"mongodb+srv://{user}:{password}@{host}/{self.db_name}?retryWrites=true&w=majority"
            self._use_tls = True
        else:
            self.mongo_uri = f"mongodb://{user}:{password}@{host}:{port}/{self.db_name}?authSource=admin"

        self._log_reconnect_policy()

        if not self._start_offline:
            self._pending_attempt = True
            self._connect_request_event.set()
        else:
            log.info("Offline mode active")
            self._ready_event.set()

        self._status_snapshot = self._build_status_snapshot()

        self.thread = threading.Thread(target=self._check_connection_loop, daemon=True)
        self.thread.start()

    def add_reconnect_listener(self, listener: Callable[[], None]) -> None:
        self._reconnect_listeners.append(listener)

    def add_status_listener(self, listener: Callable[[ConnectionStatusSnapshot], None]) -> None:
        self._status_listeners.append(listener)

    def get_status_snapshot(self) -> ConnectionStatusSnapshot:
        with self._state_lock:
            return self._status_snapshot

    def update_reconnect_policy(self, reconnect_policy: str) -> None:
        normalized_policy = self._normalize_reconnect_policy(reconnect_policy)

        with self._state_lock:
            if normalized_policy == self._reconnect_policy:
                return

            self._reconnect_policy = normalized_policy
            self._auto_retries_remaining = SETTINGS.NETWORK.AUTO_MAX_RETRIES
            self._retry_attempt_counter = 0

        self._notify_status_if_changed()
        self._log_reconnect_policy()

    def request_connection(self) -> None:
        if not self.mongo_uri:
            log.warning("Network connection requested but database host is not configured")
            return

        with self._state_lock:
            self._start_offline = False
            self._pending_attempt = True
            self._auto_retries_remaining = SETTINGS.NETWORK.AUTO_MAX_RETRIES
            self._retry_attempt_counter = 0

        self._notify_status_if_changed()
        self._connect_request_event.set()
        log.info("Network connection requested")

    def wait_for_connection(self, timeout: float | None = None) -> bool:
        if self._start_offline:
            return False
        
        if timeout is None:
            timeout = SETTINGS.NETWORK.DEFAULT_TIMEOUT
        
        self._ready_event.wait(timeout=timeout)
        
        return self.is_online

    def _check_connection_loop(self):
        client = None
        first_attempt = True
        was_offline = False

        while True:
            retry_delay_s: float | None = None

            with self._state_lock:
                pending_attempt = self._pending_attempt

            if client is None and not pending_attempt:
                self._connect_request_event.wait()
                self._connect_request_event.clear()
                continue

            try:
                if not client:
                    mongo_args = {
                        "host": self.mongo_uri,
                        "serverSelectionTimeoutMS": SETTINGS.NETWORK.SERVER_SELECTION_TIMEOUT_MS,
                        "tls": self._use_tls
                    }

                    if self._use_tls:
                        mongo_args["tlsCAFile"] = certifi.where()

                    client = MongoClient(**mongo_args)
                
                client.admin.command('ping')
                with self._state_lock:
                    self.is_online = True
                    self._pending_attempt = False
                    self._auto_retries_remaining = SETTINGS.NETWORK.AUTO_MAX_RETRIES
                    self._retry_attempt_counter = 0
                self.db = client[self.db_name]
                self._notify_status_if_changed()
                
                if first_attempt:
                    log.info(f"Database connection established - connected to '{self.db_name}' database")
                    first_attempt = False
                elif was_offline:
                    log.info("Database connection restored after temporary failure")
                    was_offline = False
                    self._notify_reconnect_listeners()

            except Exception as e:
                with self._state_lock:
                    reconnect_policy = self._reconnect_policy
                is_initial_attempt = first_attempt

                if self.is_online or first_attempt:
                    log.error(f"Database connection failed: {str(e)[:100]}")
                    log.debug(f"Full error details: {e}", exc_info=True)
                
                with self._state_lock:
                    self.is_online = False
                self.db = None
                client = None
                first_attempt = False
                was_offline = True

                if not self._should_retry_after_failure():
                    with self._state_lock:
                        self._pending_attempt = False
                        self._retry_attempt_counter = 0
                    if reconnect_policy == "manual":
                        if is_initial_attempt:
                            log.warning("Failed to connect - continuing offline")
                        else:
                            log.warning("Failed to reconnect - continuing offline")
                else:
                    retry_delay_s = self._next_retry_delay()
                    log.warning(f"Connection failed. Next attempt in {retry_delay_s:.1f}s")

                self._notify_status_if_changed()

            finally:
                if not self._ready_event.is_set():
                    self._ready_event.set()

            if client is not None:
                time.sleep(SETTINGS.NETWORK.HEARTBEAT_INTERVAL_S)
            elif self._pending_attempt and retry_delay_s is not None:
                time.sleep(retry_delay_s)

    def _should_retry_after_failure(self) -> bool:
        with self._state_lock:
            reconnect_policy = self._reconnect_policy

        if reconnect_policy == "manual":
            return False

        if reconnect_policy == "auto":
            with self._state_lock:
                if self._auto_retries_remaining <= 0:
                    exhausted = True
                else:
                    self._auto_retries_remaining -= 1
                    self._retry_attempt_counter += 1
                    exhausted = False

            if exhausted:
                log.warning("Network auto reconnect retries exhausted")
                return False
            return True

        with self._state_lock:
            self._retry_attempt_counter += 1
        return True

    def _next_retry_delay(self) -> float:
        with self._state_lock:
            reconnect_policy = self._reconnect_policy
            retry_attempt_counter = self._retry_attempt_counter

        if reconnect_policy == "manual":
            return SETTINGS.NETWORK.REQUEST_WAIT_S

        retry_index = max(1, retry_attempt_counter)
        delay = float(2 ** (retry_index - 1))

        if reconnect_policy == "always":
            return min(delay, float(SETTINGS.NETWORK.HEARTBEAT_INTERVAL_S))

        return delay

    @staticmethod
    def _normalize_reconnect_policy(mode: str) -> str:
        normalized = (mode or "auto").strip().lower()
        if normalized in {"manual", "auto", "always"}:
            return normalized
        return "auto"

    def _log_reconnect_policy(self) -> None:
        if self._start_offline:
            log.info("Offline start active")
            return

        if self._reconnect_policy == "manual":
            log.info("Manual connection mode active")
        elif self._reconnect_policy == "auto":
            log.info("Automatic connection mode active")
        else:
            log.info("Persistent connection mode active")

    def _notify_reconnect_listeners(self) -> None:
        for listener in self._reconnect_listeners:
            try:
                listener()
            except Exception:
                log.error("Reconnect listener failed", exc_info=True)

    def _build_status_snapshot(self) -> ConnectionStatusSnapshot:
        can_retry = bool(self.mongo_uri) and not self.is_online and not self._pending_attempt and (
            self._start_offline
            or self._reconnect_policy == "manual"
            or self._auto_retries_remaining <= 0
        )

        if self.is_online:
            state = "online"
        elif self._pending_attempt:
            state = "retrying"
        else:
            state = "offline"

        return ConnectionStatusSnapshot(
            state=state,
            is_online=self.is_online,
            can_retry=can_retry,
            reconnect_policy=self._reconnect_policy,
        )

    def _notify_status_if_changed(self) -> None:
        with self._state_lock:
            next_snapshot = self._build_status_snapshot()
            if next_snapshot == self._status_snapshot:
                return
            self._status_snapshot = next_snapshot
            listeners = list(self._status_listeners)

        for listener in listeners:
            try:
                listener(next_snapshot)
            except Exception:
                log.error("Connection status listener failed", exc_info=True)

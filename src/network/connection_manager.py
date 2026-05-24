import threading
import time
import urllib.parse
import certifi
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from utils.env_manager import get_env
from utils.logger import log

class NetworkManager:
    def __init__(self):
        self.is_online = False
        self.db = None
        self._use_tls = False
        self._ready_event = threading.Event()
        
        user = get_env("DB_USER")
        password = urllib.parse.quote_plus(get_env("DB_PASSWORD", ""))
        host = get_env("DB_HOST")
        port = get_env("DB_PORT")
        self.db_name = get_env("DB_NAME")

        if ".net" in host.lower():
            self.mongo_uri = f"mongodb+srv://{user}:{password}@{host}/{self.db_name}?retryWrites=true&w=majority"
            self._use_tls = True
        else:
            self.mongo_uri = f"mongodb://{user}:{password}@{host}:{port}/{self.db_name}?authSource=admin"

        self.thread = threading.Thread(target=self._check_connection_loop, daemon=True)
        self.thread.start()

    def wait_for_connection(self, timeout=None):
        from settings import SETTINGS
        
        if timeout is None:
            timeout = SETTINGS.NETWORK.DEFAULT_TIMEOUT
        
        self._ready_event.wait(timeout=timeout)
        
        return self.is_online

    def _check_connection_loop(self):
        client = None
        first_attempt = True
        was_offline = False

        while True:
            try:
                if not client:
                    from settings import SETTINGS
                    
                    mongo_args = {
                        "host": self.mongo_uri,
                        "serverSelectionTimeoutMS": SETTINGS.NETWORK.SERVER_SELECTION_TIMEOUT_MS,
                        "tls": self._use_tls
                    }

                    if self._use_tls:
                        mongo_args["tlsCAFile"] = certifi.where()

                    client = MongoClient(**mongo_args)
                
                client.admin.command('ping')
                self.is_online = True
                self.db = client[self.db_name]
                
                if first_attempt:
                    log.info(f"Database connection established - connected to '{self.db_name}' database")
                    first_attempt = False
                elif was_offline:
                    log.info("Database connection restored after temporary failure")
                    was_offline = False

            except Exception as e:
                if self.is_online or first_attempt:
                    log.error(f"Database connection failed: {str(e)[:100]}")
                    log.debug(f"Full error details: {e}", exc_info=True)
                
                self.is_online = False
                self.db = None
                client = None
                first_attempt = False
                was_offline = True

            finally:
                if not self._ready_event.is_set():
                    self._ready_event.set()
            
            from settings import SETTINGS
            time.sleep(SETTINGS.NETWORK.HEARTBEAT_INTERVAL_S)
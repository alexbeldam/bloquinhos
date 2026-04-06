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

    def wait_for_connection(self, timeout=3.0):
        self._ready_event.wait(timeout=timeout)
        
        return self.is_online

    def _check_connection_loop(self):
        client = None
        first_attempt = True

        while True:
            try:
                if not client:
                    mongo_args = {
                        "host": self.mongo_uri,
                        "serverSelectionTimeoutMS": 2000,
                        "tls": self._use_tls
                    }

                    if self._use_tls:
                        mongo_args["tlsCAFile"] = certifi.where()

                    client = MongoClient(**mongo_args)
                
                client.admin.command('ping')
                self.is_online = True
                self.db = client[self.db_name]
                
                if first_attempt:
                    log.info("🔌 Database: Connection established (Online Mode).")
                    first_attempt = False

            except Exception as e:
                if self.is_online or first_attempt:
                    log.error(f"🌐 Network: Lost connection or failed to connect. {e}")
                
                self.is_online = False
                self.db = None
                client = None
                first_attempt = False

            finally:
                if not self._ready_event.is_set():
                    self._ready_event.set()
            
            time.sleep(30)
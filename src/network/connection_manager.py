import threading
import time
import urllib.parse
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import dotenv_values
from utils.path_manager import get_env_path

class NetworkManager:
    def __init__(self):
        self.is_online = False
        self.db = None
        self._ready_event = threading.Event()
        
        config = dotenv_values(get_env_path())
        
        user = config.get("DB_USER")
        password = urllib.parse.quote_plus(config.get("DB_PASSWORD", ""))
        host = config.get("DB_HOST")
        port = config.get("DB_PORT")
        db_name = config.get("DB_NAME")

        if ".net" in host.lower():
            self.mongo_uri = f"mongodb+srv://{user}:{password}@{host}/{db_name}?retryWrites=true&w=majority"
        else:
            self.mongo_uri = f"mongodb://{user}:{password}@{host}:{port}/{db_name}?authSource=admin"

        self.thread = threading.Thread(target=self._check_connection_loop, daemon=True)
        self.thread.start()

    def wait_for_connection(self, timeout=3.0):
        self._ready_event.wait(timeout=timeout)
        
        return self.is_online

    def _check_connection_loop(self):
        client = None
        while True:
            try:
                if not client:
                    client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=2000)
                
                client.admin.command('ping')
                self.is_online = True
                self.db = client.get_database()
                
            except Exception as e:
                self.is_online = False
                client = None

            finally:
                self._ready_event.set()
            
            time.sleep(30)
    
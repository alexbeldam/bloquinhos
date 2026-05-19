from cryptography.fernet import Fernet, InvalidToken

from utils.logger import log
from .key_manager import KeyManager


class Vault:
    def __init__(self) -> None:
        key = self._get_or_create_key()
        self._fernet = Fernet(key)

    def encrypt(self, data: str) -> bytes:
        return self._fernet.encrypt(data.encode("utf-8"))

    def decrypt(self, encrypted_data: bytes) -> str:
        try:
            return self._fernet.decrypt(encrypted_data).decode("utf-8")
        except InvalidToken:
            log.error("Data integrity check failed — token invalid or tampered", exc_info=True)
            raise

    def _get_or_create_key(self) -> bytes:
        return KeyManager().load_or_create_key()

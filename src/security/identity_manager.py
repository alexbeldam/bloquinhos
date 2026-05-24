import json
import os
import re
from dataclasses import dataclass
from typing import Callable, Optional, Protocol, TYPE_CHECKING

import pygame

from settings import SETTINGS
from utils.logger import log
from utils.path_manager import PathManager
from .vault import Vault

if TYPE_CHECKING:
    from network.connection_manager import NetworkManager
    from ui.screen_manager import ScreenManager


USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,15}$")


class IdentityDAO(Protocol):
    def exists(self) -> bool: ...

    def load_name(self) -> Optional[str]: ...

    def save_name(self, name: str, pending_remote_validation: bool = False) -> None: ...

    def has_pending_remote_validation(self) -> bool: ...


class RemoteIdentityValidator(Protocol):
    def is_name_available(self, name: str) -> bool: ...


@dataclass(frozen=True)
class IdentityRecord:
    username: str
    pending_remote_validation: bool = False


class _EncryptedFileIdentityDAO:
    def __init__(self, vault: Optional[Vault] = None, save_path: Optional[str] = None) -> None:
        self._vault = vault or Vault()
        self._save_path = save_path or PathManager.get_user_save_path()

    def exists(self) -> bool:
        return os.path.exists(self._save_path)

    def load_name(self) -> Optional[str]:
        record = self._load_record()
        return record.username if record else None

    def save_name(self, name: str, pending_remote_validation: bool = False) -> None:
        record = {
            "username": name,
            "username_normalized": name.casefold(),
            "pending_remote_validation": pending_remote_validation,
        }
        encrypted = self._vault.encrypt(json.dumps(record))
        os.makedirs(os.path.dirname(self._save_path), exist_ok=True)
        with open(self._save_path, "wb") as file:
            file.write(encrypted)

    def has_pending_remote_validation(self) -> bool:
        record = self._load_record()
        return bool(record and record.pending_remote_validation)

    def _load_record(self) -> Optional[IdentityRecord]:
        if not self.exists():
            return None

        with open(self._save_path, "rb") as file:
            raw = file.read()

        payload = json.loads(self._vault.decrypt(raw))
        username = payload.get("username")
        if not isinstance(username, str) or not username:
            return None

        return IdentityRecord(
            username=username,
            pending_remote_validation=bool(payload.get("pending_remote_validation", False)),
        )


class _MongoIdentityValidator:
    COLLECTION_NAME = "users"

    def __init__(self, network_manager: "NetworkManager") -> None:
        self._network_manager = network_manager

    def is_name_available(self, name: str) -> bool:
        if not self._network_manager.is_online or self._network_manager.db is None:
            return True

        normalized = name.casefold()
        collection = self._network_manager.db[self.COLLECTION_NAME]
        existing_user = collection.find_one(
            {
                "$or": [
                    {"username_normalized": normalized},
                    {"username_lower": normalized},
                    {"username": {"$regex": f"^{re.escape(name)}$", "$options": "i"}},
                ]
            }
        )
        return existing_user is None


class IdentityManager:
    def __init__(
        self,
        network_manager: Optional["NetworkManager"] = None,
        screen_manager: Optional["ScreenManager"] = None,
        dao: Optional[IdentityDAO] = None,
        remote_validator: Optional[RemoteIdentityValidator] = None,
        prompt_provider: Optional[Callable[[Optional[str]], str]] = None,
    ) -> None:
        self._network_manager = network_manager
        self._screen_manager = screen_manager
        self._dao = dao or _EncryptedFileIdentityDAO()
        self._remote_validator = remote_validator or (
            _MongoIdentityValidator(network_manager) if network_manager is not None else None
        )
        self._prompt_provider = prompt_provider
        self._prompt_error: Optional[str] = None

    def get_or_create_identity(self) -> str:
        current_name = self._dao.load_name()
        if current_name:
            if not self._dao.has_pending_remote_validation() or not self._is_online():
                return current_name

            if self.validate_name(current_name):
                self._dao.save_name(current_name, pending_remote_validation=False)
                return current_name

            self._prompt_error = "Nome ja existe online. Escolha outro."

        while True:
            name = self._prompt_for_name()

            if self.validate_name(name):
                pending_remote_validation = not self._is_online()
                self._dao.save_name(name, pending_remote_validation=pending_remote_validation)
                return name

            self._prompt_error = (
                "Use 3-15 letras, numeros ou underscore. Nome deve ser unico."
            )

    def validate_name(self, name: str) -> bool:
        if not USERNAME_PATTERN.fullmatch(name):
            return False

        if self._remote_validator is None or not self._is_online():
            return True

        try:
            return self._remote_validator.is_name_available(name)
        except Exception:
            log.warning("Remote identity validation failed; allowing temporary offline identity", exc_info=True)
            return True

    def is_registered(self) -> bool:
        return self._dao.exists() and self._dao.load_name() is not None

    def _prompt_for_name(self) -> str:
        if self._prompt_provider is not None:
            return self._prompt_provider(self._prompt_error).strip()

        if self._screen_manager is None:
            raise RuntimeError("Identity prompt requires a ScreenManager or a prompt_provider.")

        return self._run_pygame_name_prompt()

    def _is_online(self) -> bool:
        return bool(self._network_manager and self._network_manager.is_online)

    def _run_pygame_name_prompt(self) -> str:
        text = ""
        clock = pygame.time.Clock()
        surface = self._screen_manager.surface

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise RuntimeError("Identity registration cancelled.")
                if event.type != pygame.KEYDOWN:
                    continue
                if event.key == pygame.K_RETURN and text:
                    return text.strip()
                if event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                    continue
                if event.key == pygame.K_ESCAPE:
                    raise RuntimeError("Identity registration cancelled.")
                if event.unicode and len(text) < 15:
                    candidate = text + event.unicode
                    if re.fullmatch(r"[A-Za-z0-9_]{0,15}", candidate):
                        text = candidate

            self._draw_name_prompt(surface, text)
            pygame.display.flip()
            clock.tick(SETTINGS.DISPLAY.FPS)

    def _draw_name_prompt(self, surface: pygame.Surface, text: str) -> None:
        surface.fill(SETTINGS.UI_THEME.BG_DARK)
        center_x = surface.get_width() // 2
        center_y = surface.get_height() // 2

        title_font = pygame.font.Font(None, SETTINGS.UI_TYPOGRAPHY.TITLE)
        body_font = pygame.font.Font(None, SETTINGS.UI_TYPOGRAPHY.BODY)
        small_font = pygame.font.Font(None, SETTINGS.UI_TYPOGRAPHY.SMALL)

        title = title_font.render("Nome de jogador", True, SETTINGS.UI_THEME.TEXT_PRIMARY)
        surface.blit(title, title.get_rect(center=(center_x, center_y - 105)))

        help_text = small_font.render("3-15: letras, numeros e _", True, SETTINGS.UI_THEME.TEXT_MUTED)
        surface.blit(help_text, help_text.get_rect(center=(center_x, center_y - 65)))

        input_width = min(380, surface.get_width() - 48)
        input_rect = pygame.Rect(0, 0, input_width, 46)
        input_rect.center = (center_x, center_y)
        pygame.draw.rect(surface, SETTINGS.UI_THEME.BG_MEDIUM, input_rect, border_radius=6)
        pygame.draw.rect(surface, SETTINGS.UI_THEME.PURPLE, input_rect, 2, border_radius=6)

        display_text = text or "_"
        rendered_input = body_font.render(display_text, True, SETTINGS.UI_THEME.YELLOW)
        surface.blit(rendered_input, rendered_input.get_rect(center=input_rect.center))

        if self._prompt_error:
            error = small_font.render(self._prompt_error, True, SETTINGS.UI_THEME.RED)
            surface.blit(error, error.get_rect(center=(center_x, center_y + 60)))

        action = small_font.render("Enter confirma", True, SETTINGS.UI_THEME.TEXT_MUTED)
        surface.blit(action, action.get_rect(center=(center_x, center_y + 100)))

from __future__ import annotations

from dataclasses import dataclass
import os

from ofertas.domain import DomainError
from ofertas.steam.importer import validate_steam_id


@dataclass(frozen=True, slots=True)
class SteamConfig:
    api_key: str
    steam_id: str

    @classmethod
    def from_environment(cls) -> SteamConfig:
        api_key = os.environ.get("STEAM_WEB_API_KEY", "").strip()
        steam_id = os.environ.get("STEAM_USER_ID", "").strip()
        if not api_key:
            raise DomainError("Falta la variable STEAM_WEB_API_KEY.")
        if not steam_id:
            raise DomainError("Falta la variable STEAM_USER_ID.")
        return cls(api_key=api_key, steam_id=validate_steam_id(steam_id))

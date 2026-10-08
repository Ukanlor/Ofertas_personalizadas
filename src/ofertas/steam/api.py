from __future__ import annotations

import json
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ofertas.steam.importer import SteamOwnedApp


class SteamApiError(RuntimeError):
    """Fallo de red o respuesta inválida de Steam sin exponer la clave."""


class SteamApi(Protocol):
    def get_owned_games(self, steam_id: str) -> list[SteamOwnedApp]: ...


class HttpSteamApi:
    _endpoint = (
        "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
    )

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def get_owned_games(self, steam_id: str) -> list[SteamOwnedApp]:
        input_json = json.dumps(
            {
                "steamid": steam_id,
                "include_appinfo": True,
                "include_played_free_games": True,
            },
            separators=(",", ":"),
        )
        query = urlencode(
            {"key": self._api_key, "format": "json", "input_json": input_json}
        )
        request = Request(
            f"{self._endpoint}?{query}",
            headers={"Accept": "application/json"},
            method="GET",
        )
        try:
            with urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8")
        except HTTPError as error:
            if error.code in (401, 403):
                raise SteamApiError(
                    "Steam rechazó la clave o el acceso a la biblioteca."
                ) from None
            raise SteamApiError("Steam rechazó la solicitud HTTP.") from None
        except (URLError, TimeoutError, OSError):
            raise SteamApiError("No se pudo conectar con Steam.") from None

        try:
            decoded = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise SteamApiError("Steam devolvió una respuesta no válida.") from None
        return parse_owned_games(decoded)


def parse_owned_games(payload: Any) -> list[SteamOwnedApp]:
    if not isinstance(payload, dict) or not isinstance(payload.get("response"), dict):
        raise SteamApiError("Steam devolvió una respuesta no válida.")
    response = payload["response"]
    games = response.get("games")
    if games is None:
        if response.get("game_count") == 0:
            return []
        raise SteamApiError(
            "Steam no devolvió la biblioteca; revisa la privacidad de los juegos."
        )
    if not isinstance(games, list):
        raise SteamApiError("Steam devolvió una biblioteca no válida.")

    parsed: list[SteamOwnedApp] = []
    for game in games:
        if not isinstance(game, dict):
            raise SteamApiError("Steam devolvió una entrada de biblioteca no válida.")
        app_id = required_integer(game, "appid")
        name = game.get("name")
        if not isinstance(name, str) or not name.strip():
            raise SteamApiError("Steam devolvió un juego sin nombre válido.")
        parsed.append(
            SteamOwnedApp(
                app_id=app_id,
                name=name,
                playtime_forever_minutes=required_integer(
                    game, "playtime_forever", allow_zero=True
                ),
                playtime_recent_minutes=optional_integer(game, "playtime_2weeks"),
                last_played_epoch=optional_integer(game, "rtime_last_played"),
            )
        )
    return parsed


def required_integer(
    values: dict[str, Any], key: str, *, allow_zero: bool = False
) -> int:
    value = values.get(key)
    minimum = 0 if allow_zero else 1
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise SteamApiError(f"Steam devolvió un valor inválido para {key}.")
    return value


def optional_integer(values: dict[str, Any], key: str) -> int:
    value = values.get(key, 0)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SteamApiError(f"Steam devolvió un valor inválido para {key}.")
    return value

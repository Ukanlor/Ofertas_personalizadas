from __future__ import annotations

import json
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


JsonObject = dict[str, Any]


class TelegramApiError(RuntimeError):
    """Fallo de red o respuesta inválida de Telegram sin exponer el token."""


class TelegramApi(Protocol):
    def get_me(self) -> JsonObject: ...

    def get_updates(
        self, *, offset: int | None, timeout: int = 30
    ) -> list[JsonObject]: ...

    def send_message(
        self,
        *,
        chat_id: int,
        text: str,
        reply_markup: JsonObject | None = None,
    ) -> JsonObject: ...

    def edit_message_text(
        self,
        *,
        chat_id: int,
        message_id: int,
        text: str,
        reply_markup: JsonObject | None = None,
    ) -> JsonObject: ...

    def answer_callback_query(
        self,
        *,
        callback_query_id: str,
        text: str = "",
        show_alert: bool = False,
    ) -> bool: ...


class HttpTelegramApi:
    def __init__(self, token: str) -> None:
        self._base_url = f"https://api.telegram.org/bot{token}"

    def get_me(self) -> JsonObject:
        return self._request("getMe", {})

    def get_updates(
        self, *, offset: int | None, timeout: int = 30
    ) -> list[JsonObject]:
        payload: JsonObject = {
            "timeout": timeout,
            "allowed_updates": ["message", "callback_query"],
        }
        if offset is not None:
            payload["offset"] = offset
        result = self._request("getUpdates", payload, timeout=timeout + 10)
        if not isinstance(result, list):
            raise TelegramApiError("Telegram devolvió una lista de updates inválida.")
        return result

    def send_message(
        self,
        *,
        chat_id: int,
        text: str,
        reply_markup: JsonObject | None = None,
    ) -> JsonObject:
        payload: JsonObject = {"chat_id": chat_id, "text": text}
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        return self._request("sendMessage", payload)

    def edit_message_text(
        self,
        *,
        chat_id: int,
        message_id: int,
        text: str,
        reply_markup: JsonObject | None = None,
    ) -> JsonObject:
        payload: JsonObject = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
        }
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        return self._request("editMessageText", payload)

    def answer_callback_query(
        self,
        *,
        callback_query_id: str,
        text: str = "",
        show_alert: bool = False,
    ) -> bool:
        result = self._request(
            "answerCallbackQuery",
            {
                "callback_query_id": callback_query_id,
                "text": text,
                "show_alert": show_alert,
            },
        )
        return bool(result)

    def _request(
        self, method: str, payload: JsonObject, *, timeout: int = 20
    ) -> Any:
        request = Request(
            f"{self._base_url}/{method}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8")
        except HTTPError as error:
            description = self._read_error_description(error)
            raise TelegramApiError(description) from None
        except (URLError, TimeoutError, OSError):
            raise TelegramApiError("No se pudo conectar con Telegram.") from None

        try:
            decoded = json.loads(body)
        except json.JSONDecodeError:
            raise TelegramApiError("Telegram devolvió una respuesta no válida.") from None
        if not isinstance(decoded, dict) or decoded.get("ok") is not True:
            description = (
                decoded.get("description", "Telegram rechazó la solicitud.")
                if isinstance(decoded, dict)
                else "Telegram rechazó la solicitud."
            )
            raise TelegramApiError(str(description))
        return decoded.get("result")

    @staticmethod
    def _read_error_description(error: HTTPError) -> str:
        try:
            decoded = json.loads(error.read().decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return "Telegram rechazó la solicitud HTTP."
        if isinstance(decoded, dict) and decoded.get("description"):
            return str(decoded["description"])
        return "Telegram rechazó la solicitud HTTP."

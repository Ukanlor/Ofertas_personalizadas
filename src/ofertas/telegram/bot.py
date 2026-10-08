from __future__ import annotations

from dataclasses import dataclass
import sqlite3
import time
from typing import Any, Callable

from ofertas.domain import DomainError
from ofertas.persistence.telegram_state import TelegramStateRepository
from ofertas.services import CatalogService
from ofertas.telegram.api import JsonObject, TelegramApi, TelegramApiError
from ofertas.telegram.cards import build_game_card


HELP_TEXT = (
    "Ofertas personalizadas\n\n"
    "/search texto - buscar un juego y abrir su tarjeta\n"
    "/help - mostrar esta ayuda\n\n"
    "En cada tarjeta puedes puntuar 1-10, ignorar, reactivar o marcar una "
    "variante como poseída. Todavía no se consultan precios ni se envían ofertas."
)


@dataclass(frozen=True, slots=True)
class CallbackAction:
    kind: str
    target_id: int
    value: int | bool | None = None


class TelegramPreferenceBot:
    def __init__(
        self,
        *,
        api: TelegramApi,
        catalog: CatalogService,
        state: TelegramStateRepository,
        authorized_user_id: int,
    ) -> None:
        self.api = api
        self.catalog = catalog
        self.state = state
        self.authorized_user_id = authorized_user_id

    def process_update(self, update: JsonObject) -> None:
        message = update.get("message")
        if isinstance(message, dict):
            self._process_message(message)
            return
        callback = update.get("callback_query")
        if isinstance(callback, dict):
            self._process_callback(callback)

    def _process_message(self, message: JsonObject) -> None:
        sender = message.get("from")
        chat = message.get("chat")
        if not isinstance(sender, dict) or not isinstance(chat, dict):
            return
        if not self._is_authorized(sender, chat):
            return
        text = message.get("text")
        if not isinstance(text, str):
            return
        chat_id = int(chat["id"])
        command, argument = parse_command(text)
        if command in {"/start", "/help"}:
            self.api.send_message(chat_id=chat_id, text=HELP_TEXT)
        elif command == "/search":
            self._send_search_results(chat_id, argument)
        elif command.startswith("/"):
            self.api.send_message(
                chat_id=chat_id,
                text="Comando no reconocido. Usa /help para ver las opciones.",
            )

    def _send_search_results(self, chat_id: int, query: str) -> None:
        if not query:
            self.api.send_message(chat_id=chat_id, text="Uso: /search texto")
            return
        games = self.catalog.search_games(query)
        if not games:
            self.api.send_message(chat_id=chat_id, text="No encontré juegos.")
            return
        for game in games[:5]:
            card = build_game_card(game)
            self.api.send_message(
                chat_id=chat_id,
                text=card.text,
                reply_markup=card.reply_markup,
            )
        if len(games) > 5:
            self.api.send_message(
                chat_id=chat_id,
                text="Hay más resultados; usa una búsqueda más específica.",
            )

    def _process_callback(self, callback: JsonObject) -> None:
        callback_id = callback.get("id")
        sender = callback.get("from")
        message = callback.get("message")
        data = callback.get("data")
        if not isinstance(callback_id, str):
            return
        sender_id = sender.get("id") if isinstance(sender, dict) else None
        if sender_id != self.authorized_user_id:
            self.api.answer_callback_query(
                callback_query_id=callback_id,
                text="Usuario no autorizado.",
                show_alert=True,
            )
            return
        if not isinstance(message, dict) or not isinstance(data, str):
            self.api.answer_callback_query(
                callback_query_id=callback_id,
                text="Acción no válida.",
                show_alert=True,
            )
            return
        chat = message.get("chat")
        message_id = message.get("message_id")
        if (
            not isinstance(chat, dict)
            or chat.get("type") != "private"
            or chat.get("id") != self.authorized_user_id
            or not isinstance(message_id, int)
        ):
            self.api.answer_callback_query(
                callback_query_id=callback_id,
                text="Esta acción solo funciona en el chat privado.",
                show_alert=True,
            )
            return
        if self.state.callback_was_processed(callback_id):
            self.api.answer_callback_query(
                callback_query_id=callback_id, text="La acción ya estaba aplicada."
            )
            return

        try:
            action = parse_callback_data(data)
            game_id = self._apply_action(action)
        except DomainError as error:
            self.api.answer_callback_query(
                callback_query_id=callback_id,
                text=str(error),
                show_alert=True,
            )
            return
        except sqlite3.Error:
            self.api.answer_callback_query(
                callback_query_id=callback_id,
                text="No se pudo guardar el cambio.",
                show_alert=True,
            )
            return

        recorded = self.state.record_callback(
            callback_id,
            user_id=self.authorized_user_id,
            action=action.kind,
            target_id=action.target_id,
        )
        if not recorded:
            self.api.answer_callback_query(
                callback_query_id=callback_id, text="La acción ya estaba aplicada."
            )
            return

        game = self.catalog.get_game(game_id)
        card = build_game_card(game)
        try:
            self.api.edit_message_text(
                chat_id=int(chat["id"]),
                message_id=message_id,
                text=card.text,
                reply_markup=card.reply_markup,
            )
        except TelegramApiError:
            self.api.answer_callback_query(
                callback_query_id=callback_id,
                text="Guardado; usa /search para actualizar la tarjeta.",
                show_alert=True,
            )
            return
        self.api.answer_callback_query(
            callback_query_id=callback_id, text="Cambio guardado."
        )

    def _apply_action(self, action: CallbackAction) -> int:
        if action.kind == "rate":
            self.catalog.set_interest(action.target_id, int(action.value))
            return action.target_id
        if action.kind == "ignore":
            self.catalog.ignore(action.target_id)
            return action.target_id
        if action.kind == "reactivate":
            self.catalog.reactivate(action.target_id)
            return action.target_id
        if action.kind == "owned":
            variant = self.catalog.get_variant(action.target_id)
            self.catalog.set_owned(action.target_id, bool(action.value))
            return variant.game_id
        raise DomainError("Acción no reconocida.")

    def _is_authorized(self, sender: JsonObject, chat: JsonObject) -> bool:
        return (
            sender.get("id") == self.authorized_user_id
            and chat.get("type") == "private"
            and chat.get("id") == self.authorized_user_id
        )


class TelegramPollingRunner:
    def __init__(
        self,
        *,
        api: TelegramApi,
        bot: TelegramPreferenceBot,
        state: TelegramStateRepository,
        status: Callable[[str], None] = print,
    ) -> None:
        self.api = api
        self.bot = bot
        self.state = state
        self.status = status

    def process_batch(self, updates: list[JsonObject]) -> int:
        processed = 0
        for update in sorted(updates, key=lambda item: int(item.get("update_id", -1))):
            update_id = update.get("update_id")
            if not isinstance(update_id, int):
                continue
            self.bot.process_update(update)
            self.state.mark_update_processed(update_id)
            processed += 1
        return processed

    def run_forever(self) -> None:
        self.status("Bot iniciado. Presiona Ctrl+C para detenerlo.")
        while True:
            try:
                updates = self.api.get_updates(offset=self.state.get_next_offset())
                self.process_batch(updates)
            except TelegramApiError as error:
                self.status(f"Error de Telegram: {error}. Reintentando en 3 segundos.")
                time.sleep(3)


def parse_command(text: str) -> tuple[str, str]:
    command_text, separator, argument = text.strip().partition(" ")
    command = command_text.split("@", 1)[0].casefold()
    return command, argument.strip() if separator else ""


def parse_callback_data(data: str) -> CallbackAction:
    parts = data.split(":")
    try:
        if len(parts) == 3 and parts[0] == "rate":
            game_id = positive_int(parts[1])
            score = int(parts[2])
            if not 1 <= score <= 10:
                raise ValueError
            return CallbackAction("rate", game_id, score)
        if len(parts) == 2 and parts[0] in {"ignore", "reactivate"}:
            return CallbackAction(parts[0], positive_int(parts[1]))
        if len(parts) == 3 and parts[0] == "own" and parts[2] in {"set", "unset"}:
            return CallbackAction("owned", positive_int(parts[1]), parts[2] == "set")
    except ValueError:
        pass
    raise DomainError("Acción no válida.")


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise ValueError
    return parsed

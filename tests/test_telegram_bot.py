from pathlib import Path
import tempfile
import unittest
from typing import Any

from ofertas.persistence.database import Database
from ofertas.persistence.repositories import SqliteGameRepository
from ofertas.persistence.telegram_state import TelegramStateRepository
from ofertas.services import CatalogService
from ofertas.telegram.api import JsonObject, TelegramApiError
from ofertas.telegram.bot import TelegramPollingRunner, TelegramPreferenceBot


class FakeTelegramApi:
    def __init__(self) -> None:
        self.sent_messages: list[JsonObject] = []
        self.edited_messages: list[JsonObject] = []
        self.callback_answers: list[JsonObject] = []
        self.fail_edits = False

    def get_me(self) -> JsonObject:
        return {"id": 999, "username": "ofertas_test_bot"}

    def get_updates(
        self, *, offset: int | None, timeout: int = 30
    ) -> list[JsonObject]:
        return []

    def send_message(
        self,
        *,
        chat_id: int,
        text: str,
        reply_markup: JsonObject | None = None,
    ) -> JsonObject:
        call = {"chat_id": chat_id, "text": text, "reply_markup": reply_markup}
        self.sent_messages.append(call)
        return {"message_id": len(self.sent_messages), **call}

    def edit_message_text(
        self,
        *,
        chat_id: int,
        message_id: int,
        text: str,
        reply_markup: JsonObject | None = None,
    ) -> JsonObject:
        if self.fail_edits:
            raise TelegramApiError("fallo simulado")
        call = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "reply_markup": reply_markup,
        }
        self.edited_messages.append(call)
        return call

    def answer_callback_query(
        self,
        *,
        callback_query_id: str,
        text: str = "",
        show_alert: bool = False,
    ) -> bool:
        self.callback_answers.append(
            {
                "callback_query_id": callback_query_id,
                "text": text,
                "show_alert": show_alert,
            }
        )
        return True


class TelegramPreferenceBotTests(unittest.TestCase):
    USER_ID = 12345

    def setUp(self) -> None:
        temp_root = Path(__file__).resolve().parent.parent / ".test-tmp"
        temp_root.mkdir(exist_ok=True)
        self.temp_dir = tempfile.TemporaryDirectory(dir=temp_root)
        self.database = Database(Path(self.temp_dir.name) / "telegram-bot.db")
        self.database.migrate()
        self.catalog = CatalogService(SqliteGameRepository(self.database))
        self.game_id = self.catalog.add_game("Hades")
        self.steam_id = self.catalog.add_variant(
            self.game_id, platform="pc", format="digital", region="cl", drm="steam"
        )
        self.switch_id = self.catalog.add_variant(
            self.game_id,
            platform="nintendo switch",
            format="cartucho",
            region="cl",
            condition="nuevo",
        )
        self.state = TelegramStateRepository(self.database)
        self.api = FakeTelegramApi()
        self.bot = TelegramPreferenceBot(
            api=self.api,
            catalog=self.catalog,
            state=self.state,
            authorized_user_id=self.USER_ID,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_search_sends_a_card_with_interest_and_variant_buttons(self) -> None:
        self.bot.process_update(self.message_update("/search Hades"))

        self.assertEqual(len(self.api.sent_messages), 1)
        card = self.api.sent_messages[0]
        self.assertIn("Hades", card["text"])
        self.assertIn("Interés: sin puntuar", card["text"])
        callback_data = [
            button["callback_data"]
            for row in card["reply_markup"]["inline_keyboard"]
            for button in row
        ]
        self.assertIn(f"rate:{self.game_id}:8", callback_data)
        self.assertIn(f"ignore:{self.game_id}", callback_data)
        self.assertIn(f"own:{self.steam_id}:set", callback_data)
        self.assertIn(f"own:{self.switch_id}:set", callback_data)

    def test_unauthorized_message_is_ignored(self) -> None:
        update = self.message_update("/search Hades", user_id=99999)

        self.bot.process_update(update)

        self.assertEqual(self.api.sent_messages, [])

    def test_unauthorized_callback_is_answered_without_changes(self) -> None:
        callback = self.callback_update("callback-unauthorized", f"rate:{self.game_id}:8")
        callback["callback_query"]["from"]["id"] = 99999

        self.bot.process_update(callback)

        self.assertIsNone(self.catalog.get_game(self.game_id).interest_score)
        self.assertEqual(self.api.edited_messages, [])
        self.assertEqual(
            self.api.callback_answers[-1]["text"], "Usuario no autorizado."
        )

    def test_malformed_callback_message_is_rejected_before_saving(self) -> None:
        callback = self.callback_update("callback-malformed", f"rate:{self.game_id}:8")
        del callback["callback_query"]["message"]["message_id"]

        self.bot.process_update(callback)

        self.assertIsNone(self.catalog.get_game(self.game_id).interest_score)
        self.assertEqual(self.api.edited_messages, [])
        self.assertTrue(self.api.callback_answers[-1]["show_alert"])

    def test_rate_callback_updates_and_edits_the_same_card(self) -> None:
        callback = self.callback_update("callback-1", f"rate:{self.game_id}:8")

        self.bot.process_update(callback)

        self.assertEqual(self.catalog.get_game(self.game_id).interest_score, 8)
        self.assertEqual(len(self.api.edited_messages), 1)
        self.assertIn("Interés: 8/10", self.api.edited_messages[0]["text"])
        self.assertEqual(self.api.callback_answers[-1]["text"], "Cambio guardado.")

    def test_repeated_callback_does_not_repeat_the_edit(self) -> None:
        callback = self.callback_update("callback-repeat", f"rate:{self.game_id}:8")

        self.bot.process_update(callback)
        self.bot.process_update(callback)

        self.assertEqual(len(self.api.edited_messages), 1)
        self.assertEqual(
            self.api.callback_answers[-1]["text"], "La acción ya estaba aplicada."
        )

    def test_ownership_callback_only_changes_the_selected_variant(self) -> None:
        callback = self.callback_update("callback-owned", f"own:{self.steam_id}:set")

        self.bot.process_update(callback)

        game = self.catalog.get_game(self.game_id)
        steam = next(v for v in game.variants if v.id == self.steam_id)
        switch = next(v for v in game.variants if v.id == self.switch_id)
        self.assertTrue(steam.owned)
        self.assertFalse(switch.owned)

    def test_edit_failure_keeps_the_saved_preference(self) -> None:
        self.api.fail_edits = True
        callback = self.callback_update("callback-edit-fails", f"rate:{self.game_id}:9")

        self.bot.process_update(callback)

        self.assertEqual(self.catalog.get_game(self.game_id).interest_score, 9)
        self.assertIn("Guardado", self.api.callback_answers[-1]["text"])
        self.assertTrue(self.api.callback_answers[-1]["show_alert"])

    def test_invalid_callback_is_rejected_without_changes(self) -> None:
        callback = self.callback_update("callback-invalid", "rate:1:500")

        self.bot.process_update(callback)

        self.assertIsNone(self.catalog.get_game(self.game_id).interest_score)
        self.assertEqual(self.api.edited_messages, [])
        self.assertTrue(self.api.callback_answers[-1]["show_alert"])

    def test_runner_records_offset_only_after_processing(self) -> None:
        runner = TelegramPollingRunner(
            api=self.api, bot=self.bot, state=self.state, status=lambda _: None
        )

        processed = runner.process_batch(
            [self.message_update("/help", update_id=41)]
        )

        self.assertEqual(processed, 1)
        self.assertEqual(self.state.get_next_offset(), 42)

    def message_update(
        self, text: str, *, user_id: int | None = None, update_id: int = 1
    ) -> JsonObject:
        sender_id = self.USER_ID if user_id is None else user_id
        return {
            "update_id": update_id,
            "message": {
                "message_id": 10,
                "from": {"id": sender_id},
                "chat": {"id": sender_id, "type": "private"},
                "text": text,
            },
        }

    def callback_update(self, callback_id: str, data: str) -> JsonObject:
        return {
            "update_id": 2,
            "callback_query": {
                "id": callback_id,
                "from": {"id": self.USER_ID},
                "data": data,
                "message": {
                    "message_id": 22,
                    "chat": {"id": self.USER_ID, "type": "private"},
                },
            },
        }


if __name__ == "__main__":
    unittest.main()

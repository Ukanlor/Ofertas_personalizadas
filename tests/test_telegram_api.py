from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from ofertas.telegram.api import HttpTelegramApi, TelegramApiError


class FakeHttpResponse:
    def __init__(self, payload: object) -> None:
        self.body = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> FakeHttpResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


class HttpTelegramApiTests(unittest.TestCase):
    @patch("ofertas.telegram.api.urlopen")
    def test_send_message_posts_utf8_json(self, mocked_urlopen: object) -> None:
        mocked_urlopen.return_value = FakeHttpResponse(  # type: ignore[attr-defined]
            {"ok": True, "result": {"message_id": 9}}
        )
        api = HttpTelegramApi("fictitious-token")

        result = api.send_message(chat_id=123, text="Interés actualizado")

        self.assertEqual(result["message_id"], 9)
        request = mocked_urlopen.call_args.args[0]  # type: ignore[attr-defined]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload, {"chat_id": 123, "text": "Interés actualizado"})
        self.assertEqual(request.get_method(), "POST")

    @patch("ofertas.telegram.api.urlopen")
    def test_get_updates_requires_a_list_result(self, mocked_urlopen: object) -> None:
        mocked_urlopen.return_value = FakeHttpResponse(  # type: ignore[attr-defined]
            {"ok": True, "result": {"unexpected": True}}
        )
        api = HttpTelegramApi("fictitious-token")

        with self.assertRaises(TelegramApiError):
            api.get_updates(offset=None)

    @patch("ofertas.telegram.api.urlopen")
    def test_api_error_does_not_include_the_token(self, mocked_urlopen: object) -> None:
        mocked_urlopen.return_value = FakeHttpResponse(  # type: ignore[attr-defined]
            {"ok": False, "description": "Unauthorized"}
        )
        token = "fictitious-secret-token"
        api = HttpTelegramApi(token)

        with self.assertRaises(TelegramApiError) as raised:
            api.get_me()

        self.assertEqual(str(raised.exception), "Unauthorized")
        self.assertNotIn(token, str(raised.exception))


if __name__ == "__main__":
    unittest.main()

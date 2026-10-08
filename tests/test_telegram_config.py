import os
import unittest
from unittest.mock import patch

from ofertas.domain import DomainError
from ofertas.telegram.config import TelegramConfig, token_from_environment


class TelegramConfigTests(unittest.TestCase):
    def test_complete_environment_is_loaded(self) -> None:
        with patch.dict(
            os.environ,
            {
                "TELEGRAM_BOT_TOKEN": "secret-token",
                "TELEGRAM_ALLOWED_USER_ID": "12345",
            },
            clear=True,
        ):
            config = TelegramConfig.from_environment()

        self.assertEqual(config.token, "secret-token")
        self.assertEqual(config.authorized_user_id, 12345)

    def test_missing_token_is_rejected(self) -> None:
        with patch.dict(
            os.environ, {"TELEGRAM_ALLOWED_USER_ID": "12345"}, clear=True
        ):
            with self.assertRaises(DomainError):
                TelegramConfig.from_environment()

    def test_invalid_user_id_is_rejected(self) -> None:
        with patch.dict(
            os.environ,
            {
                "TELEGRAM_BOT_TOKEN": "secret-token",
                "TELEGRAM_ALLOWED_USER_ID": "not-a-number",
            },
            clear=True,
        ):
            with self.assertRaises(DomainError):
                TelegramConfig.from_environment()

    def test_identify_only_requires_the_token(self) -> None:
        with patch.dict(
            os.environ, {"TELEGRAM_BOT_TOKEN": "secret-token"}, clear=True
        ):
            self.assertEqual(token_from_environment(), "secret-token")


if __name__ == "__main__":
    unittest.main()

import os
import unittest
from unittest.mock import patch

from ofertas.domain import DomainError
from ofertas.steam.config import SteamConfig


class SteamConfigTests(unittest.TestCase):
    def test_complete_environment_is_loaded(self) -> None:
        with patch.dict(
            os.environ,
            {
                "STEAM_WEB_API_KEY": "secret-key",
                "STEAM_USER_ID": "76561198000000000",
            },
            clear=True,
        ):
            config = SteamConfig.from_environment()

        self.assertEqual(config.api_key, "secret-key")
        self.assertEqual(config.steam_id, "76561198000000000")

    def test_missing_key_is_rejected(self) -> None:
        with patch.dict(
            os.environ, {"STEAM_USER_ID": "76561198000000000"}, clear=True
        ):
            with self.assertRaises(DomainError):
                SteamConfig.from_environment()

    def test_invalid_steam_id_is_rejected(self) -> None:
        with patch.dict(
            os.environ,
            {"STEAM_WEB_API_KEY": "secret-key", "STEAM_USER_ID": "profile-name"},
            clear=True,
        ):
            with self.assertRaises(DomainError):
                SteamConfig.from_environment()


if __name__ == "__main__":
    unittest.main()

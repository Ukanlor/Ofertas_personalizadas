from __future__ import annotations

import json
from urllib.error import URLError
from urllib.parse import parse_qs, urlparse
import unittest
from unittest.mock import patch

from ofertas.steam.api import HttpSteamApi, SteamApiError, parse_owned_games


class FakeHttpResponse:
    def __init__(self, payload: object) -> None:
        self.body = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> FakeHttpResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


class HttpSteamApiTests(unittest.TestCase):
    @patch("ofertas.steam.api.urlopen")
    def test_owned_games_requests_appinfo_and_played_free_games(
        self, mocked_urlopen: object
    ) -> None:
        mocked_urlopen.return_value = FakeHttpResponse(  # type: ignore[attr-defined]
            {
                "response": {
                    "game_count": 2,
                    "games": [
                        {
                            "appid": 1145360,
                            "name": "Hades",
                            "playtime_forever": 600,
                            "playtime_2weeks": 20,
                            "rtime_last_played": 1_700_000_000,
                        },
                        {
                            "appid": 999,
                            "name": "Nunca abierto",
                            "playtime_forever": 0,
                        },
                    ],
                }
            }
        )
        api = HttpSteamApi("fictitious-key")

        games = api.get_owned_games("76561198000000000")

        self.assertEqual(len(games), 2)
        self.assertEqual(games[0].name, "Hades")
        self.assertEqual(games[1].playtime_forever_minutes, 0)
        request = mocked_urlopen.call_args.args[0]  # type: ignore[attr-defined]
        query = parse_qs(urlparse(request.full_url).query)
        self.assertEqual(query["key"], ["fictitious-key"])
        request_data = json.loads(query["input_json"][0])
        self.assertEqual(request_data["steamid"], "76561198000000000")
        self.assertTrue(request_data["include_appinfo"])
        self.assertTrue(request_data["include_played_free_games"])

    def test_hidden_library_is_reported_clearly(self) -> None:
        with self.assertRaisesRegex(SteamApiError, "privacidad"):
            parse_owned_games({"response": {}})

    def test_zero_game_library_is_valid(self) -> None:
        self.assertEqual(
            parse_owned_games({"response": {"game_count": 0}}), []
        )

    def test_malformed_game_is_rejected(self) -> None:
        with self.assertRaises(SteamApiError):
            parse_owned_games(
                {
                    "response": {
                        "game_count": 1,
                        "games": [{"appid": 10, "name": "Juego"}],
                    }
                }
            )

    @patch("ofertas.steam.api.urlopen", side_effect=URLError("network"))
    def test_network_error_does_not_include_the_key(
        self, mocked_urlopen: object
    ) -> None:
        key = "fictitious-secret-key"
        api = HttpSteamApi(key)

        with self.assertRaises(SteamApiError) as raised:
            api.get_owned_games("76561198000000000")

        self.assertNotIn(key, str(raised.exception))


if __name__ == "__main__":
    unittest.main()

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ofertas.cli import main
from ofertas.persistence.database import Database
from ofertas.steam.config import SteamConfig
from ofertas.steam.importer import SteamOwnedApp


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_root = Path(__file__).resolve().parent.parent / ".test-tmp"
        temp_root.mkdir(exist_ok=True)
        self.temp_dir = tempfile.TemporaryDirectory(dir=temp_root)
        self.db_path = Path(self.temp_dir.name) / "cli.db"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_cli(self, *arguments: str) -> tuple[int, str, str]:
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(["--db", str(self.db_path), *arguments])
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_complete_cli_example(self) -> None:
        self.assertEqual(self.run_cli("db", "init")[0], 0)
        self.assertIn("Juego creado: 1", self.run_cli("game", "add", "Hades")[1])
        self.assertIn(
            "Variante creada: 1",
            self.run_cli(
                "variant",
                "add",
                "1",
                "--platform",
                "PC",
                "--format",
                "digital",
                "--region",
                "CL",
                "--drm",
                "Steam",
            )[1],
        )
        self.assertIn(
            "Variante creada: 2",
            self.run_cli(
                "variant",
                "add",
                "1",
                "--platform",
                "Nintendo Switch",
                "--format",
                "cartucho",
                "--region",
                "CL",
                "--condition",
                "nuevo",
            )[1],
        )
        self.assertEqual(self.run_cli("interest", "set", "1", "8")[0], 0)
        self.assertEqual(self.run_cli("owned", "set", "1")[0], 0)

        exit_code, output, error = self.run_cli("game", "show", "1")

        self.assertEqual(exit_code, 0)
        self.assertEqual(error, "")
        self.assertIn("Gusto: sin puntuar", output)
        self.assertIn("Interés de compra: interés 8/10", output)
        self.assertIn("pc / base / digital / cl / steam - poseída (manual)", output)
        self.assertIn("nintendo-switch / base / cartucho / cl / nuevo - no poseída", output)

    def test_invalid_interest_returns_a_user_error(self) -> None:
        self.run_cli("game", "add", "Hades")

        exit_code, output, error = self.run_cli("interest", "set", "1", "11")

        self.assertEqual(exit_code, 2)
        self.assertEqual(output, "")
        self.assertIn("entre 0 y 10", error)

    def test_interest_zero_uses_the_ignored_message(self) -> None:
        self.run_cli("game", "add", "Hades")

        exit_code, output, error = self.run_cli("interest", "set", "1", "0")

        self.assertEqual(exit_code, 0)
        self.assertEqual(error, "")
        self.assertIn("Juego ignorado", output)

    def test_taste_and_purchase_interest_can_be_changed_separately(self) -> None:
        self.run_cli("game", "add", "Hades")
        self.run_cli("interest", "set", "1", "8")

        taste_code, taste_output, taste_error = self.run_cli(
            "taste", "set", "1", "9"
        )
        clear_code, clear_output, clear_error = self.run_cli(
            "interest", "clear", "1"
        )
        show_code, show_output, show_error = self.run_cli("game", "show", "1")

        self.assertEqual((taste_code, clear_code, show_code), (0, 0, 0))
        self.assertEqual(taste_error + clear_error + show_error, "")
        self.assertIn("Gusto actualizado: 9/10", taste_output)
        self.assertIn("Interés de compra eliminado", clear_output)
        self.assertIn("Gusto: 9/10", show_output)
        self.assertIn("Interés de compra: sin puntuar", show_output)

    @patch("ofertas.cli.HttpSteamApi")
    @patch("ofertas.cli.SteamConfig.from_environment")
    def test_steam_check_does_not_write_games(
        self, mocked_config: object, mocked_api_class: object
    ) -> None:
        mocked_config.return_value = SteamConfig(  # type: ignore[attr-defined]
            api_key="fictitious-key", steam_id="76561198000000000"
        )
        mocked_api_class.return_value.get_owned_games.return_value = [  # type: ignore[attr-defined]
            SteamOwnedApp(10, "Jugado", 60),
            SteamOwnedApp(11, "Sin abrir", 0),
        ]

        exit_code, output, error = self.run_cli("steam", "check")

        self.assertEqual(exit_code, 0)
        self.assertEqual(error, "")
        self.assertIn("jugados alguna vez: 1", output)
        self.assertIn("omitidos sin uso: 1", output)
        with Database(self.db_path).connection() as connection:
            count = connection.execute("SELECT count(*) FROM games").fetchone()[0]
        self.assertEqual(count, 0)

    @patch("ofertas.cli.HttpSteamApi")
    @patch("ofertas.cli.SteamConfig.from_environment")
    def test_steam_import_writes_only_played_games(
        self, mocked_config: object, mocked_api_class: object
    ) -> None:
        mocked_config.return_value = SteamConfig(  # type: ignore[attr-defined]
            api_key="fictitious-key", steam_id="76561198000000000"
        )
        mocked_api_class.return_value.get_owned_games.return_value = [  # type: ignore[attr-defined]
            SteamOwnedApp(10, "Jugado", 60),
            SteamOwnedApp(11, "Sin abrir", 0),
        ]

        exit_code, output, error = self.run_cli("steam", "import")

        self.assertEqual(exit_code, 0)
        self.assertEqual(error, "")
        self.assertIn("importados: 1", output)
        self.assertIn("omitidos sin uso: 1", output)
        with Database(self.db_path).connection() as connection:
            games = connection.execute(
                "SELECT canonical_title FROM games"
            ).fetchall()
        self.assertEqual([row["canonical_title"] for row in games], ["Jugado"])

    @patch("ofertas.cli.HttpSteamApi")
    @patch("ofertas.cli.SteamConfig.from_environment")
    def test_steam_preview_lists_only_played_games_without_writing(
        self, mocked_config: object, mocked_api_class: object
    ) -> None:
        mocked_config.return_value = SteamConfig(  # type: ignore[attr-defined]
            api_key="fictitious-key", steam_id="76561198000000000"
        )
        mocked_api_class.return_value.get_owned_games.return_value = [  # type: ignore[attr-defined]
            SteamOwnedApp(10, "Zeta", 90),
            SteamOwnedApp(11, "Sin abrir", 0),
            SteamOwnedApp(12, "Alpha", 30),
        ]

        exit_code, output, error = self.run_cli("steam", "preview")

        self.assertEqual(exit_code, 0)
        self.assertEqual(error, "")
        self.assertIn("Juegos que se importarían: 2", output)
        self.assertIn("12: Alpha - 0.5 h", output)
        self.assertIn("10: Zeta - 1.5 h", output)
        self.assertNotIn("Sin abrir", output)
        self.assertLess(output.index("Alpha"), output.index("Zeta"))
        with Database(self.db_path).connection() as connection:
            count = connection.execute("SELECT count(*) FROM games").fetchone()[0]
        self.assertEqual(count, 0)

    def test_steam_exclusions_do_not_require_credentials(self) -> None:
        exit_code, output, error = self.run_cli(
            "steam",
            "exclude",
            "add",
            "50",
            "Herramienta",
            "--reason",
            "No es un juego",
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(error, "")
        self.assertIn("AppID 50", output)
        list_code, list_output, list_error = self.run_cli(
            "steam", "exclude", "list"
        )
        self.assertEqual(list_code, 0)
        self.assertEqual(list_error, "")
        self.assertIn("50: Herramienta - No es un juego", list_output)

        remove_code, remove_output, remove_error = self.run_cli(
            "steam", "exclude", "remove", "50"
        )
        self.assertEqual(remove_code, 0)
        self.assertEqual(remove_error, "")
        self.assertIn("Exclusión eliminada", remove_output)


if __name__ == "__main__":
    unittest.main()

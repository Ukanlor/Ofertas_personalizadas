from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import unittest

from ofertas.cli import main


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
        self.assertIn("Interés: interés 8/10", output)
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


if __name__ == "__main__":
    unittest.main()

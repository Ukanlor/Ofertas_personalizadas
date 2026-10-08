from pathlib import Path
import tempfile
import unittest

from ofertas.domain import ConflictError, DomainError
from ofertas.persistence.database import Database
from ofertas.persistence.repositories import SqliteGameRepository
from ofertas.persistence.steam import SqliteSteamRepository
from ofertas.services import CatalogService
from ofertas.steam.importer import SteamLibraryImporter, SteamOwnedApp


class SteamLibraryImporterTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_root = Path(__file__).resolve().parent.parent / ".test-tmp"
        temp_root.mkdir(exist_ok=True)
        self.temp_dir = tempfile.TemporaryDirectory(dir=temp_root)
        self.database = Database(Path(self.temp_dir.name) / "steam.db")
        self.database.migrate()
        self.catalog = CatalogService(SqliteGameRepository(self.database))
        self.importer = SteamLibraryImporter(SqliteSteamRepository(self.database))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_import_reuses_manual_game_and_skips_unplayed_apps(self) -> None:
        hades_id = self.catalog.add_game("Hades")
        hades_variant_id = self.catalog.add_variant(
            hades_id,
            platform="pc",
            edition="base",
            format="digital",
            region="cl",
            drm="steam",
        )
        self.catalog.set_interest(hades_id, 8)
        self.catalog.set_owned(hades_variant_id, True, "manual")

        result = self.importer.import_library(
            "76561198000000000",
            [
                SteamOwnedApp(1145360, "Hades", 600, 20, 1_700_000_000),
                SteamOwnedApp(504230, "Celeste", 90),
                SteamOwnedApp(999, "Nunca abierto", 0),
            ],
        )

        self.assertEqual(result.received, 3)
        self.assertEqual(result.imported, 2)
        self.assertEqual(result.skipped_unplayed, 1)
        self.assertEqual(result.created_games, 1)
        hades = self.catalog.get_game(hades_id)
        self.assertEqual(hades.interest_score, 8)
        self.assertEqual(len(hades.variants), 1)
        self.assertEqual(hades.variants[0].ownership_source, "manual")
        celeste = self.catalog.search_games("Celeste")[0]
        self.assertIsNone(celeste.interest_score)
        self.assertTrue(celeste.variants[0].owned)
        self.assertEqual(celeste.variants[0].ownership_source, "steam")

        with self.database.connection() as connection:
            apps = connection.execute(
                """
                SELECT app_id, playtime_forever_minutes
                FROM steam_apps ORDER BY app_id
                """
            ).fetchall()
        self.assertEqual(
            [(row["app_id"], row["playtime_forever_minutes"]) for row in apps],
            [(504230, 90), (1145360, 600)],
        )

    def test_reimport_updates_activity_without_duplicates(self) -> None:
        first = [SteamOwnedApp(504230, "Celeste", 90)]
        second = [SteamOwnedApp(504230, "Celeste", 150, 60)]

        self.importer.import_library("76561198000000000", first)
        result = self.importer.import_library("76561198000000000", second)

        self.assertEqual(result.created_games, 0)
        with self.database.connection() as connection:
            app = connection.execute(
                """
                SELECT playtime_forever_minutes, playtime_recent_minutes
                FROM steam_apps WHERE app_id = 504230
                """
            ).fetchone()
            counts = connection.execute(
                """
                SELECT
                    (SELECT count(*) FROM games) AS games,
                    (SELECT count(*) FROM variants) AS variants
                """
            ).fetchone()
        self.assertEqual(app["playtime_forever_minutes"], 150)
        self.assertEqual(app["playtime_recent_minutes"], 60)
        self.assertEqual((counts["games"], counts["variants"]), (1, 1))

    def test_different_profile_is_rejected_without_partial_changes(self) -> None:
        self.importer.import_library(
            "76561198000000000", [SteamOwnedApp(504230, "Celeste", 90)]
        )

        with self.assertRaises(ConflictError):
            self.importer.import_library(
                "76561198000000001", [SteamOwnedApp(1145360, "Hades", 60)]
            )

        self.assertEqual(self.catalog.search_games("Hades"), ())

    def test_invalid_or_duplicate_api_data_is_rejected(self) -> None:
        with self.assertRaises(DomainError):
            self.importer.import_library(
                "76561198000000000", [SteamOwnedApp(0, "Inválido", 10)]
            )
        with self.assertRaises(DomainError):
            self.importer.import_library(
                "76561198000000000",
                [
                    SteamOwnedApp(10, "Juego", 10),
                    SteamOwnedApp(10, "Juego repetido", 20),
                ],
            )


if __name__ == "__main__":
    unittest.main()

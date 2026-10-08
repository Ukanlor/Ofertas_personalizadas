from pathlib import Path
import sqlite3
import tempfile
import unittest

from ofertas.persistence.database import Database, utc_now


class MigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_root = Path(__file__).resolve().parent.parent / ".test-tmp"
        temp_root.mkdir(exist_ok=True)
        self.temp_dir = tempfile.TemporaryDirectory(dir=temp_root)
        self.db_path = Path(self.temp_dir.name) / "migration.db"
        self.database = Database(self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_upgrade_preserves_existing_catalog_data(self) -> None:
        self.assertEqual(self.database.migrate(target_version=1), (1,))
        now = utc_now()
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO games(canonical_title, normalized_title, created_at, updated_at)
                VALUES ('Hades', 'hades', ?, ?)
                """,
                (now, now),
            )

        self.assertEqual(self.database.migrate(), (2, 3, 4, 5))

        with self.database.connection() as connection:
            title = connection.execute(
                "SELECT canonical_title FROM games WHERE normalized_title = 'hades'"
            ).fetchone()["canonical_title"]
            preferences_table = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'preferences'"
            ).fetchone()
        self.assertEqual(title, "Hades")
        self.assertIsNotNone(preferences_table)
        self.assertEqual(self.database.migrate(), ())

    def test_failed_transaction_rolls_back_all_changes(self) -> None:
        self.database.migrate()
        now = utc_now()

        with self.assertRaises(sqlite3.IntegrityError):
            with self.database.transaction() as connection:
                connection.execute(
                    """
                    INSERT INTO games(
                        id, canonical_title, normalized_title, created_at, updated_at
                    ) VALUES (99, 'Temporal', 'temporal', ?, ?)
                    """,
                    (now, now),
                )
                connection.execute(
                    """
                    INSERT INTO preferences(game_id, interest_score, updated_at)
                    VALUES (999, 5, ?)
                    """,
                    (now,),
                )

        with self.database.connection() as connection:
            game = connection.execute(
                "SELECT 1 FROM games WHERE id = 99"
            ).fetchone()
        self.assertIsNone(game)

    def test_steam_migration_preserves_catalog_and_rejects_unplayed_apps(self) -> None:
        self.assertEqual(self.database.migrate(target_version=3), (1, 2, 3))
        now = utc_now()
        with self.database.transaction() as connection:
            game_id = connection.execute(
                """
                INSERT INTO games(
                    canonical_title, normalized_title, created_at, updated_at
                ) VALUES ('Hades', 'hades', ?, ?)
                """,
                (now, now),
            ).lastrowid
            variant_id = connection.execute(
                """
                INSERT INTO variants(
                    game_id, platform, edition, format, region, drm, condition,
                    created_at, updated_at
                ) VALUES (?, 'pc', 'base', 'digital', '', 'steam', '', ?, ?)
                """,
                (game_id, now, now),
            ).lastrowid

        self.assertEqual(self.database.migrate(), (4, 5))

        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO steam_profile(
                    singleton, steam_id, created_at, updated_at
                ) VALUES (1, '76561198000000000', ?, ?)
                """,
                (now, now),
            )
            connection.execute(
                """
                INSERT INTO steam_apps(
                    app_id, variant_id, name, playtime_forever_minutes,
                    playtime_recent_minutes, last_played_at,
                    first_seen_at, last_seen_at
                ) VALUES (1145360, ?, 'Hades', 120, 30, NULL, ?, ?)
                """,
                (variant_id, now, now),
            )

        with self.database.connection() as connection:
            stored = connection.execute(
                """
                SELECT name, playtime_forever_minutes
                FROM steam_apps WHERE app_id = 1145360
                """
            ).fetchone()
        self.assertEqual(stored["name"], "Hades")
        self.assertEqual(stored["playtime_forever_minutes"], 120)

        with self.database.transaction() as connection:
            connection.execute("DELETE FROM steam_apps WHERE app_id = 1145360")

        with self.assertRaises(sqlite3.IntegrityError):
            with self.database.transaction() as connection:
                connection.execute(
                    """
                    INSERT INTO steam_apps(
                        app_id, variant_id, name, playtime_forever_minutes,
                        playtime_recent_minutes, last_played_at,
                        first_seen_at, last_seen_at
                    ) VALUES (999, ?, 'Nunca abierto', 0, 0, NULL, ?, ?)
                    """,
                    (variant_id, now, now),
                )


if __name__ == "__main__":
    unittest.main()

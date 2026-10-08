from pathlib import Path
import tempfile
import unittest

from ofertas.domain import ConflictError, DomainError
from ofertas.persistence.database import Database
from ofertas.persistence.repositories import SqliteGameRepository
from ofertas.services import CatalogService


class CatalogServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_root = Path(__file__).resolve().parent.parent / ".test-tmp"
        temp_root.mkdir(exist_ok=True)
        self.temp_dir = tempfile.TemporaryDirectory(dir=temp_root)
        self.db_path = Path(self.temp_dir.name) / "catalog.db"
        database = Database(self.db_path)
        database.migrate()
        self.service = CatalogService(SqliteGameRepository(database))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_game_variants_interest_and_ownership_persist(self) -> None:
        game_id = self.service.add_game("Hades")
        steam_id = self.service.add_variant(
            game_id,
            platform="PC",
            edition="Base",
            format="Digital",
            region="CL",
            drm="Steam",
        )
        switch_id = self.service.add_variant(
            game_id,
            platform="Nintendo Switch",
            edition="Base",
            format="Cartucho",
            region="CL",
            condition="Nuevo",
        )
        self.service.set_interest(game_id, 8)
        self.service.set_taste(game_id, 9)
        self.service.set_owned(steam_id, True)

        restarted = CatalogService(
            SqliteGameRepository(Database(self.db_path))
        )
        game = restarted.get_game(game_id)

        self.assertEqual(game.canonical_title, "Hades")
        self.assertEqual(game.interest_score, 8)
        self.assertEqual(game.taste_score, 9)
        self.assertTrue(next(v for v in game.variants if v.id == steam_id).owned)
        self.assertFalse(next(v for v in game.variants if v.id == switch_id).owned)

    def test_interest_states_and_validation(self) -> None:
        game_id = self.service.add_game("Celeste")
        self.assertIsNone(self.service.get_game(game_id).interest_score)

        self.service.ignore(game_id)
        self.assertEqual(self.service.get_game(game_id).interest_score, 0)

        self.service.reactivate(game_id)
        self.assertIsNone(self.service.get_game(game_id).interest_score)

        for valid_score in (1, 10):
            self.service.set_interest(game_id, valid_score)
            self.assertEqual(
                self.service.get_game(game_id).interest_score, valid_score
            )

        for invalid_score in (-1, 11, "8", True):
            with self.subTest(score=invalid_score):
                with self.assertRaises(DomainError):
                    self.service.set_interest(
                        game_id, invalid_score  # type: ignore[arg-type]
                    )

    def test_taste_is_separate_from_purchase_interest(self) -> None:
        game_id = self.service.add_game("Hades")
        self.service.set_interest(game_id, 6)
        self.service.set_taste(game_id, 9)

        game = self.service.get_game(game_id)
        self.assertEqual(game.interest_score, 6)
        self.assertEqual(game.taste_score, 9)

        self.service.clear_taste(game_id)
        game = self.service.get_game(game_id)
        self.assertIsNone(game.taste_score)
        self.assertEqual(game.interest_score, 6)

        for invalid_score in (0, 11, "9", True):
            with self.subTest(score=invalid_score):
                with self.assertRaises(DomainError):
                    self.service.set_taste(game_id, invalid_score)  # type: ignore[arg-type]

    def test_duplicate_variant_is_rejected_after_normalization(self) -> None:
        game_id = self.service.add_game("Hades")
        self.service.add_variant(game_id, platform="PC", drm="Steam")

        with self.assertRaises(ConflictError):
            self.service.add_variant(game_id, platform=" pc ", drm="STEAM")

    def test_alias_search_finds_the_canonical_game(self) -> None:
        game_id = self.service.add_game("The Legend of Zelda: Breath of the Wild")
        self.service.add_alias(game_id, "Zelda BOTW")

        results = self.service.search_games("botw")

        self.assertEqual([game.id for game in results], [game_id])

    def test_aliases_cannot_collide_with_canonical_titles(self) -> None:
        hades_id = self.service.add_game("Hades")
        self.service.add_game("Bastion")

        with self.assertRaises(ConflictError):
            self.service.add_alias(hades_id, "Bastion")

        self.service.add_alias(hades_id, "Hades Game")
        with self.assertRaises(ConflictError):
            self.service.add_game("HADES GAME")


if __name__ == "__main__":
    unittest.main()

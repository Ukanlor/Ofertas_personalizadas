from pathlib import Path
import tempfile
import unittest

from ofertas.persistence.database import Database
from ofertas.persistence.telegram_state import TelegramStateRepository


class TelegramStateRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_root = Path(__file__).resolve().parent.parent / ".test-tmp"
        temp_root.mkdir(exist_ok=True)
        self.temp_dir = tempfile.TemporaryDirectory(dir=temp_root)
        database = Database(Path(self.temp_dir.name) / "telegram-state.db")
        database.migrate()
        self.state = TelegramStateRepository(database)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_offset_advances_and_never_moves_backwards(self) -> None:
        self.assertIsNone(self.state.get_next_offset())

        self.state.mark_update_processed(20)
        self.state.mark_update_processed(19)

        self.assertEqual(self.state.get_next_offset(), 21)

    def test_callback_record_is_idempotent(self) -> None:
        first = self.state.record_callback(
            "callback-1", user_id=123, action="rate", target_id=1
        )
        repeated = self.state.record_callback(
            "callback-1", user_id=123, action="rate", target_id=1
        )

        self.assertTrue(first)
        self.assertFalse(repeated)
        self.assertTrue(self.state.callback_was_processed("callback-1"))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import sqlite3

from ofertas.persistence.database import Database, utc_now


class TelegramStateRepository:
    LAST_UPDATE_KEY = "last_update_id"

    def __init__(self, database: Database) -> None:
        self.database = database

    def get_next_offset(self) -> int | None:
        with self.database.connection() as connection:
            row = connection.execute(
                "SELECT value FROM telegram_state WHERE key = ?",
                (self.LAST_UPDATE_KEY,),
            ).fetchone()
        if row is None:
            return None
        return int(row["value"]) + 1

    def mark_update_processed(self, update_id: int) -> None:
        with self.database.transaction() as connection:
            row = connection.execute(
                "SELECT value FROM telegram_state WHERE key = ?",
                (self.LAST_UPDATE_KEY,),
            ).fetchone()
            if row is not None and int(row["value"]) >= update_id:
                return
            connection.execute(
                """
                INSERT INTO telegram_state(key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                (self.LAST_UPDATE_KEY, str(update_id), utc_now()),
            )

    def callback_was_processed(self, callback_query_id: str) -> bool:
        with self.database.connection() as connection:
            row = connection.execute(
                "SELECT 1 FROM telegram_callbacks WHERE callback_query_id = ?",
                (callback_query_id,),
            ).fetchone()
        return row is not None

    def record_callback(
        self,
        callback_query_id: str,
        *,
        user_id: int,
        action: str,
        target_id: int,
    ) -> bool:
        try:
            with self.database.transaction() as connection:
                connection.execute(
                    """
                    INSERT INTO telegram_callbacks(
                        callback_query_id, user_id, action, target_id, processed_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (callback_query_id, user_id, action, target_id, utc_now()),
                )
            return True
        except sqlite3.IntegrityError:
            return False

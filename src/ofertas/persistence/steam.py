from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from ofertas.domain import ConflictError
from ofertas.persistence.database import Database, utc_now


@dataclass(frozen=True, slots=True)
class SteamAppRecord:
    app_id: int
    name: str
    normalized_name: str
    playtime_forever_minutes: int
    playtime_recent_minutes: int
    last_played_at: str | None


class SqliteSteamRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def import_apps(self, steam_id: str, apps: list[SteamAppRecord]) -> int:
        now = utc_now()
        created_games = 0
        with self.database.transaction() as connection:
            self._bind_profile(connection, steam_id, now)
            for app in apps:
                mapped = connection.execute(
                    "SELECT variant_id FROM steam_apps WHERE app_id = ?",
                    (app.app_id,),
                ).fetchone()
                if mapped is None:
                    game_id = self._find_game(connection, app.normalized_name)
                    if game_id is None:
                        game_id = self._create_game(connection, app, now)
                        created_games += 1
                    variant_id = self._find_or_create_variant(
                        connection, game_id, now
                    )
                    connection.execute(
                        """
                        INSERT INTO steam_apps(
                            app_id, variant_id, name, playtime_forever_minutes,
                            playtime_recent_minutes, last_played_at,
                            first_seen_at, last_seen_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            app.app_id,
                            variant_id,
                            app.name,
                            app.playtime_forever_minutes,
                            app.playtime_recent_minutes,
                            app.last_played_at,
                            now,
                            now,
                        ),
                    )
                else:
                    variant_id = int(mapped["variant_id"])
                    connection.execute(
                        """
                        UPDATE steam_apps
                        SET name = ?, playtime_forever_minutes = ?,
                            playtime_recent_minutes = ?, last_played_at = ?,
                            last_seen_at = ?
                        WHERE app_id = ?
                        """,
                        (
                            app.name,
                            app.playtime_forever_minutes,
                            app.playtime_recent_minutes,
                            app.last_played_at,
                            now,
                            app.app_id,
                        ),
                    )
                self._ensure_owned(connection, variant_id, now)
        return created_games

    @staticmethod
    def _bind_profile(
        connection: sqlite3.Connection, steam_id: str, now: str
    ) -> None:
        current = connection.execute(
            "SELECT steam_id FROM steam_profile WHERE singleton = 1"
        ).fetchone()
        if current is not None and current["steam_id"] != steam_id:
            raise ConflictError(
                "La base ya está vinculada a otra cuenta de Steam."
            )
        connection.execute(
            """
            INSERT INTO steam_profile(singleton, steam_id, created_at, updated_at)
            VALUES (1, ?, ?, ?)
            ON CONFLICT(singleton) DO UPDATE SET updated_at = excluded.updated_at
            """,
            (steam_id, now, now),
        )

    @staticmethod
    def _find_game(
        connection: sqlite3.Connection, normalized_name: str
    ) -> int | None:
        matches = connection.execute(
            """
            SELECT game_id
            FROM (
                SELECT id AS game_id FROM games WHERE normalized_title = ?
                UNION
                SELECT game_id FROM aliases WHERE normalized_alias = ?
            )
            """,
            (normalized_name, normalized_name),
        ).fetchall()
        if len(matches) > 1:
            raise ConflictError(
                "El nombre de Steam coincide con más de un juego local."
            )
        return int(matches[0]["game_id"]) if matches else None

    @staticmethod
    def _create_game(
        connection: sqlite3.Connection, app: SteamAppRecord, now: str
    ) -> int:
        cursor = connection.execute(
            """
            INSERT INTO games(canonical_title, normalized_title, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (app.name, app.normalized_name, now, now),
        )
        return int(cursor.lastrowid)

    @staticmethod
    def _find_or_create_variant(
        connection: sqlite3.Connection, game_id: int, now: str
    ) -> int:
        matches = connection.execute(
            """
            SELECT id
            FROM variants
            WHERE game_id = ? AND platform = 'pc' AND edition = 'base'
              AND format IN ('', 'digital') AND drm = 'steam'
              AND condition = ''
            ORDER BY id
            """,
            (game_id,),
        ).fetchall()
        if len(matches) > 1:
            raise ConflictError(
                "Hay más de una variante Steam compatible; se requiere revisión manual."
            )
        if matches:
            return int(matches[0]["id"])
        cursor = connection.execute(
            """
            INSERT INTO variants(
                game_id, platform, edition, format, region, drm, condition,
                created_at, updated_at
            ) VALUES (?, 'pc', 'base', 'digital', '', 'steam', '', ?, ?)
            """,
            (game_id, now, now),
        )
        return int(cursor.lastrowid)

    @staticmethod
    def _ensure_owned(
        connection: sqlite3.Connection, variant_id: int, now: str
    ) -> None:
        connection.execute(
            """
            INSERT INTO ownership(variant_id, source, acquired_at, updated_at)
            VALUES (?, 'steam', NULL, ?)
            ON CONFLICT(variant_id) DO NOTHING
            """,
            (variant_id, now),
        )

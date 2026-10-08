from __future__ import annotations

import sqlite3

from ofertas.domain import ConflictError, Game, NotFoundError, Variant
from ofertas.persistence.database import Database, utc_now


class SqliteGameRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create_game(self, canonical_title: str, normalized_title: str) -> int:
        now = utc_now()
        try:
            with self.database.transaction() as connection:
                alias_match = connection.execute(
                    "SELECT 1 FROM aliases WHERE normalized_alias = ?",
                    (normalized_title,),
                ).fetchone()
                if alias_match is not None:
                    raise ConflictError("Ese título ya existe como alias de otro juego.")
                cursor = connection.execute(
                    """
                    INSERT INTO games(canonical_title, normalized_title, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (canonical_title, normalized_title, now, now),
                )
                return int(cursor.lastrowid)
        except sqlite3.IntegrityError as error:
            raise ConflictError("Ya existe un juego con ese título.") from error

    def add_alias(self, game_id: int, alias: str, normalized_alias: str) -> int:
        self._require_game(game_id)
        try:
            with self.database.transaction() as connection:
                title_match = connection.execute(
                    "SELECT 1 FROM games WHERE normalized_title = ?",
                    (normalized_alias,),
                ).fetchone()
                if title_match is not None:
                    raise ConflictError("Ese alias ya existe como título canónico.")
                cursor = connection.execute(
                    """
                    INSERT INTO aliases(game_id, alias, normalized_alias, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (game_id, alias, normalized_alias, utc_now()),
                )
                return int(cursor.lastrowid)
        except sqlite3.IntegrityError as error:
            raise ConflictError("Ese alias ya está asociado a un juego.") from error

    def add_variant(
        self,
        game_id: int,
        *,
        platform: str,
        edition: str,
        format: str,
        region: str,
        drm: str,
        condition: str,
    ) -> int:
        self._require_game(game_id)
        now = utc_now()
        try:
            with self.database.transaction() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO variants(
                        game_id, platform, edition, format, region, drm, condition,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        game_id,
                        platform,
                        edition,
                        format,
                        region,
                        drm,
                        condition,
                        now,
                        now,
                    ),
                )
                return int(cursor.lastrowid)
        except sqlite3.IntegrityError as error:
            raise ConflictError("Ya existe una variante con esa identidad.") from error

    def set_interest(self, game_id: int, score: int | None) -> None:
        self._require_game(game_id)
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO preferences(game_id, interest_score, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(game_id) DO UPDATE SET
                    interest_score = excluded.interest_score,
                    updated_at = excluded.updated_at
                """,
                (game_id, score, utc_now()),
            )

    def set_owned(self, variant_id: int, owned: bool, source: str = "manual") -> None:
        self._require_variant(variant_id)
        with self.database.transaction() as connection:
            if owned:
                now = utc_now()
                connection.execute(
                    """
                    INSERT INTO ownership(variant_id, source, acquired_at, updated_at)
                    VALUES (?, ?, NULL, ?)
                    ON CONFLICT(variant_id) DO UPDATE SET
                        source = excluded.source,
                        updated_at = excluded.updated_at
                    """,
                    (variant_id, source, now),
                )
            else:
                connection.execute(
                    "DELETE FROM ownership WHERE variant_id = ?", (variant_id,)
                )

    def get_game(self, game_id: int) -> Game:
        with self.database.connection() as connection:
            game_row = connection.execute(
                """
                SELECT g.id, g.canonical_title, p.interest_score
                FROM games AS g
                LEFT JOIN preferences AS p ON p.game_id = g.id
                WHERE g.id = ?
                """,
                (game_id,),
            ).fetchone()
            if game_row is None:
                raise NotFoundError(f"No existe el juego {game_id}.")

            aliases = tuple(
                row["alias"]
                for row in connection.execute(
                    "SELECT alias FROM aliases WHERE game_id = ? ORDER BY alias",
                    (game_id,),
                )
            )
            variants = tuple(
                self._variant_from_row(row)
                for row in connection.execute(
                    """
                    SELECT
                        v.id, v.game_id, v.platform, v.edition, v.format,
                        v.region, v.drm, v.condition,
                        o.variant_id IS NOT NULL AS owned,
                        o.source AS ownership_source
                    FROM variants AS v
                    LEFT JOIN ownership AS o ON o.variant_id = v.id
                    WHERE v.game_id = ?
                    ORDER BY v.id
                    """,
                    (game_id,),
                )
            )
            return Game(
                id=game_row["id"],
                canonical_title=game_row["canonical_title"],
                interest_score=game_row["interest_score"],
                aliases=aliases,
                variants=variants,
            )

    def search_games(self, normalized_query: str) -> tuple[Game, ...]:
        escaped = normalized_query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        with self.database.connection() as connection:
            ids = [
                row["id"]
                for row in connection.execute(
                    """
                    SELECT DISTINCT g.id, g.canonical_title
                    FROM games AS g
                    LEFT JOIN aliases AS a ON a.game_id = g.id
                    WHERE g.normalized_title LIKE ? ESCAPE '\\'
                       OR a.normalized_alias LIKE ? ESCAPE '\\'
                    ORDER BY g.canonical_title
                    """,
                    (pattern, pattern),
                )
            ]
        return tuple(self.get_game(game_id) for game_id in ids)

    def _require_game(self, game_id: int) -> None:
        with self.database.connection() as connection:
            exists = connection.execute(
                "SELECT 1 FROM games WHERE id = ?", (game_id,)
            ).fetchone()
        if exists is None:
            raise NotFoundError(f"No existe el juego {game_id}.")

    def _require_variant(self, variant_id: int) -> None:
        with self.database.connection() as connection:
            exists = connection.execute(
                "SELECT 1 FROM variants WHERE id = ?", (variant_id,)
            ).fetchone()
        if exists is None:
            raise NotFoundError(f"No existe la variante {variant_id}.")

    @staticmethod
    def _variant_from_row(row: sqlite3.Row) -> Variant:
        return Variant(
            id=row["id"],
            game_id=row["game_id"],
            platform=row["platform"],
            edition=row["edition"],
            format=row["format"],
            region=row["region"],
            drm=row["drm"],
            condition=row["condition"],
            owned=bool(row["owned"]),
            ownership_source=row["ownership_source"],
        )

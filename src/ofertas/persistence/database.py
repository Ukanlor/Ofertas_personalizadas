from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from collections.abc import Iterator


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def iter_sql_statements(sql: str) -> Iterator[str]:
    buffer: list[str] = []
    for line in sql.splitlines():
        buffer.append(line)
        candidate = "\n".join(buffer).strip()
        if candidate and sqlite3.complete_statement(candidate):
            yield candidate
            buffer.clear()
    if "\n".join(buffer).strip():
        raise ValueError("La migración termina con una sentencia SQL incompleta.")


class Database:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self.connection() as connection:
            with connection:
                yield connection

    def migrate(self, target_version: int | None = None) -> tuple[int, ...]:
        migrations_dir = Path(__file__).with_name("migrations")
        migration_files = sorted(migrations_dir.glob("[0-9][0-9][0-9]_*.sql"))
        applied_now: list[int] = []

        with self.connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TEXT NOT NULL
                )
                """
            )
            connection.commit()
            applied = {
                row["version"]
                for row in connection.execute("SELECT version FROM schema_migrations")
            }

            for migration_path in migration_files:
                version = int(migration_path.name.split("_", 1)[0])
                if version in applied or (
                    target_version is not None and version > target_version
                ):
                    continue
                sql = migration_path.read_text(encoding="utf-8")
                with connection:
                    for statement in iter_sql_statements(sql):
                        connection.execute(statement)
                    connection.execute(
                        """
                        INSERT INTO schema_migrations(version, name, applied_at)
                        VALUES (?, ?, ?)
                        """,
                        (version, migration_path.name, utc_now()),
                    )
                applied_now.append(version)

        return tuple(applied_now)

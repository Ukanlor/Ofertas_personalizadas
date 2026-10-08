from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from collections.abc import Iterable

from ofertas.domain import DomainError, clean_display_text, normalize_text
from ofertas.persistence.steam import SqliteSteamRepository, SteamAppRecord


@dataclass(frozen=True, slots=True)
class SteamOwnedApp:
    app_id: int
    name: str
    playtime_forever_minutes: int
    playtime_recent_minutes: int = 0
    last_played_epoch: int = 0


@dataclass(frozen=True, slots=True)
class SteamImportResult:
    received: int
    imported: int
    skipped_unplayed: int
    created_games: int


class SteamLibraryImporter:
    def __init__(self, repository: SqliteSteamRepository) -> None:
        self.repository = repository

    def import_library(
        self, steam_id: str, apps: Iterable[SteamOwnedApp]
    ) -> SteamImportResult:
        normalized_steam_id = validate_steam_id(steam_id)
        received = tuple(apps)
        seen_app_ids: set[int] = set()
        records: list[SteamAppRecord] = []
        skipped_unplayed = 0

        for app in received:
            record = validate_app(app)
            if record.app_id in seen_app_ids:
                raise DomainError(f"Steam repitió el AppID {record.app_id}.")
            seen_app_ids.add(record.app_id)
            if record.playtime_forever_minutes == 0:
                skipped_unplayed += 1
                continue
            records.append(record)

        created_games = self.repository.import_apps(normalized_steam_id, records)
        return SteamImportResult(
            received=len(received),
            imported=len(records),
            skipped_unplayed=skipped_unplayed,
            created_games=created_games,
        )


def validate_steam_id(value: str) -> str:
    if not isinstance(value, str):
        raise DomainError("El SteamID debe ser texto numérico.")
    cleaned = value.strip()
    if not cleaned.isdecimal() or int(cleaned) <= 0:
        raise DomainError("El SteamID debe ser un entero positivo.")
    return cleaned


def validate_app(app: SteamOwnedApp) -> SteamAppRecord:
    app_id = positive_integer(app.app_id, "El AppID")
    total = non_negative_integer(
        app.playtime_forever_minutes, "El tiempo total"
    )
    recent = non_negative_integer(
        app.playtime_recent_minutes, "El tiempo reciente"
    )
    last_played_epoch = non_negative_integer(
        app.last_played_epoch, "La última ejecución"
    )
    last_played_at = (
        datetime.fromtimestamp(last_played_epoch, timezone.utc).isoformat(
            timespec="seconds"
        )
        if last_played_epoch
        else None
    )
    display_name = clean_display_text(app.name, "El nombre de Steam")
    return SteamAppRecord(
        app_id=app_id,
        name=display_name,
        normalized_name=normalize_text(display_name),
        playtime_forever_minutes=total,
        playtime_recent_minutes=recent,
        last_played_at=last_played_at,
    )


def positive_integer(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise DomainError(f"{field_name} debe ser un entero positivo.")
    return value


def non_negative_integer(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise DomainError(f"{field_name} debe ser un entero no negativo.")
    return value

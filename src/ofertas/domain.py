from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


class DomainError(ValueError):
    """Error de entrada que puede mostrarse al usuario."""


class NotFoundError(DomainError):
    """La entidad solicitada no existe."""


class ConflictError(DomainError):
    """La operación produciría una identidad duplicada."""


@dataclass(frozen=True, slots=True)
class Variant:
    id: int
    game_id: int
    platform: str
    edition: str
    format: str
    region: str
    drm: str
    condition: str
    owned: bool
    ownership_source: str | None


@dataclass(frozen=True, slots=True)
class Game:
    id: int
    canonical_title: str
    taste_score: int | None
    interest_score: int | None
    aliases: tuple[str, ...] = ()
    variants: tuple[Variant, ...] = ()


@dataclass(frozen=True, slots=True)
class TasteCandidate:
    game: Game
    playtime_forever_minutes: int
    remaining: int


def clean_display_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise DomainError(f"{field_name} debe ser texto.")
    cleaned = " ".join(unicodedata.normalize("NFKC", value).split())
    if not cleaned:
        raise DomainError(f"{field_name} no puede estar vacío.")
    return cleaned


def normalize_text(value: str) -> str:
    return clean_display_text(value, "texto").casefold()


def normalize_code(value: str, field_name: str, *, allow_empty: bool = True) -> str:
    if not isinstance(value, str):
        raise DomainError(f"{field_name} debe ser texto.")
    cleaned = unicodedata.normalize("NFKC", value).strip().casefold()
    cleaned = re.sub(r"\s+", "-", cleaned)
    if not cleaned and not allow_empty:
        raise DomainError(f"{field_name} no puede estar vacío.")
    return cleaned


def validate_interest(score: int | None) -> int | None:
    if score is None:
        return None
    if isinstance(score, bool) or not isinstance(score, int):
        raise DomainError("El interés debe ser un número entero entre 0 y 10.")
    if not 0 <= score <= 10:
        raise DomainError("El interés debe estar entre 0 y 10.")
    return score


def validate_taste(score: int) -> int:
    if isinstance(score, bool) or not isinstance(score, int):
        raise DomainError("El gusto debe ser un número entero entre 1 y 10.")
    if not 1 <= score <= 10:
        raise DomainError("El gusto debe estar entre 1 y 10.")
    return score

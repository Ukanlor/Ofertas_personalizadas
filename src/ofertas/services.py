from __future__ import annotations

from ofertas.domain import (
    Game,
    TasteCandidate,
    Variant,
    clean_display_text,
    normalize_code,
    normalize_text,
    validate_interest,
    validate_taste,
)
from ofertas.persistence.repositories import SqliteGameRepository


class CatalogService:
    def __init__(self, repository: SqliteGameRepository) -> None:
        self.repository = repository

    def add_game(self, title: str) -> int:
        display_title = clean_display_text(title, "El título")
        return self.repository.create_game(display_title, normalize_text(display_title))

    def add_alias(self, game_id: int, alias: str) -> int:
        display_alias = clean_display_text(alias, "El alias")
        return self.repository.add_alias(game_id, display_alias, normalize_text(display_alias))

    def add_variant(
        self,
        game_id: int,
        *,
        platform: str,
        edition: str = "base",
        format: str = "",
        region: str = "",
        drm: str = "",
        condition: str = "",
    ) -> int:
        return self.repository.add_variant(
            game_id,
            platform=normalize_code(platform, "La plataforma", allow_empty=False),
            edition=normalize_code(edition, "La edición", allow_empty=False),
            format=normalize_code(format, "El formato"),
            region=normalize_code(region, "La región"),
            drm=normalize_code(drm, "El DRM"),
            condition=normalize_code(condition, "La condición"),
        )

    def set_interest(self, game_id: int, score: int | None) -> None:
        self.repository.set_interest(game_id, validate_interest(score))

    def ignore(self, game_id: int) -> None:
        self.set_interest(game_id, 0)

    def reactivate(self, game_id: int) -> None:
        self.set_interest(game_id, None)

    def set_taste(self, game_id: int, score: int) -> None:
        self.repository.set_taste(game_id, validate_taste(score))

    def clear_taste(self, game_id: int) -> None:
        self.repository.set_taste(game_id, None)

    def set_owned(self, variant_id: int, owned: bool, source: str = "manual") -> None:
        normalized_source = normalize_code(source, "La fuente", allow_empty=False)
        self.repository.set_owned(variant_id, owned, normalized_source)

    def get_game(self, game_id: int) -> Game:
        return self.repository.get_game(game_id)

    def get_variant(self, variant_id: int) -> Variant:
        return self.repository.get_variant(variant_id)

    def search_games(self, query: str) -> tuple[Game, ...]:
        return self.repository.search_games(normalize_text(query))

    def next_taste_candidate(self) -> TasteCandidate | None:
        return self.repository.next_taste_candidate()

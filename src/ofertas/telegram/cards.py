from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ofertas.domain import Game, TasteCandidate, Variant


JsonObject = dict[str, Any]


@dataclass(frozen=True, slots=True)
class GameCard:
    text: str
    reply_markup: JsonObject


def build_game_card(game: Game) -> GameCard:
    taste = f"{game.taste_score}/10" if game.taste_score is not None else "sin puntuar"
    lines = [
        game.canonical_title,
        f"Gusto: {taste}",
        f"Interés de compra: {interest_label(game.interest_score)}",
    ]
    if game.variants:
        lines.append("Variantes:")
        lines.extend(f"- {variant_line(variant)}" for variant in game.variants)
    else:
        lines.append("Variantes: ninguna")

    keyboard: list[list[JsonObject]] = []
    for start in (1, 6):
        keyboard.append(
            [
                {
                    "text": str(score),
                    "callback_data": f"rate:{game.id}:{score}",
                }
                for score in range(start, start + 5)
            ]
        )
    if game.interest_score == 0:
        keyboard.append(
            [{"text": "Reactivar", "callback_data": f"reactivate:{game.id}"}]
        )
    else:
        keyboard.append(
            [{"text": "Ignorar", "callback_data": f"ignore:{game.id}"}]
        )
    for variant in game.variants:
        action = "unset" if variant.owned else "set"
        prefix = "Quitar propiedad" if variant.owned else "Ya lo tengo"
        label = compact_variant_label(variant)
        keyboard.append(
            [
                {
                    "text": f"{prefix}: {label}"[:64],
                    "callback_data": f"own:{variant.id}:{action}",
                }
            ]
        )
    return GameCard(
        text="\n".join(lines),
        reply_markup={"inline_keyboard": keyboard},
    )


def build_taste_card(candidate: TasteCandidate) -> GameCard:
    game = candidate.game
    hours = candidate.playtime_forever_minutes / 60
    keyboard = [
        [
            {
                "text": str(score),
                "callback_data": f"taste:{game.id}:{score}",
            }
            for score in range(start, start + 5)
        ]
        for start in (1, 6)
    ]
    return GameCard(
        text=(
            "Calibración de gusto\n\n"
            f"{game.canonical_title}\n"
            f"Tiempo en Steam: {hours:.1f} h (solo contexto)\n"
            f"Juegos pendientes: {candidate.remaining}\n\n"
            "¿Cuánto te gustó?"
        ),
        reply_markup={"inline_keyboard": keyboard},
    )


def build_taste_saved_card(game: Game) -> GameCard:
    return GameCard(
        text=(
            "Gusto guardado\n\n"
            f"{game.canonical_title}\n"
            f"Gusto: {game.taste_score}/10"
        ),
        reply_markup={"inline_keyboard": []},
    )


def interest_label(score: int | None) -> str:
    if score is None:
        return "sin puntuar"
    if score == 0:
        return "ignorado"
    return f"{score}/10"


def variant_line(variant: Variant) -> str:
    ownership = "poseída" if variant.owned else "no poseída"
    return f"{compact_variant_label(variant)} - {ownership}"


def compact_variant_label(variant: Variant) -> str:
    values = [variant.platform, variant.edition]
    values.extend(
        value
        for value in (variant.format, variant.region, variant.drm, variant.condition)
        if value
    )
    return " / ".join(values)

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ofertas.domain import Game, Variant


JsonObject = dict[str, Any]


@dataclass(frozen=True, slots=True)
class GameCard:
    text: str
    reply_markup: JsonObject


def build_game_card(game: Game) -> GameCard:
    lines = [game.canonical_title, f"Interés: {interest_label(game.interest_score)}"]
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

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from collections.abc import Sequence

from ofertas.domain import DomainError, Game
from ofertas.persistence.database import Database
from ofertas.persistence.repositories import SqliteGameRepository
from ofertas.services import CatalogService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ofertas")
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("data/ofertas.db"),
        help="Ruta de la base SQLite (predeterminado: data/ofertas.db).",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    db_parser = commands.add_parser("db", help="Administrar la base local.")
    db_commands = db_parser.add_subparsers(dest="db_command", required=True)
    db_commands.add_parser("init", help="Aplicar migraciones pendientes.")

    game_parser = commands.add_parser("game", help="Administrar juegos.")
    game_commands = game_parser.add_subparsers(dest="game_command", required=True)
    game_add = game_commands.add_parser("add", help="Crear un juego.")
    game_add.add_argument("title")
    game_show = game_commands.add_parser("show", help="Mostrar un juego.")
    game_show.add_argument("game_id", type=int)
    game_search = game_commands.add_parser("search", help="Buscar por título o alias.")
    game_search.add_argument("query")

    alias_parser = commands.add_parser("alias", help="Administrar alias.")
    alias_commands = alias_parser.add_subparsers(dest="alias_command", required=True)
    alias_add = alias_commands.add_parser("add", help="Añadir un alias.")
    alias_add.add_argument("game_id", type=int)
    alias_add.add_argument("alias")

    variant_parser = commands.add_parser("variant", help="Administrar variantes.")
    variant_commands = variant_parser.add_subparsers(
        dest="variant_command", required=True
    )
    variant_add = variant_commands.add_parser("add", help="Crear una variante.")
    variant_add.add_argument("game_id", type=int)
    variant_add.add_argument("--platform", required=True)
    variant_add.add_argument("--edition", default="base")
    variant_add.add_argument("--format", default="")
    variant_add.add_argument("--region", default="")
    variant_add.add_argument("--drm", default="")
    variant_add.add_argument("--condition", default="")

    interest_parser = commands.add_parser("interest", help="Guardar interés 1-10.")
    interest_commands = interest_parser.add_subparsers(
        dest="interest_command", required=True
    )
    interest_set = interest_commands.add_parser("set", help="Guardar una puntuación.")
    interest_set.add_argument("game_id", type=int)
    interest_set.add_argument("score", type=int)

    ignore_parser = commands.add_parser("ignore", help="Ignorar un juego (interés 0).")
    ignore_parser.add_argument("game_id", type=int)

    reactivate_parser = commands.add_parser(
        "reactivate", help="Reactivar un juego y dejarlo sin puntuar."
    )
    reactivate_parser.add_argument("game_id", type=int)

    owned_parser = commands.add_parser("owned", help="Administrar propiedad.")
    owned_commands = owned_parser.add_subparsers(dest="owned_command", required=True)
    owned_set = owned_commands.add_parser("set", help="Marcar una variante como poseída.")
    owned_set.add_argument("variant_id", type=int)
    owned_set.add_argument("--source", default="manual")
    owned_unset = owned_commands.add_parser(
        "unset", help="Quitar la marca de propiedad de una variante."
    )
    owned_unset.add_argument("variant_id", type=int)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    database = Database(args.db)

    try:
        applied = database.migrate()
        if args.command == "db":
            if applied:
                versions = ", ".join(str(version) for version in applied)
                print(f"Migraciones aplicadas: {versions}")
            else:
                print("Base actualizada; no había migraciones pendientes.")
            return 0

        service = CatalogService(SqliteGameRepository(database))
        return run_command(args, service)
    except DomainError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


def run_command(args: argparse.Namespace, service: CatalogService) -> int:
    if args.command == "game" and args.game_command == "add":
        game_id = service.add_game(args.title)
        print(f"Juego creado: {game_id}")
    elif args.command == "game" and args.game_command == "show":
        print_game(service.get_game(args.game_id))
    elif args.command == "game" and args.game_command == "search":
        games = service.search_games(args.query)
        if not games:
            print("Sin resultados.")
        for game in games:
            print(f"{game.id}: {game.canonical_title} ({interest_label(game.interest_score)})")
    elif args.command == "alias" and args.alias_command == "add":
        alias_id = service.add_alias(args.game_id, args.alias)
        print(f"Alias creado: {alias_id}")
    elif args.command == "variant" and args.variant_command == "add":
        variant_id = service.add_variant(
            args.game_id,
            platform=args.platform,
            edition=args.edition,
            format=args.format,
            region=args.region,
            drm=args.drm,
            condition=args.condition,
        )
        print(f"Variante creada: {variant_id}")
    elif args.command == "interest" and args.interest_command == "set":
        if args.score == 0:
            service.ignore(args.game_id)
            print("Juego ignorado: avisos y sugerencias automáticas bloqueados.")
        else:
            service.set_interest(args.game_id, args.score)
            print(f"Interés actualizado: {args.score}/10")
    elif args.command == "ignore":
        service.ignore(args.game_id)
        print("Juego ignorado: avisos y sugerencias automáticas bloqueados.")
    elif args.command == "reactivate":
        service.reactivate(args.game_id)
        print("Juego reactivado: interés sin puntuar.")
    elif args.command == "owned" and args.owned_command == "set":
        service.set_owned(args.variant_id, True, args.source)
        print("Variante marcada como poseída.")
    elif args.command == "owned" and args.owned_command == "unset":
        service.set_owned(args.variant_id, False)
        print("Marca de propiedad eliminada.")
    else:
        raise AssertionError("Comando no implementado.")
    return 0


def interest_label(score: int | None) -> str:
    if score is None:
        return "sin puntuar"
    if score == 0:
        return "ignorado"
    return f"interés {score}/10"


def print_game(game: Game) -> None:
    print(f"Juego {game.id}: {game.canonical_title}")
    print(f"Interés: {interest_label(game.interest_score)}")
    if game.aliases:
        print(f"Alias: {', '.join(game.aliases)}")
    if not game.variants:
        print("Variantes: ninguna")
        return
    print("Variantes:")
    for variant in game.variants:
        details = [variant.platform, variant.edition]
        details.extend(
            value
            for value in (variant.format, variant.region, variant.drm, variant.condition)
            if value
        )
        ownership = (
            f"poseída ({variant.ownership_source})" if variant.owned else "no poseída"
        )
        print(f"  {variant.id}: {' / '.join(details)} - {ownership}")

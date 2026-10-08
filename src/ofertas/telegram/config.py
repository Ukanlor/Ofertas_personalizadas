from __future__ import annotations

from dataclasses import dataclass
import os

from ofertas.domain import DomainError


@dataclass(frozen=True, slots=True)
class TelegramConfig:
    token: str
    authorized_user_id: int

    @classmethod
    def from_environment(cls) -> TelegramConfig:
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        user_id_text = os.environ.get("TELEGRAM_ALLOWED_USER_ID", "").strip()
        if not token:
            raise DomainError("Falta la variable TELEGRAM_BOT_TOKEN.")
        if not user_id_text:
            raise DomainError("Falta la variable TELEGRAM_ALLOWED_USER_ID.")
        try:
            user_id = int(user_id_text)
        except ValueError:
            raise DomainError("TELEGRAM_ALLOWED_USER_ID debe ser un entero.") from None
        if user_id <= 0:
            raise DomainError("TELEGRAM_ALLOWED_USER_ID debe ser positivo.")
        return cls(token=token, authorized_user_id=user_id)


def token_from_environment() -> str:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise DomainError("Falta la variable TELEGRAM_BOT_TOKEN.")
    return token

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from config import config
from logger import logger


def _user_id(event: TelegramObject) -> int | None:
    if isinstance(event, (Message, CallbackQuery)):
        return event.from_user.id if event.from_user else None
    return None


class AccessControlMiddleware(BaseMiddleware):
    """Optional allowlist by Telegram user ID (empty list = allow all)."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        allowed = config.allowed_user_ids
        if not allowed:
            return await handler(event, data)

        user_id = _user_id(event)
        if user_id is None or user_id in allowed:
            return await handler(event, data)

        logger.warning("Access denied for user_id={}", user_id)
        if isinstance(event, Message):
            await event.answer("Access denied.")
        return None

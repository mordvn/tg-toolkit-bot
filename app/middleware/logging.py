from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from logger import logger


def _update_summary(event: TelegramObject) -> str:
    if isinstance(event, Message):
        user_id = event.from_user.id if event.from_user else "-"
        cmd = (event.text or "").split(maxsplit=1)[0] if event.text else "-"
        return f"message chat_id={event.chat.id} user_id={user_id} cmd={cmd!r}"
    if isinstance(event, CallbackQuery):
        user_id = event.from_user.id if event.from_user else "-"
        return f"callback user_id={user_id} data={event.data!r}"
    return type(event).__name__


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        logger.debug("Update in: {}", _update_summary(event))
        try:
            result = await handler(event, data)
            logger.debug("Update out: {}", _update_summary(event))
            return result
        except Exception:
            logger.exception("Update failed: {}", _update_summary(event))
            raise

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from logger import logger
from metrics import handler_errors_total


class ErrorHandlingMiddleware(BaseMiddleware):
    """Catch handler errors, log + metric, reply to user when possible."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception:
            if handler_errors_total is not None:
                handler_errors_total.add(1)
            logger.exception("Unhandled handler error")
            if isinstance(event, Message):
                await event.answer("Something went wrong. Try again later.")
            return None

import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from metrics import handler_duration_ms, updates_total


def _update_type(event: TelegramObject) -> str:
    if isinstance(event, Message):
        if event.text and event.text.startswith("/"):
            return "command"
        return "message"
    if isinstance(event, CallbackQuery):
        return "callback_query"
    return type(event).__name__


class MetricsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        update_type = _update_type(event)
        if updates_total is not None:
            updates_total.add(1, {"update_type": update_type})

        started = time.perf_counter()
        try:
            return await handler(event, data)
        finally:
            if handler_duration_ms is not None:
                elapsed_ms = (time.perf_counter() - started) * 1000
                handler_duration_ms.record(
                    elapsed_ms,
                    {"update_type": update_type},
                )

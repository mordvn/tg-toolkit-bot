from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from config import config
from tracing import get_tracer


def _span_name(event: TelegramObject) -> str:
    if isinstance(event, Message):
        if event.text and event.text.startswith("/"):
            return f"command {event.text.split(maxsplit=1)[0]}"
        return "message"
    if isinstance(event, CallbackQuery):
        return "callback_query"
    return type(event).__name__


class TracingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not config.TRACE_ENABLED:
            return await handler(event, data)

        tracer = get_tracer(__name__)
        with tracer.start_as_current_span(_span_name(event)) as span:
            if isinstance(event, Message):
                span.set_attribute("chat.id", event.chat.id)
                if event.from_user:
                    span.set_attribute("user.id", event.from_user.id)
            elif isinstance(event, CallbackQuery) and event.from_user:
                span.set_attribute("user.id", event.from_user.id)
            return await handler(event, data)

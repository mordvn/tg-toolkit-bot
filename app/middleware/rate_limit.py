import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from config import config
from logger import logger
from metrics import rate_limited_total


class RateLimitMiddleware(BaseMiddleware):
    """Per-user sliding window rate limit (in-memory)."""

    def __init__(
        self,
        max_requests: int | None = None,
        window_sec: int | None = None,
    ) -> None:
        self._max = max_requests if max_requests is not None else config.RATE_LIMIT_MAX
        self._window = (
            window_sec if window_sec is not None else config.RATE_LIMIT_WINDOW_SEC
        )
        self._hits: dict[tuple[int, int], list[float]] = defaultdict(list)

    @staticmethod
    def _actor_key(event: TelegramObject) -> tuple[int, int] | None:
        if isinstance(event, Message):
            if not event.from_user:
                return None
            return (event.chat.id, event.from_user.id)
        if isinstance(event, CallbackQuery):
            if not event.from_user or not event.message:
                return None
            return (event.message.chat.id, event.from_user.id)
        return None

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        key = self._actor_key(event)
        if key is None:
            return await handler(event, data)

        now = time.monotonic()
        window_start = now - self._window
        hits = [t for t in self._hits[key] if t > window_start]

        if len(hits) >= self._max:
            if rate_limited_total is not None:
                rate_limited_total.add(1, {"chat_id": str(key[0])})
            logger.warning("Rate limit exceeded chat_id={} user_id={}", key[0], key[1])
            if isinstance(event, Message):
                await event.answer("Too many requests. Please slow down.")
            return None

        hits.append(now)
        self._hits[key] = hits
        return await handler(event, data)

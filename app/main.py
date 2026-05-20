import asyncio

from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import BotCommand, Message

from config import config
from logger import logger
from metrics import setup_metrics, shutdown_metrics
from middleware import (
    AccessControlMiddleware,
    ErrorHandlingMiddleware,
    LoggingMiddleware,
    MetricsMiddleware,
    RateLimitMiddleware,
    TracingMiddleware,
)
from tracing import setup_tracing, shutdown_tracing

router = Router(name=__name__)


# --- helpers ---------------------------------------------------------------
def _target_message(message: Message) -> Message:
    return message.reply_to_message or message


def _extract_file(message: Message) -> tuple[str, str, str]:
    """Return (media_type, file_id, file_unique_id) for any file-bearing message."""
    source = _target_message(message)

    if source.photo:
        largest = source.photo[-1]
        return ("photo", largest.file_id, largest.file_unique_id)
    if source.video:
        return ("video", source.video.file_id, source.video.file_unique_id)
    if source.document:
        return ("document", source.document.file_id, source.document.file_unique_id)
    if source.audio:
        return ("audio", source.audio.file_id, source.audio.file_unique_id)
    if source.voice:
        return ("voice", source.voice.file_id, source.voice.file_unique_id)
    if source.animation:
        return ("animation", source.animation.file_id, source.animation.file_unique_id)
    if source.video_note:
        return (
            "video_note",
            source.video_note.file_id,
            source.video_note.file_unique_id,
        )
    if source.sticker:
        return ("sticker", source.sticker.file_id, source.sticker.file_unique_id)
    if source.paid_media:
        for paid in reversed(source.paid_media.paid_media):
            photo_sizes = getattr(paid, "photo", None)
            if photo_sizes:
                largest = photo_sizes[-1]
                return ("paid_photo", largest.file_id, largest.file_unique_id)
            video = getattr(paid, "video", None)
            if video:
                return ("paid_video", video.file_id, video.file_unique_id)

    return ("", "", "")


def _message_kind(source: Message) -> str:
    if source.text and not source.caption:
        return "text"
    if source.photo:
        return "photo"
    if source.video:
        return "video"
    if source.document:
        return "document"
    if source.audio:
        return "audio"
    if source.voice:
        return "voice"
    if source.animation:
        return "animation"
    if source.video_note:
        return "video_note"
    if source.sticker:
        return "sticker"
    if source.location:
        return "location"
    if source.venue:
        return "venue"
    if source.contact:
        return "contact"
    if source.poll:
        return "poll"
    if source.dice:
        return "dice"
    if source.game:
        return "game"
    if source.invoice:
        return "invoice"
    if source.paid_media:
        return "paid_media"
    if source.web_app_data:
        return "web_app_data"
    if source.caption:
        return "media_caption"
    return "unknown"


def _format_msg_info(source: Message) -> list[str]:
    lines = [
        f"message_id: {source.message_id}",
        f"date: {source.date.isoformat()}",
        f"kind: {_message_kind(source)}",
    ]

    if source.message_thread_id:
        lines.append(f"message_thread_id: {source.message_thread_id}")
    if source.is_topic_message:
        lines.append("is_topic_message: true")

    if source.text:
        preview = source.text[:120].replace("\n", " ")
        lines.append(f"text_preview: {preview!r}")
    if source.caption:
        preview = source.caption[:120].replace("\n", " ")
        lines.append(f"caption_preview: {preview!r}")
    if source.entities:
        lines.append(f"entities: {len(source.entities)}")
    if source.link_preview_options:
        lines.append("link_preview: configured")

    if source.location:
        lines.append(f"latitude: {source.location.latitude}")
        lines.append(f"longitude: {source.location.longitude}")
    if source.venue:
        lines.append(f"venue_title: {source.venue.title}")
        lines.append(f"venue_address: {source.venue.address}")
    if source.contact:
        lines.append(f"contact_name: {source.contact.first_name}")
        lines.append(f"contact_phone: {source.contact.phone_number}")
        lines.append(f"contact_user_id: {source.contact.user_id or '-'}")
    if source.poll:
        lines.append(f"poll_question: {source.poll.question}")
        lines.append(f"poll_options: {len(source.poll.options)}")
    if source.dice:
        lines.append(f"dice_emoji: {source.dice.emoji}")
        lines.append(f"dice_value: {source.dice.value}")
    if source.game:
        lines.append(f"game_title: {source.game.title}")
        lines.append(f"game_name: {source.game.name}")
    if source.invoice:
        lines.append(f"invoice_title: {source.invoice.title}")
        lines.append(f"invoice_currency: {source.invoice.currency}")
    if source.web_app_data:
        lines.append(f"web_app_button_text: {source.web_app_data.button_text}")
    if source.paid_media:
        lines.append(f"paid_star_count: {source.paid_media.star_count}")
        lines.append(f"paid_media_items: {len(source.paid_media.paid_media)}")

    if source.forward_origin:
        lines.append(f"forward_origin: {source.forward_origin.type}")
    elif source.forward_from:
        lines.append(f"forward_from_user_id: {source.forward_from.id}")
    elif source.forward_from_chat:
        lines.append(f"forward_from_chat_id: {source.forward_from_chat.id}")

    if source.reply_to_message:
        lines.append(f"reply_to_message_id: {source.reply_to_message.message_id}")

    return lines


# --- basic commands --------------------------------------------------------
@router.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer(
        "<b>Toolkit Bot</b> ready.\nUse /help to see available technical commands.",
        parse_mode=ParseMode.HTML,
    )


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(
        "<b>Toolkit Bot</b> commands:\n\n"
        "/chat_info — chat &amp; sender IDs (reply adds replied user)\n"
        "/msg_info — message meta: text, forward, poll, location, …\n"
        "/file_info — file_id, path &amp; sticker set (photo, video, sticker, …)\n\n"
        "Attach content or reply to a message.",
        parse_mode=ParseMode.HTML,
    )


@router.message(Command("chat_info"))
async def chat_info(message: Message) -> None:
    chat = message.chat
    from_user = message.from_user

    lines = [
        f"chat_id: {chat.id}",
        f"chat_type: {chat.type}",
    ]
    if chat.title:
        lines.append(f"chat_title: {chat.title}")
    if chat.username:
        lines.append(f"chat_username: @{chat.username}")

    if from_user:
        lines.append(f"user_id: {from_user.id}")
        lines.append(f"username: @{from_user.username}" if from_user.username else "username: -")
        lines.append(f"full_name: {from_user.full_name}")
        lines.append(f"is_bot: {from_user.is_bot}")
    else:
        lines.append("user_id: -")

    if message.reply_to_message and message.reply_to_message.from_user:
        reply_user = message.reply_to_message.from_user
        lines.append(f"reply_user_id: {reply_user.id}")
        lines.append(
            f"reply_username: @{reply_user.username}"
            if reply_user.username
            else "reply_username: -"
        )

    await message.answer("\n".join(lines))


@router.message(Command("msg_info"))
async def msg_info(message: Message) -> None:
    source = _target_message(message)
    await message.answer("\n".join(_format_msg_info(source)))


@router.message(Command("file_info"))
async def file_info(message: Message) -> None:
    source = _target_message(message)
    media_type, file_id, file_unique_id = _extract_file(message)
    if not media_type:
        await message.answer(
            "No file found. Send /file_info with media or reply to a file message."
        )
        return

    tg_file = await message.bot.get_file(file_id)
    lines = [
        f"media_type: {media_type}",
        f"file_id: {file_id}",
        f"file_unique_id: {file_unique_id}",
        f"file_path: {tg_file.file_path}",
        "download: https://api.telegram.org/file/bot<TOKEN>/" + (tg_file.file_path or ""),
    ]

    if source.sticker:
        sticker = source.sticker
        lines.extend(
            [
                f"sticker_emoji: {sticker.emoji or '-'}",
                f"sticker_set: {sticker.set_name or '-'}",
                f"is_animated: {sticker.is_animated}",
                f"is_video: {sticker.is_video}",
            ]
        )
    if source.caption:
        lines.append(f"caption_len: {len(source.caption)}")
    if source.has_media_spoiler:
        lines.append("has_media_spoiler: true")

    await message.answer("\n".join(lines))


def _register_middlewares(dp: Dispatcher) -> None:
    dp.update.outer_middleware(ErrorHandlingMiddleware())
    dp.update.outer_middleware(MetricsMiddleware())
    dp.update.outer_middleware(TracingMiddleware())
    dp.update.outer_middleware(LoggingMiddleware())
    dp.update.outer_middleware(AccessControlMiddleware())
    dp.update.outer_middleware(RateLimitMiddleware())


async def main() -> None:
    setup_tracing()
    setup_metrics()

    bot = Bot(token=config.TG_BOT_TOKEN)
    dp = Dispatcher()
    _register_middlewares(dp)
    dp.include_router(router)

    logger.info("Starting bot service={}", config.OTEL_SERVICE_NAME)
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Start bot and show greeting"),
            BotCommand(command="help", description="Show full command list"),
        ]
    )

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        shutdown_metrics()
        shutdown_tracing()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())

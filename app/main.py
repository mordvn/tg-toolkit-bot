import asyncio

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import BotCommand, Message

from config import config
from logger import logger

router = Router(name=__name__)


# --- helpers ---------------------------------------------------------------
def _target_message(message: Message) -> Message:
    return message.reply_to_message or message


def _extract_media(message: Message) -> tuple[str, str, str]:
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

    return ("", "", "")


# --- basic commands --------------------------------------------------------
@router.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer(
        "TG Toolkit Bot ready.\nUse /help to see available technical commands."
    )


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(
        "TG Toolkit commands:\n\n"
        "IDs (most useful)\n"
        "/ids - chat_id + your user_id (+ replied user_id)\n"
        "/get_chat_id - current chat ID\n"
        "/get_user_id - your Telegram user ID\n"
        "/get_my_id - alias for /get_user_id\n\n"
        "Chat/user debug\n"
        "/chat_info - extended chat + user metadata\n\n"
        "Media/sticker tools\n"
        "/media_id - file_id + file_unique_id for any media (reply or attach)\n"
        "/media_path - Telegram file_path for any media (reply or attach)\n"
        "/sticker_id - sticker set + ids (reply or attach)"
    )


# --- ids -------------------------------------------------------------------
@router.message(Command("ids"))
async def ids(message: Message) -> None:
    from_user = message.from_user
    reply_user = (
        message.reply_to_message.from_user if message.reply_to_message else None
    )

    lines = [f"chat_id: {message.chat.id}"]
    if from_user:
        lines.append(f"user_id: {from_user.id}")
    if reply_user:
        lines.append(f"reply_user_id: {reply_user.id}")

    await message.answer("\n".join(lines))


@router.message(Command("get_chat_id"))
async def get_chat_id(message: Message) -> None:
    await message.answer(f"chat_id: {message.chat.id}")


@router.message(Command("get_user_id", "get_my_id"))
async def get_user_id(message: Message) -> None:
    if not message.from_user:
        await message.answer("Unable to resolve user ID for this update.")
        return

    await message.answer(f"user_id: {message.from_user.id}")


# --- chat/user debug -------------------------------------------------------
@router.message(Command("chat_info"))
async def chat_info(message: Message) -> None:
    from_user = message.from_user
    username = f"@{from_user.username}" if from_user and from_user.username else "-"
    full_name = from_user.full_name if from_user else "-"

    lines = [
        "chat_info",
        f"chat_id: {message.chat.id}",
        f"chat_type: {message.chat.type}",
        f"user_id: {from_user.id if from_user else '-'}",
        f"username: {username}",
        f"full_name: {full_name}",
    ]

    await message.answer("\n".join(lines))


# --- media/sticker tools ---------------------------------------------------
@router.message(Command("media_id"))
async def media_id(message: Message) -> None:
    media_type, file_id, file_unique_id = _extract_media(message)
    if not media_type:
        await message.answer(
            "No media found. Send /media_id with media or reply to a media message."
        )
        return

    await message.answer(
        f"media_type: {media_type}\n"
        f"file_id: {file_id}\n"
        f"file_unique_id: {file_unique_id}"
    )


@router.message(Command("media_path"))
async def media_path(message: Message) -> None:
    media_type, file_id, _ = _extract_media(message)
    if not media_type:
        await message.answer(
            "No media found. Send /media_path with media or reply to a media message."
        )
        return

    file = await message.bot.get_file(file_id)
    await message.answer(
        f"media_type: {media_type}\n"
        f"file_path: {file.file_path}\n"
        "Download URL format: https://api.telegram.org/file/bot<TOKEN>/<file_path>"
    )


@router.message(Command("sticker_id"))
async def sticker_id(message: Message) -> None:
    source = _target_message(message)
    sticker = source.sticker
    if not sticker:
        await message.answer(
            "No sticker found. Send /sticker_id with a sticker or reply to one."
        )
        return

    await message.answer(
        "sticker_info\n"
        f"sticker_file_id: {sticker.file_id}\n"
        f"sticker_unique_id: {sticker.file_unique_id}\n"
        f"emoji: {sticker.emoji or '-'}\n"
        f"set_name: {sticker.set_name or '-'}\n"
        f"is_animated: {sticker.is_animated}\n"
        f"is_video: {sticker.is_video}"
    )


async def main() -> None:
    bot = Bot(token=config.TG_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    logger.info("Starting bot")
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Start bot and show greeting"),
            BotCommand(command="help", description="Show full command list"),
            BotCommand(command="ids", description="Show chat_id and user_id"),
            BotCommand(command="get_chat_id", description="Show current chat ID"),
            BotCommand(command="get_user_id", description="Show your Telegram user ID"),
            BotCommand(command="chat_info", description="Show detailed chat metadata"),
            BotCommand(command="media_id", description="Get file_id from any media"),
            BotCommand(command="media_path", description="Get Telegram file_path"),
            BotCommand(
                command="sticker_id", description="Get sticker IDs and set name"
            ),
        ]
    )

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

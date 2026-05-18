# TG Toolkit Bot

<div align="left">
<img src="media/icon.png" alt="Icon" width="300">
</div>
<p align="left">
Telegram toolkit bot for developers and advanced users:
quick IDs, chat metadata, and media technical info.
</p>

## Setup

- Python 3
- `uv`
- Telegram bot token from [@BotFather](https://t.me/BotFather)

```bash
uv sync
```

Create `.env` in project root:

```plaintext
TG_BOT_TOKEN=123456:your_bot_token_here
```

## Usage

```bash
uv run python app/main.py
```

Or with Docker Compose:

```bash
# set TG_BOT_TOKEN in .env
docker compose up --build -d
```

## Commands

- `/start` - bot status and intro
- `/help` - full command list
- `/ids` - `chat_id` + your `user_id` (+ `reply_user_id` if reply)
- `/get_chat_id` - current chat ID
- `/get_user_id` - your Telegram user ID
- `/get_my_id` - alias for `/get_user_id`
- `/chat_info` - detailed chat/user metadata
- `/media_id` - `file_id` + `file_unique_id` for attached/replied media
- `/media_path` - Telegram `file_path` for attached/replied media
- `/sticker_id` - sticker IDs and sticker set info

## License

[MIT](https://choosealicense.com/licenses/mit/)

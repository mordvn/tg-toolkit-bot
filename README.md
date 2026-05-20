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

- `/start` — intro
- `/help` — command list
- `/chat_info` — `chat_id`, chat type/title, your `user_id`; reply adds replied user
- `/msg_info` — message metadata: kind, forward, thread, text/location/contact/poll/dice/game/invoice/web_app
- `/file_info` — `file_id`, `file_unique_id`, `file_path` for photo/video/audio/voice/document/animation/video_note/sticker/paid media

Attach content or reply to any message when using toolkit commands.

## License

[MIT](https://choosealicense.com/licenses/mit/)

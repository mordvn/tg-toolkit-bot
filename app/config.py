from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    TG_BOT_TOKEN: str

    LOG_LEVEL: str = "INFO"

    OTEL_SERVICE_NAME: str = "tg-toolkit-bot"
    TRACE_ENABLED: bool = True
    METRICS_ENABLED: bool = True
    METRICS_EXPORT_INTERVAL_SEC: float = 30.0

    RATE_LIMIT_MAX: int = Field(default=20, ge=1)
    RATE_LIMIT_WINDOW_SEC: int = Field(default=60, ge=1)

    ALLOWED_USER_IDS: str = Field(
        default="",
        description="Comma-separated Telegram user IDs; empty = allow everyone",
    )

    @property
    def allowed_user_ids(self) -> frozenset[int]:
        if not self.ALLOWED_USER_IDS.strip():
            return frozenset()
        return frozenset(
            int(part.strip())
            for part in self.ALLOWED_USER_IDS.split(",")
            if part.strip()
        )


config = Config()

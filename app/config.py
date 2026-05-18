from pydantic_settings import BaseSettings


class Config(BaseSettings):
    TG_BOT_TOKEN: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


config = Config()

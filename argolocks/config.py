from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "ARGOLOCK_"}

    slack_bot_token: str = ""
    slack_channel_id: str = ""
    lock_timeout_seconds: int = 600
    host: str = "0.0.0.0"
    port: int = 8080


settings = Settings()


from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SNATCH"
    app_env: str = "development"
    debug: bool = True
    vonage_api_key: str = ""
    vonage_api_secret: str = ""
    vonage_sender_id: str = "SNATCH"
    sms_live_enabled: bool = False
    openai_api_key: str | None = None
    openai_model: str | None = None

    api_version: str = "v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

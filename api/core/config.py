import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    app_title: str = "SyJDWH Data API"
    app_version: str = "1.0.0"
    cors_origins: list[str] = field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", "*").split(",")
    )
    firebase_service_account_json: str | None = os.getenv(
        "FIREBASE_SERVICE_ACCOUNT_JSON"
    )
    database_url: str | None = os.getenv("DATABASE_URL")


settings = Settings()

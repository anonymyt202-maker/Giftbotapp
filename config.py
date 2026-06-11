from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: str = ""
    API_BASE_URL: str = "http://localhost:8000"
    SECRET_KEY: str = "changeme"
    PORT: int = 8000

    API_ID: int = 0
    API_HASH: str = ""

    DATABASE_URL: str = "sqlite+aiosqlite:///./giftbot.db"

    CARD_NUMBER: str = "5614681256483730"
    STARS_TO_UZS: int = 140
    REFERRAL_REWARD: int = 2

    class Config:
        env_file = ".env"

    @property
    def admin_ids(self) -> List[int]:
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip()]


settings = Settings()

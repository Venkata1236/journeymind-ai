from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # LLM
    openai_api_key: str

    # Database
    database_url: str

    # FAISS
    faiss_index_path: str = "faiss_index/"

    # Optional APIs (mock used if empty)
    weather_api_key: str = ""
    currency_api_key: str = ""

    # App
    environment: str = "development"
    max_trip_days: int = 30
    default_contingency_pct: float = 0.10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
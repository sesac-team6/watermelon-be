from datetime import date
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "watermelon-backend"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/watermelon"
    agri_weather_service_key: str = ""
    agri_weather_search_year: int = Field(default_factory=lambda: date.today().year)
    agri_weather_obsr_spot_cd: str = "137180A001"
    kamis_cert_key: str = ""
    kamis_cert_id: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

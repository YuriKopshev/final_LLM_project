"""Настройки приложения: только переменные окружения.

Порядок приоритета: реальное окружение > .env > профиль config/profiles/<APP_ENV>.env
"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    app_env: str
    yandex_api_key: str
    yandex_folder_id: str
    yandex_api_url: str
    yandex_model: str
    llm_timeout: float
    llm_max_retries: int
    llm_temperature: float
    llm_max_tokens: int
    cache_ttl: int
    log_level: str
    max_text_length: int


def load_settings() -> Settings:
    load_dotenv(ROOT / ".env")  # не перезаписывает уже заданные переменные
    app_env = os.getenv("APP_ENV", "dev")
    load_dotenv(ROOT / "config" / "profiles" / f"{app_env}.env")

    return Settings(
        app_env=app_env,
        yandex_api_key=os.getenv("YANDEX_API_KEY", ""),
        yandex_folder_id=os.getenv("YANDEX_FOLDER_ID", ""),
        yandex_api_url=os.environ["YANDEX_API_URL"],
        yandex_model=os.environ["YANDEX_MODEL"],
        llm_timeout=float(os.environ["LLM_TIMEOUT_SECONDS"]),
        llm_max_retries=int(os.environ["LLM_MAX_RETRIES"]),
        llm_temperature=float(os.environ["LLM_TEMPERATURE"]),
        llm_max_tokens=int(os.environ["LLM_MAX_TOKENS"]),
        cache_ttl=int(os.environ["CACHE_TTL_SECONDS"]),
        log_level=os.environ["LOG_LEVEL"].upper(),
        max_text_length=int(os.environ["MAX_TEXT_LENGTH"]),
    )

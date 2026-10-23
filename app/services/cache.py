"""Простой in-memory кеш с TTL."""
import hashlib
import logging
import time

from app.logging_setup import log

logger = logging.getLogger(__name__)


class TTLCache:
    def __init__(self, ttl: int):
        self.ttl = ttl
        self._data: dict[str, tuple[float, str]] = {}

    @staticmethod
    def make_key(scenario: str, text: str, model: str, temperature: float) -> str:
        raw = f"{scenario}|{model}|{temperature}|{text}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, key: str) -> str | None:
        item = self._data.get(key)
        if item and item[0] > time.monotonic():
            log(logger, logging.INFO, "cache_hit", key=key[:12])
            return item[1]
        if item:
            del self._data[key]  # протухшая запись
        log(logger, logging.INFO, "cache_miss", key=key[:12])
        return None

    def set(self, key: str, value: str) -> None:
        self._data[key] = (time.monotonic() + self.ttl, value)

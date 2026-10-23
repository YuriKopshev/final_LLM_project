"""Бизнес-логика: кеш → промпт → LLM → пост-обработка → fallback."""
import logging
import re
from dataclasses import dataclass

from app.config.settings import Settings
from app.llm.client import LLMError, YandexGPTClient
from app.llm.prompts import build_prompt
from app.logging_setup import log
from app.services.cache import TTLCache
from app.services.postprocess import EmptyResponseError, postprocess

logger = logging.getLogger(__name__)


@dataclass
class Result:
    scenario: str
    result: str
    cached: bool = False
    fallback: bool = False


def fallback_text(scenario: str, text: str) -> str:
    """Ответ без модели: первые предложения текста."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    head = " ".join(sentences[:3])[:500]
    return f"[Автоответ, модель недоступна] {head}"


class Pipeline:
    def __init__(self, settings: Settings, llm: YandexGPTClient, cache: TTLCache):
        self.s, self.llm, self.cache = settings, llm, cache

    def run(self, scenario: str, text: str) -> Result:
        log(logger, logging.INFO, "request_received", scenario=scenario, chars=len(text))

        key = self.cache.make_key(scenario, text, self.s.yandex_model, self.s.llm_temperature)
        cached = self.cache.get(key)
        if cached is not None:
            return Result(scenario, cached, cached=True)

        system, user = build_prompt(scenario, text)
        log(logger, logging.DEBUG, "prompt_built", prompt_chars=len(user))
        try:
            raw = self.llm.complete(system, user)
            answer = postprocess(scenario, raw)
        except (LLMError, EmptyResponseError) as e:
            log(logger, logging.ERROR, "fallback_used", reason=str(e))
            return Result(scenario, fallback_text(scenario, text), fallback=True)

        self.cache.set(key, answer)
        return Result(scenario, answer)

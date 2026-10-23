"""LLM-модуль: вызов YandexGPT с таймаутом и ретраями."""
import logging
import time

import httpx

from app.config.settings import Settings
from app.logging_setup import log

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Модель недоступна или вернула ошибку (после всех ретраев)."""


class YandexGPTClient:
    def __init__(self, settings: Settings):
        self.s = settings

    def complete(self, system: str, user: str) -> str:
        if not self.s.yandex_api_key or not self.s.yandex_folder_id:
            raise LLMError("YANDEX_API_KEY / YANDEX_FOLDER_ID не заданы")

        payload = {
            "modelUri": f"gpt://{self.s.yandex_folder_id}/{self.s.yandex_model}",
            "completionOptions": {
                "stream": False,
                "temperature": self.s.llm_temperature,
                "maxTokens": str(self.s.llm_max_tokens),
            },
            "messages": [
                {"role": "system", "text": system},
                {"role": "user", "text": user},
            ],
        }
        headers = {"Authorization": f"Api-Key {self.s.yandex_api_key}"}

        last_error: Exception | None = None
        for attempt in range(1, self.s.llm_max_retries + 2):
            try:
                log(logger, logging.INFO, "llm_request", attempt=attempt,
                    model=self.s.yandex_model)
                resp = httpx.post(self.s.yandex_api_url, json=payload, headers=headers,
                                  timeout=self.s.llm_timeout)
                resp.raise_for_status()
                text = resp.json()["result"]["alternatives"][0]["message"]["text"]
                log(logger, logging.INFO, "llm_response", chars=len(text))
                return text
            except httpx.HTTPStatusError as e:
                last_error = e
                log(logger, logging.ERROR, "llm_http_error", status=e.response.status_code,
                    body=e.response.text[:300])
                # 4xx (кроме 429) повторять бессмысленно
                if e.response.status_code < 500 and e.response.status_code != 429:
                    break
            except (httpx.TransportError, KeyError, IndexError, ValueError) as e:
                last_error = e
            log(logger, logging.ERROR, "llm_error", attempt=attempt,
                error=repr(last_error))
            time.sleep(min(2 ** (attempt - 1) * 0.5, 4))

        raise LLMError(f"LLM недоступна: {last_error!r}")

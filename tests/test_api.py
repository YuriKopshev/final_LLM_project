import dataclasses
import time

import pytest
from fastapi.testclient import TestClient

from app.config.settings import load_settings
from app.llm.client import LLMError
from app.main import create_app

TEXT = "Это достаточно длинный текст статьи про подкасты и контент. " * 3


class FakeLLM:
    def __init__(self, answer="Заголовок\n• мысль один\n• мысль два", fail=False):
        self.answer, self.fail, self.calls = answer, fail, 0

    def complete(self, system, user):
        self.calls += 1
        if self.fail:
            raise LLMError("boom")
        return self.answer


def make_client(llm, **over):
    s = dataclasses.replace(load_settings(), **over)
    return TestClient(create_app(s, llm))


def test_success():
    c = make_client(FakeLLM())
    r = c.post("/process", json={"scenario": "summary", "text": TEXT})
    assert r.status_code == 200
    body = r.json()
    assert body["fallback"] is False and body["cached"] is False
    assert "мысль" in body["result"]


@pytest.mark.parametrize("payload", [
    {"scenario": "summary", "text": "коротко"},
    {"scenario": "unknown", "text": TEXT},
    {"scenario": "summary"},
])
def test_validation_error(payload):
    c = make_client(FakeLLM())
    assert c.post("/process", json=payload).status_code == 422


def test_too_long():
    c = make_client(FakeLLM(), max_text_length=100)
    assert c.post("/process", json={"scenario": "faq", "text": TEXT * 5}).status_code == 413


def test_fallback_when_llm_down():
    c = make_client(FakeLLM(fail=True))
    r = c.post("/process", json={"scenario": "summary", "text": TEXT})
    assert r.status_code == 200 and r.json()["fallback"] is True


def test_cache_hit_and_not_cached_fallback():
    llm = FakeLLM()
    c = make_client(llm)
    req = {"scenario": "summary", "text": TEXT}
    assert c.post("/process", json=req).json()["cached"] is False
    assert c.post("/process", json=req).json()["cached"] is True
    assert llm.calls == 1
    # другой сценарий -> другой ключ
    assert c.post("/process", json={**req, "scenario": "faq"}).json()["cached"] is False


def test_cache_ttl_expires():
    llm = FakeLLM()
    c = make_client(llm, cache_ttl=1)
    req = {"scenario": "summary", "text": TEXT}
    c.post("/process", json=req)
    time.sleep(1.1)
    assert c.post("/process", json=req).json()["cached"] is False


def test_headlines_postprocess_requires_five():
    c = make_client(FakeLLM(answer="1. Один заголовок только"))
    r = c.post("/process", json={"scenario": "headlines", "text": TEXT})
    assert r.json()["fallback"] is True


def test_health():
    assert make_client(FakeLLM()).get("/health").json() == {"status": "ok"}

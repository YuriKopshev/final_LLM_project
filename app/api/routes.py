"""HTTP API: приём и валидация запросов."""
import logging
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)
router = APIRouter()


class ProcessRequest(BaseModel):
    scenario: Literal["summary", "headlines", "faq"]
    text: str = Field(..., description="Текст статьи или подкаста")

    @field_validator("text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 50:
            raise ValueError("Текст слишком короткий (минимум 50 символов)")
        return v


class ProcessResponse(BaseModel):
    scenario: str
    result: str
    cached: bool
    fallback: bool


@router.get("/", include_in_schema=False)
def index():
    return FileResponse(Path(__file__).resolve().parents[1] / "static" / "index.html")


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/process", response_model=ProcessResponse)
def process(body: ProcessRequest, request: Request):
    pipeline = request.app.state.pipeline
    max_len = request.app.state.settings.max_text_length
    if len(body.text) > max_len:
        raise HTTPException(413, f"Текст длиннее {max_len} символов")
    try:
        res = pipeline.run(body.scenario, body.text)
    except Exception as e:  # непредвиденная внутренняя ошибка
        logger.exception("internal_error")
        raise HTTPException(500, "Внутренняя ошибка сервиса") from e
    return ProcessResponse(**res.__dict__)

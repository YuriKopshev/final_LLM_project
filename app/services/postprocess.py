"""Пост-обработка: проверка и очистка ответа модели."""
import re


class EmptyResponseError(Exception):
    pass


def clean(text: str) -> str:
    text = re.sub(r"[*_`#]+", "", text)          # markdown-мусор
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def postprocess(scenario: str, raw: str) -> str:
    text = clean(raw)
    if len(text) < 10:
        raise EmptyResponseError("Модель вернула пустой или слишком короткий ответ")
    if scenario == "headlines" and len(re.findall(r"^\s*\d[.)]", text, re.MULTILINE)) < 5:
        raise EmptyResponseError("В ответе нет 5 пронумерованных заголовков")
    return text

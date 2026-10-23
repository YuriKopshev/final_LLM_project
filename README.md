# Ассистент контент-мейкера (LLM-сервис на YandexGPT)

Учебный HTTP-сервис на FastAPI. Принимает текст статьи/подкаста и выполняет один из сценариев:

| `scenario`  | Что делает |
|-------------|-----------|
| `summary`   | Саммари-пост для Telegram с ключевыми мыслями |
| `headlines` | 5 цепляющих заголовков + 2 кликбейтные цитаты |
| `faq`       | FAQ: 5 вопросов и ответов по тексту |

## Архитектура

```
POST /process → api/routes.py (валидация)
             → services/pipeline.py (кеш → промпт → LLM → пост-обработка → fallback)
                  ├─ services/cache.py        TTL-кеш
                  ├─ llm/prompts.py + client.py   промпты, YandexGPT, таймаут, ретраи
                  └─ services/postprocess.py  очистка и проверка ответа
config/profiles/{dev,prod}.env  — несекретные настройки; app/config/settings.py — загрузка
```

## Запуск

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # впишите YANDEX_API_KEY и YANDEX_FOLDER_ID
uvicorn app.main:app --reload
```
Веб-интерфейс: http://127.0.0.1:8000/ (удобно для скриншотов), Swagger: http://127.0.0.1:8000/docs

Ключ: консоль Yandex Cloud → сервисный аккаунт с ролью `ai.languageModels.user` → API-ключ; `FOLDER_ID` — id каталога.

## Конфигурация

Приоритет: переменные окружения > `.env` > `config/profiles/<APP_ENV>.env`. `APP_ENV=dev|prod`.
Все параметры (URL, модель, таймаут, ретраи, TTL кеша, лимит текста, уровень логов) — в `.env.example`.
`.env` в `.gitignore`, в репозитории только `.env.example`.

## API

`POST /process`
```bash
curl -X POST http://127.0.0.1:8000/process -H 'Content-Type: application/json' \
  -d '{"scenario":"summary","text":"<текст не короче 50 символов>"}'
```
Ответ 200:
```json
{"scenario":"summary","result":"Заголовок\n• ...","cached":false,"fallback":false}
```

| Код | Когда |
|-----|-------|
| 200 | Успех. `fallback:true` — модель недоступна, вернулся автоответ (первые предложения текста) |
| 413 | Текст длиннее `MAX_TEXT_LENGTH` |
| 422 | Ошибка валидации (неизвестный сценарий, текст < 50 символов, нет поля) |
| 500 | Внутренняя ошибка |

`GET /health` → `{"status":"ok"}`

## Отказоустойчивость, кеш, логи

- Таймаут и ретраи с экспоненциальной паузой на сетевые ошибки, 5xx и 429; при отказе — fallback.
- Кеш в памяти: ключ = sha256(сценарий + модель + температура + текст), TTL из `CACHE_TTL_SECONDS`. Fallback-ответы не кешируются.
- JSON-логи: `request_received`, `cache_hit`/`cache_miss`, `prompt_built`, `llm_request`, `llm_response`, `llm_error`, `fallback_used`.

## Тесты и линтер

```bash
ruff check . && pytest -q
```
Результаты проверок — в [TESTING.md](TESTING.md). CI: `.github/workflows/ci.yml`.

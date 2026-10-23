## Цель
Учебный end-to-end LLM-сервис «Ассистент контент-мейкера» (summary / headlines / faq) на FastAPI + YandexGPT с CI, конфигами через окружение и кешем.

## Архитектура
- **api/** — FastAPI, валидация (pydantic), коды 200/413/422/500
- **services/** — `pipeline` (бизнес-логика), `cache` (TTL), `postprocess` (очистка/проверка)
- **llm/** — промпты (system+user), клиент YandexGPT: таймаут, ретраи, `LLMError`
- **config/** — профили dev/prod + загрузка настроек из env
- Fallback при недоступности LLM; структурированные JSON-логи

## Чек-лист самопроверки
- [x] Сервис запускается одной командой (`uvicorn app.main:app`)
- [x] Разделение API / LLM / бизнес-логика / пост-обработка
- [x] Валидация входа → 422/413
- [x] Таймауты, ретраи, fallback при сбое LLM
- [x] Кеш с TTL, логи cache hit/miss
- [x] Структурированные логи с уровнями
- [x] Конфиг через env, dev/prod профили, без хардкода
- [x] `.env` в `.gitignore`, есть `.env.example`, секретов в коде нет
- [x] CI: линтер + тесты + установка зависимостей
- [x] README и TESTING.md

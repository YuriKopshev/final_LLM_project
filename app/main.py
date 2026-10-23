from fastapi import FastAPI

from app.api.routes import router
from app.config.settings import Settings, load_settings
from app.llm.client import YandexGPTClient
from app.logging_setup import setup_logging
from app.services.cache import TTLCache
from app.services.pipeline import Pipeline


def create_app(settings: Settings | None = None, llm=None) -> FastAPI:
    settings = settings or load_settings()
    setup_logging(settings.log_level)
    app = FastAPI(title="Content Maker Assistant")
    app.state.settings = settings
    app.state.pipeline = Pipeline(settings, llm or YandexGPTClient(settings),
                                  TTLCache(settings.cache_ttl))
    app.include_router(router)
    return app


app = create_app()

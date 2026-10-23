"""Структурированные (JSON) логи."""
import json
import logging


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "time": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        data.update(getattr(record, "extra_fields", {}))
        return json.dumps(data, ensure_ascii=False)


def setup_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
    for noisy in ("httpx", "httpcore", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def log(logger: logging.Logger, level: int, event: str, **fields) -> None:
    logger.log(level, event, extra={"extra_fields": fields})

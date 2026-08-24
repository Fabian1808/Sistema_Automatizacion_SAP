from __future__ import annotations

import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional


class JsonFormatter(logging.Formatter):
    """Formateador estructurado JSON para logs de producción."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        extra = getattr(record, "extra_fields", None)
        if extra:
            payload.update(extra)
        return json.dumps(payload, ensure_ascii=False)


class LogService:
    """Configura logging rotativo + consola. Un logger por módulo."""

    LOG_DIR_NAME = "logs"
    MAX_BYTES = 5 * 1024 * 1024
    BACKUP_COUNT = 5

    def __init__(self, log_dir: Optional[Path] = None, app_name: str = "SapDocumentAutomation"):
        if log_dir is None:
            log_dir = Path.home() / "AppData" / "Roaming" / app_name / self.LOG_DIR_NAME
        self.log_dir = Path(log_dir)
        self._configured = False

    def setup(self, level: int = logging.INFO) -> None:
        if self._configured:
            return
        self.log_dir.mkdir(parents=True, exist_ok=True)
        root = logging.getLogger()
        root.setLevel(level)

        # File handler rotativo con formato JSON
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "app.log",
            maxBytes=self.MAX_BYTES,
            backupCount=self.BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(JsonFormatter())

        # Console handler legible
        console = logging.StreamHandler()
        console.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )

        root.addHandler(file_handler)
        if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) for h in root.handlers):
            root.addHandler(console)
        self._configured = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

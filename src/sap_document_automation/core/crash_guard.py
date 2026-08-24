"""Instala guardianes globales de errores para que la app nunca muera en silencio.

Cubre: excepciones no capturadas (hilo principal), excepciones en threads,
warnings/errores de Qt y crashes nativos (faulthandler). Todo queda en el log.
"""
from __future__ import annotations

import faulthandler
import logging
import sys
import threading
from pathlib import Path


def install_crash_handlers(log_dir: Path) -> None:
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log = logging.getLogger("crash")

    # Crashes nativos (access violation, etc.)
    try:
        fault_file = open(log_dir / "faults.log", "a", encoding="utf-8")
        faulthandler.enable(file=fault_file)
    except Exception:
        pass

    def _log_exception(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        log.critical(
            "Excepcion no capturada",
            exc_info=(exc_type, exc_value, exc_tb),
        )

    def _thread_exception(args):
        log.critical(
            f"Excepcion en hilo {args.thread.name if args.thread else '?'}",
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )

    sys.excepthook = _log_exception
    if hasattr(threading, "excepthook"):
        threading.excepthook = _thread_exception

    try:
        from PySide6.QtCore import qInstallMessageHandler, QtMsgType

        levels = {
            QtMsgType.QtDebugMsg: logging.DEBUG,
            QtMsgType.QtInfoMsg: logging.INFO,
            QtMsgType.QtWarningMsg: logging.WARNING,
            QtMsgType.QtCriticalMsg: logging.ERROR,
            QtMsgType.QtFatalMsg: logging.CRITICAL,
        }

        def qt_handler(mode, context, message):
            log.log(levels.get(mode, logging.WARNING), "Qt: %s", message)

        qInstallMessageHandler(qt_handler)
    except Exception:
        pass

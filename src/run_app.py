"""Punto de entrada de la aplicación (src layout).

Ejecutar: python -m sap_document_automation
o:        python src/run_app.py
"""
from __future__ import annotations

import sys
from pathlib import Path


def _ensure_src_on_path() -> None:
    src = Path(__file__).resolve().parent.parent / "src"
    if src.exists() and str(src) not in sys.path:
        sys.path.insert(0, str(src))


def main() -> int:
    _ensure_src_on_path()

    from sap_document_automation.core.exceptions import SapError
    from sap_document_automation.services.log_service import LogService

    log_service = LogService()
    import logging
    import os

    log_service.setup(
        level=logging.DEBUG if os.environ.get("SAPDOC_DEBUG") else logging.INFO
    )
    from sap_document_automation.core.crash_guard import install_crash_handlers

    install_crash_handlers(log_service.log_dir)
    log = logging.getLogger(__name__)

    try:
        from PySide6.QtWidgets import QApplication

        from sap_document_automation.ui.design import build_stylesheet

        app = QApplication(sys.argv)
        app.setApplicationName("SAP Document Automation")
        app.setOrganizationName("Fabian1808")
        app.setStyleSheet(build_stylesheet())

        # UI principal: se resuelve desde el paquete legacy mientras dura la migración
        try:
            from sap_document_automation.services.config_service import ConfigService

            from sap_document_automation.ui.main_window import MainWindow  # type: ignore
        except ImportError:
            log.warning("UI legacy no disponible; mostrando ventana placeholder")
            from PySide6.QtWidgets import QLabel

            win = QLabel("SAP Document Automation v1.0.0\n(UI en construcción)")
            win.setWindowTitle("SAP Document Automation")
            win.resize(480, 240)
            win.show()
            return app.exec()

        window = MainWindow(ConfigService(), LogService())
        window.show()
        return app.exec()

    except SapError as exc:
        log.error("Error de aplicación: %s", exc)
        return 1
    except Exception:
        log.exception("Error inesperado al iniciar")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

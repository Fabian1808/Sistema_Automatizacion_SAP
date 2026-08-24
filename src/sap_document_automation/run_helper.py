"""Helper de arranque compartido entre __main__.py y run_app.py."""
from __future__ import annotations

import sys
from pathlib import Path


def _ensure_src_on_path() -> None:
    src = Path(__file__).resolve().parent.parent
    if src.exists() and str(src) not in sys.path:
        sys.path.insert(0, str(src))


def main() -> int:
    _ensure_src_on_path()

    from sap_document_automation.core.exceptions import SapError
    from sap_document_automation.services.log_service import LogService

    LogService().setup()
    import logging

    log = logging.getLogger(__name__)

    try:
        from PySide6.QtWidgets import QApplication, QLabel

        from sap_document_automation.ui.design import build_stylesheet

        app = QApplication(sys.argv)
        app.setApplicationName("SAP Document Automation")
        app.setOrganizationName("Fabian1808")
        app.setStyleSheet(build_stylesheet())

        try:
            from sap_document_automation.services.config_service import ConfigService

            from sap_document_automation.ui.main_window import MainWindow  # type: ignore
            window = MainWindow(ConfigService(), LogService())
        except ImportError:
            log.warning("UI legacy no disponible; mostrando ventana placeholder")
            window = QLabel("SAP Document Automation v1.0.0\n(UI en construcción)")
            window.setWindowTitle("SAP Document Automation")
            window.resize(480, 240)

        window.show()
        return app.exec()

    except SapError as exc:
        log.error("Error de aplicación: %s", exc)
        return 1
    except Exception:
        log.exception("Error inesperado al iniciar")
        return 2

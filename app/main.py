import sys

from PySide6.QtWidgets import QApplication

from app.services.config_service import ConfigService
from app.services.log_service import LogService
from app.ui.main_window import MainWindow


def main():
    config = ConfigService()
    log_service = LogService(config.logs_folder)
    app = QApplication(sys.argv)
    app.setApplicationName("SAP Document Automation")
    window = MainWindow(config, log_service)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
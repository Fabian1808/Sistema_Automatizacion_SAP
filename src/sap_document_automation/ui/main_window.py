from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from .help_view import HelpView
from .hes_view import HesView
from .history_view import HistoryView
from .macro_view import MacroView
from .oc_view import OcView
from .sap_status_widget import SapStatusWidget
from .settings_view import SettingsView

QSS = """
QMainWindow, QStackedWidget { background: #f5f6fa; }
QListWidget#sidebar {
    background: #1f2937;
    color: #e5e7eb;
    border: none;
    font-size: 14px;
    padding-top: 12px;
    outline: 0;
}
QListWidget#sidebar::item { padding: 10px 14px; border-radius: 6px; margin: 2px 6px; }
QListWidget#sidebar::item:selected { background: #2563eb; color: #ffffff; }
QListWidget#sidebar::item:hover { background: #374151; }
QLabel#title { font-size: 20px; font-weight: bold; color: #111827; }
QLabel#subtitle { font-size: 13px; color: #6b7280; }
QPushButton {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    color: #111827;
}
QPushButton:hover { background: #f3f4f6; }
QPushButton:disabled { color: #9ca3af; background: #e5e7eb; }
QPushButton#primary {
    background: #2563eb;
    border: none;
    color: #ffffff;
    font-weight: bold;
    padding: 12px 24px;
    font-size: 14px;
}
QPushButton#primary:hover { background: #1d4ed8; }
QPushButton#primary:disabled { background: #93c5fd; color: #eff6ff; }
QPlainTextEdit, QTextEdit, QLineEdit {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 8px;
    font-size: 13px;
}
QPlainTextEdit:focus, QTextEdit:focus, QLineEdit:focus { border: 1px solid #2563eb; }
QProgressBar {
    border: none;
    border-radius: 6px;
    background: #e5e7eb;
    height: 14px;
    text-align: center;
    font-size: 11px;
}
QProgressBar::chunk { background: #2563eb; border-radius: 6px; }
QStatusBar { background: #ffffff; border-top: 1px solid #e5e7eb; }
"""


class MainWindow(QMainWindow):
    def __init__(self, config, log_service):
        super().__init__()
        self.config = config
        self.log_service = log_service
        self.setWindowTitle("SAP Document Automation")
        self.resize(1000, 650)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.menu = QListWidget()
        self.menu.setObjectName("sidebar")
        self.menu.setFixedWidth(190)
        for label in (
            "HES",
            "Órdenes de Compra",
            "Macros",
            "Historial",
            "Configuración",
            "Ayuda",
        ):
            item = QListWidgetItem(label)
            item.setSizeHint(QSize(0, 44))
            self.menu.addItem(item)

        self.stack = QStackedWidget()
        self.hes_view = HesView(self.config, self.log_service)
        self.oc_view = OcView()
        self.macro_view = MacroView(self.config, self.log_service)
        self.history_view = HistoryView()
        self.settings_view = SettingsView(self.config)
        self.help_view = HelpView()
        self.stack.addWidget(self.hes_view)
        self.stack.addWidget(self.oc_view)
        self.stack.addWidget(self.macro_view)
        self.stack.addWidget(self.history_view)
        self.stack.addWidget(self.settings_view)
        self.stack.addWidget(self.help_view)

        layout.addWidget(self.menu)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self.sap_status = SapStatusWidget(self.config)
        self.statusBar().addPermanentWidget(self.sap_status)

        self.menu.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.menu.setCurrentRow(0)
        self.setStyleSheet(QSS)
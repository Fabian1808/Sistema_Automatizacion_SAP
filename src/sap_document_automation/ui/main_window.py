from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from .hes_view import HesView
from .sap_status_widget import SapStatusWidget

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

VIEW_FACTORIES = {
    0: lambda w: HesView(w.config, w.log_service),
    1: lambda w: _import_oc()(w),
    2: lambda w: _import_macro()(w.config, w.log_service),
    3: lambda w: _import_history()(w),
    4: lambda w: _import_settings()(w.config),
    5: lambda w: _import_help()(w),
}


def _import_oc():
    from .oc_view import OcView

    return OcView


def _import_macro():
    from .macro_view import MacroView

    return MacroView


def _import_history():
    from .history_view import HistoryView

    return HistoryView


def _import_settings():
    from .settings_view import SettingsView

    return SettingsView


def _import_help():
    from .help_view import HelpView

    return HelpView


class MainWindow(QMainWindow):
    def __init__(self, config, log_service):
        super().__init__()
        self.config = config
        self.log_service = log_service
        self.setWindowTitle("SAP Document Automation")
        self.resize(1000, 650)
        self._views = {}

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
        self._ensure_view(0)

        layout.addWidget(self.menu)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self.sap_status = SapStatusWidget(self.config)
        self.statusBar().addPermanentWidget(self.sap_status)

        self.menu.currentRowChanged.connect(self._on_navigate)
        self.menu.setCurrentRow(0)
        self.setStyleSheet(QSS)

    def _on_navigate(self, index: int):
        self._ensure_view(index)
        self.stack.setCurrentIndex(index)

    def _ensure_view(self, index: int):
        if index in self._views:
            return
        view = VIEW_FACTORIES[index](self)
        self.stack.insertWidget(index, view)
        self._views[index] = view

    @property
    def hes_view(self):
        return self._views[0]

    @property
    def oc_view(self):
        self._ensure_view(1)
        return self._views[1]

    @property
    def macro_view(self):
        self._ensure_view(2)
        return self._views[2]

    @property
    def history_view(self):
        self._ensure_view(3)
        return self._views[3]

    @property
    def settings_view(self):
        self._ensure_view(4)
        return self._views[4]

    @property
    def help_view(self):
        self._ensure_view(5)
        return self._views[5]

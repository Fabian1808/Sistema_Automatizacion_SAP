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
from .macros_view import MacrosView
from .sap_status_widget import SapStatusWidget

VIEW_FACTORIES = {
    0: lambda w: MacrosView(w.config, w.log_service),
    1: lambda w: HesView(w.config, w.log_service),
    2: lambda w: _import_oc()(),
    3: lambda w: _import_macro()(w.config, w.log_service),
    4: lambda w: _import_history()(),
    5: lambda w: _import_settings()(w.config),
    6: lambda w: _import_help()(),
}

MENU_LABELS = (
    "Automatizaciones",
    "HES",
    "Órdenes de Compra",
    "Macros VBS",
    "Historial",
    "Configuración",
    "Ayuda",
)


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
        for label in MENU_LABELS:
            item = QListWidgetItem(label)
            item.setSizeHint(QSize(0, 44))
            self.menu.addItem(item)

        self.stack = QStackedWidget()
        self._ensure_view(0)  # solo la pantalla inicial; resto bajo demanda

        layout.addWidget(self.menu)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self.sap_status = SapStatusWidget(self.config)
        self.statusBar().addPermanentWidget(self.sap_status)

        self.menu.currentRowChanged.connect(self._on_navigate)
        self.menu.setCurrentRow(0)
        macros_view = self._views[0]
        macros_view.macro_selected.connect(self._on_macro_selected)

    def _on_navigate(self, index: int):
        self._ensure_view(index)
        view = self._views.get(index)
        if index == 0 and hasattr(view, "refresh_last_runs"):
            view.refresh_last_runs()
        self.stack.setCurrentIndex(index)

    def _on_macro_selected(self, module_id: str):
        targets = {"hes": 1, "oc": 2, "vbs": 3}
        index = targets.get(module_id)
        if index is not None:
            self.menu.setCurrentRow(index)

    def navigate_to(self, index: int):
        self.menu.setCurrentRow(index)

    def _ensure_view(self, index: int):
        if index in self._views:
            return
        view = VIEW_FACTORIES[index](self)
        self.stack.insertWidget(index, view)
        self._views[index] = view

    # Accesos compatibles para tests / código existente
    @property
    def macros_view(self):
        return self._views[0]

    @property
    def hes_view(self):
        return self._views[1]

    @property
    def oc_view(self):
        self._ensure_view(2)
        return self._views[2]

    @property
    def macro_view(self):
        self._ensure_view(3)
        return self._views[3]

    @property
    def history_view(self):
        self._ensure_view(4)
        return self._views[4]

    @property
    def settings_view(self):
        self._ensure_view(5)
        return self._views[5]

    @property
    def help_view(self):
        self._ensure_view(6)
        return self._views[6]

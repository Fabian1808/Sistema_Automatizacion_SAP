from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..modules.registry import build_default_registry
from ..services.state_service import StateService

STATUS_LABELS = {
    "RUNNING": "En curso",
    "COMPLETED": "Exitoso",
    "PARTIAL": "Parcial",
    "CANCELLED": "Cancelado",
    "FAILED": "Fallido",
}


def _last_run_label(module_id: str) -> str:
    try:
        service = StateService()
        for batch in service.list_batches(limit=15):
            if batch.get("module_id") == module_id:
                status = STATUS_LABELS.get(batch.get("status") or "", "")
                ok = batch.get("ok_count") or 0
                fail = batch.get("failed_count") or 0
                return f"Última ejecución: {status} ({ok} OK / {fail} errores)" if status else ""
    except Exception:
        pass
    return "Sin ejecuciones registradas"


class MacroCard(QFrame):
    selected = Signal(str)

    def __init__(self, meta):
        super().__init__()
        self.module_id = meta["id"]
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        header = QHBoxLayout()
        name = QLabel(meta["name"])
        name.setObjectName("cardTitle")
        header.addWidget(name)
        header.addStretch(1)
        chip = QLabel("Disponible" if meta["available"] else "Próximamente")
        chip.setObjectName("chipOk" if meta["available"] else "chipSoon")
        header.addWidget(chip)
        layout.addLayout(header)

        desc = QLabel(meta["description"])
        desc.setWordWrap(True)
        layout.addWidget(desc)

        docs = QLabel(f"<b>Acepta:</b> {meta['accepted_documents']}")
        docs.setWordWrap(True)
        docs.setObjectName("subtitle")
        layout.addWidget(docs)

        self.last_run = QLabel(_last_run_label(self.module_id))
        self.last_run.setObjectName("subtitle")
        layout.addWidget(self.last_run)

        row = QHBoxLayout()
        row.addStretch(1)
        button = QPushButton("Ejecutar")
        button.setEnabled(bool(meta["available"]))
        if meta["available"]:
            button.clicked.connect(lambda: self.selected.emit(self.module_id))
        row.addWidget(button)
        layout.addLayout(row)


class MacrosView(QWidget):
    """Centro de automatizaciones: catálogo dinámico desde el registro."""

    macro_selected = Signal(str)

    EXTRA_CARDS = [
        {
            "id": "vbs",
            "name": "Macros personalizadas (VBS)",
            "description": (
                "Cree, importe o edite macros grabadas en SAP GUI y ejecútelas "
                "con listas de documentos."
            ),
            "accepted_documents": "Según la macro configurada",
            "available": True,
        }
    ]

    def __init__(self, config=None, log_service=None):
        super().__init__()
        self._config = config
        self._log_service = log_service

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Centro de Automatizaciones")
        title.setObjectName("title")
        subtitle = QLabel(
            "Seleccione una automatización para comenzar. Las nuevas macros que se "
            "incorporen al sistema aparecerán aquí automáticamente."
        )
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        grid = QGridLayout()
        grid.setSpacing(12)
        metas = build_default_registry().metadata() + list(self.EXTRA_CARDS)
        for position, meta in enumerate(metas):
            card = MacroCard(meta)
            card.selected.connect(self.macro_selected.emit)
            grid.addWidget(card, position // 2, position % 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)
        layout.addStretch(1)

    def refresh_last_runs(self):
        for card in self.findChildren(MacroCard):
            card.last_run.setText(_last_run_label(card.module_id))

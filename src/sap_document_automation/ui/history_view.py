from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..core.error_catalog import explain_error
from ..services.state_service import DocumentState, StateService

STATUS_LABELS = {
    "RUNNING": "En curso",
    "COMPLETED": "Exitoso",
    "PARTIAL": "Parcial",
    "CANCELLED": "Cancelado",
    "FAILED": "Fallido",
}
PAGE_SIZE = 100


def _format_duration(seconds) -> str:
    try:
        seconds = int(float(seconds or 0))
    except (TypeError, ValueError):
        return "-"
    if seconds <= 0:
        return "-"
    minutes, secs = divmod(seconds, 60)
    return f"{minutes}m {secs:02d}s" if minutes else f"{secs}s"


def _batch_display_status(batch: dict) -> str:
    status = batch.get("status") or ""
    if status:
        return STATUS_LABELS.get(status, status)
    # Lotes antiguos sin estado: inferir
    if batch.get("failed_count"):
        return "Parcial"
    return "Exitoso"


def _split_timestamp(value: str):
    try:
        moment = datetime.fromisoformat(value)
        return moment.strftime("%d/%m/%Y"), moment.strftime("%H:%M:%S")
    except (TypeError, ValueError):
        return "-", "-"


class BatchDetailDialog(QDialog):
    """Muestra los documentos de un lote y el detalle comprensible de errores."""

    def __init__(self, batch_id: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Detalle del lote {batch_id}")
        self.resize(720, 480)
        self._state = StateService()

        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Documento", "Estado", "Duración (s)", "Archivo"]
        )
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table, 2)

        detail_title = QLabel("Seleccione un documento fallido para ver el detalle:")
        detail_title.setObjectName("subtitle")
        layout.addWidget(detail_title)

        self.detail_pane = QLabel("—")
        self.detail_pane.setWordWrap(True)
        self.detail_pane.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.detail_pane.setStyleSheet("padding: 8px;")
        layout.addWidget(self.detail_pane, 1)

        close = QPushButton("Cerrar")
        close.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(close)
        layout.addLayout(row)

        state_labels = {
            DocumentState.SUCCESS.value: "✅ Exitoso",
            DocumentState.FAILED.value: "❌ Fallido",
            DocumentState.SKIPPED_DUPLICATE.value: "⧉ Duplicado",
            DocumentState.PENDING.value: "⏳ Pendiente",
            DocumentState.PROCESSING.value: "⚙ Procesando",
            DocumentState.RETRY.value: "↻ Reintento",
        }
        documents = self._state.get_documents(batch_id)
        for record in documents:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(record.document_id))
            self.table.setItem(
                r, 1, QTableWidgetItem(state_labels.get(record.state.value, record.state.value))
            )
            self.table.setItem(r, 2, QTableWidgetItem(f"{record.duration:.1f}"))
            self.table.setItem(r, 3, QTableWidgetItem(record.file_path or "-"))
            if record.state == DocumentState.FAILED and record.error:
                for col in range(4):
                    item = self.table.item(r, col)
                    if item:
                        item.setToolTip(record.error)
        self.table.cellClicked.connect(self._on_row)

        self._errors = {
            rec.document_id: rec.error
            for rec in documents
            if rec.state == DocumentState.FAILED
        }

    def _on_row(self, row: int, _column: int):
        doc_id = self.table.item(row, 0).text()
        error = self._errors.get(doc_id)
        if error is None:
            self.detail_pane.setText("Documento procesado correctamente.")
            return
        info = explain_error(error)
        self.detail_pane.setText(
            f"<b>Estado:</b> ❌ Fallido<br>"
            f"<b>Motivo:</b> {info['motivo']}<br>"
            f"<b>Detalle:</b> {info['detalle']}<br>"
            f"<b>Etapa:</b> {info['etapa']}<br>"
            f"<b>Recomendación:</b> {info['recomendacion']}<br>"
            f"<small><b>Técnico:</b> {error}</small>"
        )


class HistoryView(QWidget):
    """Historial de ejecuciones con carga asíncrona y filtros."""

    _data_ready = Signal(list)

    def __init__(self):
        super().__init__()
        self._loaded = False
        self._rows = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Historial de ejecuciones")
        title.setObjectName("title")
        layout.addWidget(title)

        toolbar = QHBoxLayout()
        self.filter = QComboBox()
        self.filter.addItems(
            ["Todas", "Exitosas", "Parciales", "Fallidas", "Canceladas", "En curso"]
        )
        self.filter.currentIndexChanged.connect(self._apply_filter)
        btn_refresh = QPushButton("Actualizar")
        btn_refresh.clicked.connect(self._load_async)
        toolbar.addWidget(QLabel("Estado:"))
        toolbar.addWidget(self.filter)
        toolbar.addStretch(1)
        toolbar.addWidget(btn_refresh)
        layout.addLayout(toolbar)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            [
                "Fecha",
                "Hora",
                "Usuario",
                "Macro",
                "Docs",
                "✅ OK",
                "❌ Errores",
                "Estado",
                "Duración",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.cellDoubleClicked.connect(self._open_detail)
        layout.addWidget(self.table, 1)

        hint = QLabel("Doble clic en una ejecución para ver el detalle por documento.")
        hint.setObjectName("subtitle")
        layout.addWidget(hint)

        self._data_ready.connect(self._fill_table)

    def showEvent(self, event):
        if not self._loaded:
            self._load_async()
        super().showEvent(event)

    def _load_async(self):
        self._loaded = True
        import threading

        def worker():
            try:
                service = StateService()
                rows = service.list_batches(limit=200)
            except Exception:
                rows = []
            self._data_ready.emit(rows)

        threading.Thread(target=worker, daemon=True).start()

    def _fill_table(self, rows):
        self._rows = rows
        self._apply_filter()

    def _apply_filter(self):
        choice = self.filter.currentText()
        mapping = {
            "Exitosas": ("COMPLETED", "Exitoso"),
            "Parciales": ("PARTIAL", "Parcial"),
            "Fallidas": ("FAILED", "Fallido"),
            "Canceladas": ("CANCELLED", "Cancelado"),
            "En curso": ("RUNNING", "En curso"),
        }
        table = self.table
        table.setRowCount(0)
        for batch in self._rows:
            display = _batch_display_status(batch)
            if choice in mapping and display not in mapping[choice]:
                continue
            date, time_part = _split_timestamp(batch.get("created_at", ""))
            row = table.rowCount()
            table.insertRow(row)
            values = [
                date,
                time_part,
                batch.get("username") or "-",
                batch.get("module_id", "").upper(),
                str(batch.get("total_documents", 0)),
                str(batch.get("ok_count") or 0),
                str(batch.get("failed_count") or 0),
                display,
                _format_duration(batch.get("total_duration")),
            ]
            for column, value in enumerate(values):
                table.setItem(row, column, QTableWidgetItem(value))
            table.item(row, 0).setData(Qt.ItemDataRole.UserRole, batch.get("batch_id"))

    def _open_detail(self, row: int, _column: int):
        batch_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if batch_id:
            BatchDetailDialog(batch_id, self).exec()

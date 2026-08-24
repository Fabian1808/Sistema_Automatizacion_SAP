from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..macros.macro_model import ACTION_LABELS
from ..macros.macro_service import MacroService
from .macro_editor import MacroEditorDialog, read_vbs_text
from .run_panel import RunPanel
from .worker import DocumentWorker


class MacroView(QWidget):
    def __init__(self, config, log_service):
        super().__init__()
        self._config = config
        self._log_service = log_service
        self._service = MacroService()
        self._current = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Macros")
        title.setObjectName("title")
        subtitle = QLabel(
            "Cree o importe macros desde scripts VBS grabados en SAP GUI y ejecútelas "
            "con listas de documentos."
        )
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        content = QHBoxLayout()
        content.setSpacing(12)

        left = QVBoxLayout()
        self.list = QListWidget()
        self.list.setFixedWidth(230)
        self.list.currentRowChanged.connect(self._on_select)
        left.addWidget(self.list, 1)

        btn_new = QPushButton("Nueva macro")
        btn_edit = QPushButton("Editar")
        btn_delete = QPushButton("Eliminar")
        btn_import = QPushButton("Importar VBS...")
        btn_new.clicked.connect(self._new_macro)
        btn_edit.clicked.connect(self._edit_macro)
        btn_delete.clicked.connect(self._delete_macro)
        btn_import.clicked.connect(self._import_macro)
        for button in (btn_new, btn_edit, btn_delete, btn_import):
            left.addWidget(button)
        content.addLayout(left)

        right = QVBoxLayout()
        self.name_label = QLabel("Seleccione una macro")
        self.name_label.setObjectName("title")
        self.desc_label = QLabel("")
        self.desc_label.setObjectName("subtitle")
        right.addWidget(self.name_label)
        right.addWidget(self.desc_label)

        self.steps_table = QTableWidget(0, 3)
        self.steps_table.setHorizontalHeaderLabels(["Acción", "Ruta (findById)", "Valor / Tecla"])
        self.steps_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.steps_table.verticalHeader().setVisible(False)
        self.steps_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        right.addWidget(self.steps_table, 3)

        self.panel = RunPanel(config, "documento", self._report_name)
        right.addWidget(self.panel, 4)
        self.panel.run_requested.connect(self._launch)

        content.addLayout(right, 1)
        layout.addLayout(content, 1)

        self._refresh()

    @property
    def _report_name(self):
        name = self._current.name if self._current else "macro"
        return name.replace(" ", "_")

    def _refresh(self):
        names = self._service.list_macros()
        self.list.clear()
        self.list.addItems(names)
        if names:
            self.list.setCurrentRow(0)
        else:
            self._current = None
            self._show_macro(None)

    def _on_select(self, row):
        if row < 0:
            return
        name = self.list.item(row).text()
        self._current = self._service.load(name)
        self._show_macro(self._current)

    def _show_macro(self, macro):
        self.steps_table.setRowCount(0)
        if macro is None:
            self.name_label.setText("Seleccione una macro")
            self.desc_label.setText("")
            return
        self.name_label.setText(macro.name)
        self.desc_label.setText(macro.description or "(sin descripción)")
        for index, step in enumerate(macro.steps, start=1):
            row = self.steps_table.rowCount()
            self.steps_table.insertRow(row)
            label = ACTION_LABELS.get(step.action, step.action)
            self.steps_table.setItem(row, 0, QTableWidgetItem(str(index)))
            self.steps_table.setItem(row, 1, QTableWidgetItem(label))
            self.steps_table.setItem(row, 2, QTableWidgetItem(step.path or step.value or ""))

    def _new_macro(self):
        dialog = MacroEditorDialog(self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            macro = dialog.result_macro()
            self._service.save(macro)
            self._refresh()
            self._select_name(macro.name)

    def _edit_macro(self):
        if self._current is None:
            return
        dialog = MacroEditorDialog(self, macro=self._current)
        if dialog.exec() == dialog.DialogCode.Accepted:
            macro = dialog.result_macro()
            if macro.name != self._current.name:
                self._service.delete(self._current.name)
            self._service.save(macro)
            self._refresh()
            self._select_name(macro.name)

    def _delete_macro(self):
        if self._current is None:
            return
        answer = QMessageBox.question(
            self,
            "Eliminar macro",
            f"¿Eliminar la macro '{self._current.name}'?",
        )
        if answer == QMessageBox.StandardButton.Yes:
            self._service.delete(self._current.name)
            self._current = None
            self._refresh()

    def _import_macro(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar script VBS", "", "Script VBS (*.vbs *.txt)"
        )
        if not path:
            return
        try:
            from ..macros.vbs_parser import parse_vbs

            steps = parse_vbs(read_vbs_text(path))
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudo leer el script:\n{exc}")
            return
        dialog = MacroEditorDialog(self)
        dialog.name_edit.setText(dialog.name_edit.text() or "Nueva macro")
        dialog.steps_table.setRowCount(0)

        for step in steps:
            dialog._add_row(step)
        if dialog.exec() == dialog.DialogCode.Accepted:
            macro = dialog.result_macro()
            self._service.save(macro)
            self._refresh()
            self._select_name(macro.name)

    def _select_name(self, name):
        for row in range(self.list.count()):
            if self.list.item(row).text() == name:
                self.list.setCurrentRow(row)
                return

    def _launch(self, ids, dry_run, batch_id="", resume=False):
        if self._current is None:
            return
        from ..macros.macro_processor import MacroModule

        module = MacroModule(self._current)
        self.panel.start_run(ids, batch_id)
        self._worker = DocumentWorker(
            module, ids, self._config, self._log_service, dry_run, batch_id, resume
        )
        self._worker.progress.connect(self.panel.on_progress)
        self._worker.document_done.connect(self.panel.on_document)
        self._worker.run_finished.connect(self.panel.on_finished)
        self._worker.start()

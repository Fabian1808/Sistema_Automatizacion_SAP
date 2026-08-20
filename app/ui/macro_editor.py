from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ..macros.macro_model import ACTION_LABELS, STEP_ACTIONS, VKEY_ACTIONS, Macro, MacroStep
from ..macros.vbs_parser import parse_vbs


def read_vbs_text(path):
    raw = Path(path).read_bytes()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")
    return raw.decode("utf-8", errors="replace")


class MacroEditorDialog(QDialog):
    def __init__(self, parent=None, macro=None):
        super().__init__(parent)
        self.setWindowTitle("Macro")
        self.resize(780, 520)
        self._macro = macro or Macro(name="")

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        self.name_edit = QLineEdit(self._macro.name)
        self.description_edit = QLineEdit(self._macro.description)
        self.folder_edit = QLineEdit(self._macro.output_doc_type)
        self.folder_edit.setPlaceholderText("Ej: HES, OC, FACTURAS...")
        form.addRow("Nombre:", self.name_edit)
        form.addRow("Descripción:", self.description_edit)
        form.addRow("Carpeta de salida:", self.folder_edit)
        layout.addLayout(form)

        steps_label = QLabel("Pasos de la macro:")
        steps_label.setObjectName("subtitle")
        layout.addWidget(steps_label)

        self.steps_table = QTableWidget(0, 3)
        self.steps_table.setHorizontalHeaderLabels(["Acción", "Ruta (findById)", "Valor / Tecla"])
        self.steps_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.steps_table.verticalHeader().setVisible(False)
        layout.addWidget(self.steps_table, 1)

        buttons_row = QHBoxLayout()
        btn_add = QPushButton("Agregar paso")
        btn_remove = QPushButton("Eliminar paso")
        btn_import = QPushButton("Importar desde VBS...")
        btn_add.clicked.connect(self._add_empty_row)
        btn_remove.clicked.connect(self._remove_row)
        btn_import.clicked.connect(self._import_vbs)
        buttons_row.addWidget(btn_add)
        buttons_row.addWidget(btn_remove)
        buttons_row.addWidget(btn_import)
        buttons_row.addStretch(1)
        layout.addLayout(buttons_row)

        note = QLabel(
            'Use "{ID}" en el valor de un paso "Escribir texto" para insertar '
            "el número de documento de cada lote."
        )
        note.setObjectName("subtitle")
        layout.addWidget(note)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        for step in self._macro.steps:
            self._add_row(step)

    def _add_empty_row(self):
        self._add_row(MacroStep(action="press"))

    def _add_row(self, step):
        row = self.steps_table.rowCount()
        self.steps_table.insertRow(row)
        combo = QComboBox()
        for action in STEP_ACTIONS:
            combo.addItem(ACTION_LABELS.get(action, action), action)
        if step.action in STEP_ACTIONS:
            combo.setCurrentIndex(STEP_ACTIONS.index(step.action))
        self.steps_table.setCellWidget(row, 0, combo)
        self.steps_table.setItem(row, 1, QTableWidgetItem(step.path))
        if step.action in VKEY_ACTIONS:
            value = str(step.key) if step.key else ""
        else:
            value = step.value
        self.steps_table.setItem(row, 2, QTableWidgetItem(value))

    def _remove_row(self):
        row = self.steps_table.currentRow()
        if row >= 0:
            self.steps_table.removeRow(row)

    def _import_vbs(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar script VBS", "", "Script VBS (*.vbs *.txt)"
        )
        if not path:
            return
        try:
            steps = parse_vbs(read_vbs_text(path))
        except Exception as exc:
            QMessageBox.critical(
                self, "Error", f"No se pudo leer el script:\n{exc}"
            )
            return
        self.steps_table.setRowCount(0)
        for step in steps:
            self._add_row(step)
        if not self.name_edit.text():
            self.name_edit.setText(Path(path).stem)

    def _collect_steps(self):
        steps = []
        for row in range(self.steps_table.rowCount()):
            combo = self.steps_table.cellWidget(row, 0)
            if combo is None:
                continue
            action = combo.currentData()
            path = self.steps_table.item(row, 1).text().strip()
            value = self.steps_table.item(row, 2).text().strip()
            key = 0
            if action in VKEY_ACTIONS:
                try:
                    key = int(value)
                except ValueError:
                    key = 0
                value = ""
            steps.append(MacroStep(action=action, path=path, value=value, key=key))
        return steps

    def _accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Macro", "El nombre de la macro es obligatorio.")
            return
        self._macro = Macro(
            name=name,
            description=self.description_edit.text().strip(),
            output_doc_type=self.folder_edit.text().strip(),
            steps=self._collect_steps(),
        )
        self.accept()

    def result_macro(self):
        return self._macro
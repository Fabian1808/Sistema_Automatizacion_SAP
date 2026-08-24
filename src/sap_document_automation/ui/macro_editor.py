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
    QSpinBox,
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
        self.resize(950, 560)
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

        # Columnas: Acción | Ruta principal | Valor/Tecla | Tabla/Columna | Valor a escribir | Combo path | Combo valor | Max filas
        self.steps_table = QTableWidget(0, 8)
        self.steps_table.setHorizontalHeaderLabels([
            "Acción", "Ruta (findById)", "Valor / Tecla",
            "Columna a verificar", "Valor a escribir", "Combo path", "Combo valor", "Máx. filas"
        ])
        self.steps_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
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
            "el número de documento de cada lote. Para 'Buscar fila vacía', use {row} en la ruta de la columna."
        )
        note.setObjectName("subtitle")
        note.setWordWrap(True)
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
        combo.currentIndexChanged.connect(lambda _, r=row: self._on_action_changed(r))
        self.steps_table.setCellWidget(row, 0, combo)

        self.steps_table.setItem(row, 1, QTableWidgetItem(step.path))

        if step.action in VKEY_ACTIONS:
            val = str(step.key) if step.key else ""
        else:
            val = step.value
        self.steps_table.setItem(row, 2, QTableWidgetItem(val))

        # Columnas específicas para find_empty_row
        self.steps_table.setItem(row, 3, QTableWidgetItem(step.column_path))
        self.steps_table.setItem(row, 4, QTableWidgetItem(step.write_value))
        self.steps_table.setItem(row, 5, QTableWidgetItem(step.combo_path))
        self.steps_table.setItem(row, 6, QTableWidgetItem(step.combo_value))

        max_rows_spin = QSpinBox()
        max_rows_spin.setRange(1, 100)
        max_rows_spin.setValue(step.max_rows if step.max_rows else 20)
        self.steps_table.setCellWidget(row, 7, max_rows_spin)

        self._update_row_visibility(row, step.action)

    def _on_action_changed(self, row):
        combo = self.steps_table.cellWidget(row, 0)
        if combo:
            action = combo.currentData()
            self._update_row_visibility(row, action)

    def _update_row_visibility(self, row, action):
        """Muestra/oculta columnas según la acción."""
        is_find_empty = action == "find_empty_row"
        for col in [3, 4, 5, 6, 7]:
            self.steps_table.setColumnHidden(col, not is_find_empty)

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

            # Campos adicionales para find_empty_row
            column_path = self.steps_table.item(row, 3).text().strip() if self.steps_table.item(row, 3) else ""
            write_value = self.steps_table.item(row, 4).text().strip() if self.steps_table.item(row, 4) else ""
            combo_path = self.steps_table.item(row, 5).text().strip() if self.steps_table.item(row, 5) else ""
            combo_value = self.steps_table.item(row, 6).text().strip() if self.steps_table.item(row, 6) else ""

            max_rows_widget = self.steps_table.cellWidget(row, 7)
            max_rows = max_rows_widget.value() if max_rows_widget else 20

            steps.append(MacroStep(
                action=action,
                path=path,
                value=value,
                key=key,
                column_path=column_path,
                write_value=write_value,
                combo_path=combo_path,
                combo_value=combo_value,
                max_rows=max_rows,
            ))
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

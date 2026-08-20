from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class SettingsView(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Configuración")
        title.setObjectName("title")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        self.output_edit = QLineEdit(str(config.output_folder))
        output_row = QHBoxLayout()
        output_row.addWidget(self.output_edit, 1)
        output_btn = QPushButton("Examinar...")
        output_btn.clicked.connect(self._pick_output)
        output_row.addWidget(output_btn)
        form.addRow("Carpeta de salida:", output_row)

        self.logs_edit = QLineEdit(str(config.logs_folder))
        logs_row = QHBoxLayout()
        logs_row.addWidget(self.logs_edit, 1)
        logs_btn = QPushButton("Examinar...")
        logs_btn.clicked.connect(self._pick_logs)
        logs_row.addWidget(logs_btn)
        form.addRow("Carpeta de logs:", logs_row)

        self.retries_spin = QSpinBox()
        self.retries_spin.setRange(0, 10)
        self.retries_spin.setValue(config.get("max_retries"))
        form.addRow("Reintentos máximos:", self.retries_spin)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setSuffix(" seg")
        self.timeout_spin.setValue(config.get("sap_timeout_seconds"))
        form.addRow("Tiempo máximo de espera SAP:", self.timeout_spin)

        self.overwrite_check = QCheckBox("Sobrescribir archivos existentes")
        self.overwrite_check.setChecked(config.get("overwrite_existing"))
        form.addRow("", self.overwrite_check)

        self.auto_session_check = QCheckBox(
            "Seleccionar automáticamente la primera sesión SAP"
        )
        self.auto_session_check.setChecked(config.get("auto_select_session"))
        form.addRow("", self.auto_session_check)

        self.confirm_check = QCheckBox("Confirmar antes de procesar")
        self.confirm_check.setChecked(config.get("confirm_before_process"))
        form.addRow("", self.confirm_check)

        layout.addLayout(form)

        note = QLabel("La aplicación nunca guarda credenciales SAP.")
        note.setObjectName("subtitle")
        layout.addWidget(note)

        save_btn = QPushButton("Guardar configuración")
        save_btn.setObjectName("primary")
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)
        layout.addStretch(1)

    def _pick_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Carpeta de salida")
        if folder:
            self.output_edit.setText(folder)

    def _pick_logs(self):
        folder = QFileDialog.getExistingDirectory(self, "Carpeta de logs")
        if folder:
            self.logs_edit.setText(folder)

    def _save(self):
        self.config.set("output_folder", self.output_edit.text().strip())
        self.config.set("logs_folder", self.logs_edit.text().strip())
        self.config.set("max_retries", self.retries_spin.value())
        self.config.set("sap_timeout_seconds", self.timeout_spin.value())
        self.config.set("overwrite_existing", self.overwrite_check.isChecked())
        self.config.set("auto_select_session", self.auto_session_check.isChecked())
        self.config.set("confirm_before_process", self.confirm_check.isChecked())
        self.config.save()
        QMessageBox.information(self, "Configuración", "Configuración guardada correctamente.")
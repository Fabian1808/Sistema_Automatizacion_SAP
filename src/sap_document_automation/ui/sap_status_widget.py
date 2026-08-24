from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from ..sap.sap_connection import SapConnection
from ..sap.sap_exceptions import SapError


class SapStatusWidget(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.label = QLabel("SAP: verificando...")
        self.button = QPushButton("Actualizar conexión")
        self.button.setFixedWidth(150)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(8)
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        self.button.clicked.connect(self.refresh)
        self.refresh()

    def refresh(self):
        self.label.setText("SAP: verificando...")
        try:
            conn = SapConnection(timeout=self.config.get("sap_timeout_seconds"))
            sessions = conn.list_sessions()
        except SapError as exc:
            self.label.setText(
                f"<b style='color:#dc2626'>SAP DESCONECTADO</b> &nbsp; {exc.user_message}"
            )
            return
        if not sessions:
            self.label.setText(
                "<b style='color:#dc2626'>SAP DESCONECTADO</b> &nbsp; No hay sesiones activas."
            )
            return
        first = sessions[0]
        extra = f" ({len(sessions)} sesiones)" if len(sessions) > 1 else ""
        desc = first["description"] or "sesión"
        user = first["user"] or ""
        self.label.setText(
            f"<b style='color:#16a34a'>SAP CONECTADO</b> &nbsp; {desc} &nbsp; {user}{extra}"
        )

import threading

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from ..sap.sap_connection import SapConnection
from ..sap.sap_exceptions import SapError


class SapStatusWidget(QWidget):
    _result = Signal(str, str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self._checking = False
        self.label = QLabel("SAP: verificando...")
        self.button = QPushButton("Actualizar conexión")
        self.button.setFixedWidth(150)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(8)
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        self.button.clicked.connect(self.refresh)
        self._result.connect(self._on_result)
        self.refresh()

    def refresh(self):
        if self._checking:
            return
        self._checking = True
        self.label.setText("SAP: verificando...")
        self.button.setEnabled(False)
        timeout = int(self.config.get("sap_timeout_seconds") or 30)
        thread = threading.Thread(target=self._check, args=(timeout,), daemon=True)
        thread.start()

    def _check(self, timeout: int):
        try:
            sessions = SapConnection(timeout=timeout).list_sessions()
        except SapError as exc:
            self._result.emit("error", exc.user_message)
            return
        except Exception as exc:
            self._result.emit("error", str(exc))
            return
        if not sessions:
            self._result.emit("error", "No hay sesiones activas.")
            return
        first = sessions[0]
        extra = f" ({len(sessions)} sesiones)" if len(sessions) > 1 else ""
        desc = first["description"] or "sesión"
        user = first["user"] or ""
        self._result.emit("ok", f"{desc} &nbsp; {user}{extra}")

    def _on_result(self, kind: str, detail: str):
        self._checking = False
        self.button.setEnabled(True)
        if kind == "ok":
            self.label.setText(
                f"<b style='color:#16a34a'>SAP CONECTADO</b> &nbsp; {detail}"
            )
        else:
            self.label.setText(
                f"<b style='color:#dc2626'>SAP DESCONECTADO</b> &nbsp; {detail}"
            )

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

TEXTO = """Cómo usar la aplicación

1. Abra SAP GUI e inicie sesión con su usuario.
2. Verifique que SAP GUI Scripting esté habilitado:
   Alt+F12 > Opciones > Accessibility & Scripting > Scripting.
3. Abra esta aplicación (SAP Document Automation).
4. En la barra inferior derecha revise el estado de conexión SAP.
5. En la pestaña HES pegue los números o importe un Excel/CSV.
6. Presione PROCESAR HES (disponible en la Fase 2).

Nota: la aplicación no almacena ni solicita credenciales SAP.
Utiliza la sesión de SAP GUI que usted ya tenga abierta."""


class HelpView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        title = QLabel("Ayuda")
        title.setObjectName("title")
        text = QLabel(TEXTO)
        text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(title)
        layout.addWidget(text)
        layout.addStretch(1)
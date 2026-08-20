from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class HistoryView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        title = QLabel("Historial de procesos")
        title.setObjectName("title")
        placeholder = QLabel("El historial estará disponible a partir de la Fase 5.")
        placeholder.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(placeholder)
        layout.addStretch(1)
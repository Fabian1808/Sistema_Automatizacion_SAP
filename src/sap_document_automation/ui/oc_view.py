from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class OcView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        title = QLabel("Órdenes de Compra")
        title.setObjectName("title")
        placeholder = QLabel("El módulo de Órdenes de Compra estará disponible en la Fase 8.")
        placeholder.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(placeholder)
        layout.addStretch(1)

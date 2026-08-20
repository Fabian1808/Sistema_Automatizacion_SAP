from dataclasses import dataclass, field

STEP_ACTIONS = [
    "transaction",
    "press",
    "set_text",
    "set_combo",
    "set_checked",
    "focus",
    "send_vkey",
    "send_vkey_active",
    "set_tree_node",
    "maximize",
    "wait_idle",
    "sleep",
    "wait_popup_close",
    "close_popup",
    "check_error",
    "save_pdf",
]

ACTION_LABELS = {
    "transaction": "Transacción",
    "press": "Presionar botón",
    "set_text": "Escribir texto",
    "set_combo": "Seleccionar combo",
    "set_checked": "Marcar casilla",
    "focus": "Enfocar campo",
    "send_vkey": "Enviar tecla (ventana)",
    "send_vkey_active": "Enviar tecla (ventana activa)",
    "set_tree_node": "Posicionar árbol",
    "maximize": "Maximizar ventana",
    "wait_idle": "Esperar a que SAP termine",
    "sleep": "Esperar (segundos)",
    "wait_popup_close": "Esperar cierre de popup",
    "close_popup": "Cerrar popup",
    "check_error": "Verificar mensaje de error",
    "save_pdf": "Guardar PDF (diálogo nativo)",
}

VKEY_ACTIONS = ("send_vkey", "send_vkey_active")


@dataclass
class MacroStep:
    action: str
    path: str = ""
    value: str = ""
    key: int = 0

    def to_dict(self):
        return {
            "action": self.action,
            "path": self.path,
            "value": self.value,
            "key": self.key,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            action=data.get("action", ""),
            path=data.get("path", ""),
            value=data.get("value", ""),
            key=int(data.get("key", 0)),
        )


@dataclass
class Macro:
    name: str
    description: str = ""
    output_doc_type: str = ""
    steps: list = field(default_factory=list)

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "output_doc_type": self.output_doc_type,
            "steps": [step.to_dict() for step in self.steps],
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            output_doc_type=data.get("output_doc_type", ""),
            steps=[MacroStep.from_dict(item) for item in data.get("steps", [])],
        )
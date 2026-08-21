from __future__ import annotations
from typing import Any, Optional
from ..core.interfaces import SapElement


class ComSapElementWrapper(SapElement):
    """Wrapper que implementa la interfaz SapElement para elementos COM."""

    def __init__(self, path: str, com_element: Any):
        self.path = path
        self._com = com_element

    def set_text(self, value: str) -> None:
        try:
            self._com.text = value
        except Exception:
            self._com.value = value

    def get_text(self) -> str:
        try:
            return self._com.Text
        except Exception:
            return ""

    def press(self) -> None:
        self._com.press()

    def set_focus(self) -> None:
        self._com.SetFocus()

    def set_combo_key(self, key: str) -> None:
        self._com.key = key

    def set_checked(self, checked: bool) -> None:
        try:
            self._com.Selected = checked
        except Exception:
            self._com.selected = checked

    def send_vkey(self, key: int) -> None:
        self._com.sendVKey(key)

    def set_top_node(self, node: str) -> None:
        self._com.topNode = node

    def get_attribute(self, name: str) -> Any:
        return getattr(self._com, name, None)

    def exists(self) -> bool:
        try:
            _ = self._com.Text
            return True
        except Exception:
            return False

    def get_com_object(self):
        """Acceso al objeto COM subyacente para operaciones avanzadas."""
        return self._com
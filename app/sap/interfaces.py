from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path


@dataclass
class SapElement:
    """Wrapper unificado para elementos SAP (COM u otro backend)."""
    path: str
    _com_element: Any = None

    def set_text(self, value: str) -> None: ...
    def get_text(self) -> str: ...
    def press(self) -> None: ...
    def set_focus(self) -> None: ...
    def set_combo_key(self, key: str) -> None: ...
    def set_checked(self, checked: bool) -> None: ...
    def send_vkey(self, key: int) -> None: ...
    def set_top_node(self, node: str) -> None: ...
    def get_attribute(self, name: str) -> Any: ...
    def exists(self) -> bool: ...


@dataclass
class SapWindowState:
    busy: bool = False
    status_bar_text: str = ""
    active_window_exists: bool = False


class ISapClient(ABC):
    """Interfaz unificada para automatización SAP. Permite swap entre SAP GUI Scripting, API REST, mocks."""

    @abstractmethod
    def connect(self, connection_id: int = 0, session_id: int = 0) -> bool:
        """Conecta a una sesión SAP existente."""
        ...

    @abstractmethod
    def disconnect(self) -> None: ...

    @abstractmethod
    def is_connected(self) -> bool: ...

    @abstractmethod
    def get_sessions(self) -> List[Dict[str, Any]]:
        """Lista sesiones disponibles con metadatos."""
        ...

    @abstractmethod
    def find_element(self, path: str, timeout: float = 10.0) -> SapElement:
        """Encuentra elemento por path SAP (wnd[0]/usr/...). Lanza excepción si no existe."""
        ...

    @abstractmethod
    def find_optional(self, path: str) -> Optional[SapElement]:
        """Busca elemento sin lanzar excepción."""
        ...

    @abstractmethod
    def wait_for(self, condition: Callable[[], bool], timeout: float = 10.0, interval: float = 0.5) -> bool:
        """Espera hasta que condition() retorne True."""
        ...

    @abstractmethod
    def wait_until_idle(self, timeout: float = 30.0) -> bool:
        """Espera hasta que SAP no esté busy."""
        ...

    @abstractmethod
    def get_status_bar_text(self) -> str: ...

    @abstractmethod
    def send_vkey(self, key: int, window: str = "wnd[0]") -> None: ...

    @abstractmethod
    def active_window_send_vkey(self, key: int) -> None: ...

    @abstractmethod
    def start_transaction(self, tcode: str) -> None: ...

    @abstractmethod
    def close_popup(self, popup_path: str = "wnd[1]") -> None: ...

    @abstractmethod
    def get_window_state(self) -> SapWindowState: ...

    @abstractmethod
    def take_screenshot(self, path: Path) -> bool: ...

    @abstractmethod
    def execute_script(self, script: str, params: Dict = None) -> Any:
        """Ejecuta script personalizado (VBS, JS, etc.) si el backend lo soporta."""
        ...


class SapElementNotFoundError(Exception):
    def __init__(self, path: str, timeout: float):
        self.path = path
        self.timeout = timeout
        super().__init__(f"Elemento SAP no encontrado: {path} (timeout: {timeout}s)")


class SapSessionLostError(Exception):
    pass


class SapScriptingDisabledError(Exception):
    pass


class SapNotRunningError(Exception):
    pass

# Re-exports para compatibilidad con m�dulos que importan excepciones desde aqu�
from .sap_exceptions import (  # noqa: E402,F401
    SapError,
    SapNotRunningError,
    SapScriptingDisabledError,
    SapNoSessionError,
    SapSessionLostError,
    SapElementNotFoundError,
    SapPopupError,
)

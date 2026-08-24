from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable, Dict, List

from ..core.exceptions import SapError
from ..core.interfaces import (
    SapElementNotFoundError,
    SapWindowState,
)


class ComSapElement:
    """Wrapper para elemento COM de SAP GUI Scripting."""

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


class ComSapClient:
    """Implementación SAP GUI Scripting vía COM (pywin32)."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self._engine = None
        self._session = None
        self._connection_id = 0
        self._session_id = 0

    def _get_engine(self):
        if self._engine is not None:
            return self._engine
        try:
            import win32com.client
        except ImportError as exc:
            raise SapError("pywin32 no disponible. Reinstale la aplicación.") from exc
        try:
            sapgui = win32com.client.GetObject("SAPGUI")
            engine = sapgui.GetScriptingEngine
        except Exception as exc:
            if "SCRIPTING" in str(exc).upper():
                from ..core.exceptions import SapScriptingDisabledError
                raise SapScriptingDisabledError(str(exc)) from exc
            from ..core.exceptions import SapNotRunningError
            raise SapNotRunningError(str(exc)) from exc
        self._engine = engine
        return engine

    def connect(self, connection_id: int = 0, session_id: int = 0) -> bool:
        engine = self._get_engine()
        try:
            conns = engine.Children
            if conns.Count == 0:
                from ..core.exceptions import SapNotRunningError
                raise SapNotRunningError("No hay conexiones SAP abiertas.")
            conn = conns.Item(connection_id)
            sessions = conn.Children
            if sessions.Count == 0:
                from ..core.exceptions import SapNotRunningError
                raise SapNotRunningError("No hay sesiones activas en la conexión.")
            self._session = sessions.Item(session_id)
            self._connection_id = connection_id
            self._session_id = session_id
            return True
        except Exception as exc:
            if "SCRIPTING" in str(exc).upper():
                from ..core.exceptions import SapScriptingDisabledError
                raise SapScriptingDisabledError(str(exc)) from exc
            from ..core.exceptions import SapSessionLostError
            raise SapSessionLostError(str(exc)) from exc

    def disconnect(self) -> None:
        self._session = None
        self._engine = None

    def is_connected(self) -> bool:
        try:
            if self._session is None:
                return False
            _ = self._session.Busy
            return True
        except Exception:
            return False

    def get_sessions(self) -> List[Dict[str, Any]]:
        engine = self._get_engine()
        conns = engine.Children
        result = []
        for c_idx in range(conns.Count):
            conn = conns.Item(c_idx)
            sessions = conn.Children
            for s_idx in range(sessions.Count):
                sess = sessions.Item(s_idx)
                try:
                    info = sess.Info
                    result.append({
                        "connection_id": c_idx,
                        "session_id": s_idx,
                        "description": getattr(info, "Description", ""),
                        "user": getattr(info, "User", ""),
                        "client": getattr(info, "Client", ""),
                        "transaction": getattr(info, "Transaction", ""),
                    })
                except Exception:
                    pass
        return result

    def _wrap_element(self, path: str, com_element: Any):
        from .element import ComSapElementWrapper
        return ComSapElementWrapper(path, com_element)

    def find_element(self, path: str, timeout: float = 10.0):
        limit = time.monotonic() + timeout
        while time.monotonic() < limit:
            try:
                com_el = self._session.findById(path)
                return ComSapElementWrapper(path, com_el)
            except Exception:
                time.sleep(0.5)
        raise SapElementNotFoundError(path, timeout)

    def find_optional(self, path: str):
        try:
            com_el = self._session.findById(path)
            return ComSapElementWrapper(path, com_el)
        except Exception:
            return None

    def wait_for(self, condition: Callable[[], bool], timeout: float = 10.0, interval: float = 0.5) -> bool:
        limit = time.monotonic() + timeout
        while time.monotonic() < limit:
            if condition():
                return True
            time.sleep(interval)
        return False

    def wait_until_idle(self, timeout: float = 30.0) -> bool:
        return self.wait_for(lambda: not self._is_busy(), timeout=timeout)

    def _is_busy(self) -> bool:
        try:
            return bool(self._session.Busy)
        except Exception as exc:
            from ..core.exceptions import SapSessionLostError
            raise SapSessionLostError(str(exc)) from exc

    def get_status_bar_text(self) -> str:
        el = self.find_optional("wnd[0]/sbar")
        if el is None:
            return ""
        try:
            return el.get_text()
        except Exception:
            return ""

    def send_vkey(self, key: int, window: str = "wnd[0]") -> None:
        self.find_element(window).send_vkey(key)

    def active_window_send_vkey(self, key: int) -> None:
        try:
            self._session.ActiveWindow.sendVKey(key)
        except Exception as exc:
            from ..core.exceptions import SapSessionLostError
            raise SapSessionLostError(str(exc)) from exc

    def start_transaction(self, tcode: str) -> None:
        try:
            self._session.StartTransaction(tcode)
        except Exception as exc:
            from ..core.exceptions import SapSessionLostError
            raise SapSessionLostError(str(exc)) from exc

    def close_popup(self, popup_path: str = "wnd[1]") -> None:
        if self.find_optional(popup_path) is None:
            return
        for button in ("tbar[0]/btn[0]", "usr/btnSPOP-OPTION1", "tbar[0]/btn[1]"):
            el = self.find_optional(f"{popup_path}/{button}")
            if el is not None:
                el.press()
                self.wait_until_idle()
                return
        self.send_vkey(0, window=popup_path)

    def get_window_state(self):
        try:
            busy = self._is_busy()
        except Exception:
            busy = True
        return SapWindowState(
            busy=busy,
            status_bar_text=self.get_status_bar_text(),
            active_window_exists=self.find_optional("wnd[1]") is not None,
        )

    def take_screenshot(self, path: Path) -> bool:
        try:
            self._session.ActiveWindow.HardCopy(str(path), "BMP")
            return True
        except Exception:
            return False

    def execute_script(self, script: str, params: Dict = None):
        raise NotImplementedError("execute_script no disponible en COM client")


class ComSapElementWrapper:
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


class SapClientFactory:
    """Factory para crear clientes SAP según configuración."""

    @staticmethod
    def create(backend: str = "com", **kwargs):
        if backend == "com":
            from .client import ComSapClient
            return ComSapClient(**kwargs)
        elif backend == "mock":
            from .mock_client import MockSapClient
            return MockSapClient(**kwargs)
        else:
            raise ValueError(f"Backend SAP no soportado: {backend}")

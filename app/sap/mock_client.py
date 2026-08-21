import time
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path
from dataclasses import dataclass, field

from .interfaces import (
    ISapClient, SapElement, SapElementNotFoundError, SapSessionLostError,
    SapScriptingDisabledError, SapNotRunningError, SapWindowState
)


@dataclass
class MockSapElement(SapElement):
    path: str
    _attrs: Dict[str, Any] = field(default_factory=dict)
    _children: Dict[str, 'MockSapElement'] = field(default_factory=dict)

    def __post_init__(self):
        self._attrs.setdefault("Text", "")
        self._attrs.setdefault("Selected", False)

    def set_text(self, value: str) -> None:
        self._attrs["Text"] = value

    def get_text(self) -> str:
        return self._attrs.get("Text", "")

    def press(self) -> None:
        self._attrs["_pressed"] = True

    def set_focus(self) -> None:
        self._attrs["_focused"] = True

    def set_combo_key(self, key: str) -> None:
        self._attrs["Key"] = key

    def set_checked(self, checked: bool) -> None:
        self._attrs["Selected"] = checked

    def send_vkey(self, key: int) -> None:
        self._attrs["_vkey"] = key

    def set_top_node(self, node: str) -> None:
        self._attrs["TopNode"] = node

    def get_attribute(self, name: str) -> Any:
        return self._attrs.get(name)

    def exists(self) -> bool:
        return True


class MockSapClient(ISapClient):
    """Cliente SAP mock para testing sin SAP real."""

    def __init__(self, timeout: float = 5.0, fail_on: Optional[List[str]] = None):
        self.timeout = timeout
        self._connected = False
        self._busy = False
        self._status_bar = ""
        self._elements: Dict[str, Any] = {}
        self._fail_on = set(fail_on or [])
        self._transactions: List[str] = []
        self._vkeys: List[int] = []

    def connect(self, connection_id: int = 0, session_id: int = 0) -> bool:
        if "connect" in self._fail_on:
            raise ConnectionError("Simulated connection failure")
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def get_sessions(self) -> List[Dict[str, Any]]:
        return [{
            "connection_id": 0,
            "session_id": 0,
            "description": "MOCK - Desarrollo",
            "user": "TEST_USER",
            "client": "100",
            "transaction": "ML81N",
        }]

    def find_element(self, path: str, timeout: float = 10.0) -> 'MockSapElement':
        if path in self._fail_on:
            raise SapElementNotFoundError(path, timeout)
        if path not in self._elements:
            self._elements[path] = MockSapElement(path=path)
        return self._elements[path]

    def find_optional(self, path: str) -> Optional['MockSapElement']:
        if path in self._fail_on:
            return None
        if path not in self._elements:
            self._elements[path] = MockSapElement(path=path)
        return self._elements[path]

    def wait_for(self, condition: Callable[[], bool], timeout: float = 10.0, interval: float = 0.1) -> bool:
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            if condition():
                return True
            time.sleep(interval)
        return False

    def wait_until_idle(self, timeout: float = 30.0) -> bool:
        self._busy = False
        return True

    def get_status_bar_text(self) -> str:
        return self._status_bar

    def set_status_bar(self, text: str) -> None:
        self._status_bar = text

    def send_vkey(self, key: int, window: str = "wnd[0]") -> None:
        self._vkeys.append(key)

    def active_window_send_vkey(self, key: int) -> None:
        self._vkeys.append(key)

    def start_transaction(self, tcode: str) -> None:
        self._transactions.append(tcode)

    def close_popup(self, popup_path: str = "wnd[1]") -> None:
        pass

    def get_window_state(self) -> 'SapWindowState':
        from .interfaces import SapWindowState
        return SapWindowState(busy=self._busy, status_bar_text=self._status_bar)

    def take_screenshot(self, path: Path) -> bool:
        return True

    def execute_script(self, script: str, params: Dict = None) -> Any:
        return {"executed": True, "script": script[:50]}

    def set_busy(self, busy: bool):
        self._busy = busy

    def set_status_bar_text(self, text: str):
        self._status_bar = text

    def get_last_transaction(self) -> Optional[str]:
        return self._transactions[-1] if self._transactions else None

    def get_sent_vkeys(self) -> List[int]:
        return self._vkeys.copy()
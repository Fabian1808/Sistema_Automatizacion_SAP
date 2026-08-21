from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol
from enum import Enum


class DocumentState(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRY = "RETRY"
    SKIPPED_DUPLICATE = "SKIPPED_DUPLICATE"


@dataclass
class ProcessResult:
    document_id: str
    ok: bool
    error: str = ""
    file_path: str = ""
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class DocumentModule(Protocol):
    """Protocolo para módulos de documentos (HES, OC, Macros, etc.)"""
    module_id: str
    module_name: str

    def validate_ids(self, lines: List[str]) -> Dict[str, List[str]]:
        ...

    def process_one(self, client: 'ISapClient', document_id: str, context: Dict[str, Any]):
        ...


class ISapClient(Protocol):
    """Protocolo para cliente SAP (permite duck typing)"""
    def find_element(self, path: str, timeout: float = 10.0) -> Any: ...
    def find_optional(self, path: str) -> Any: ...
    def wait_for(self, condition, timeout: float = 10.0, interval: float = 0.5) -> bool: ...
    def wait_until_idle(self, timeout: float = 30.0) -> bool: ...
    def get_status_bar_text(self) -> str: ...
    def send_vkey(self, key: int, window: str = "wnd[0]") -> None: ...
    def active_window_send_vkey(self, key: int) -> None: ...
    def start_transaction(self, tcode: str) -> None: ...
    def close_popup(self, popup_path: str = "wnd[1]") -> None: ...
    def get_window_state(self) -> Any: ...
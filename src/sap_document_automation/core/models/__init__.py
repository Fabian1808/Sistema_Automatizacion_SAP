from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pathlib import Path


class DocumentState(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRY = "RETRY"
    SKIPPED_DUPLICATE = "SKIPPED_DUPLICATE"


@dataclass
class DocumentRecord:
    document_id: str
    batch_id: str
    module_id: str
    state: DocumentState = DocumentState.PENDING
    file_path: str = ""
    file_hash: str = ""
    error: str = ""
    attempts: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "batch_id": self.batch_id,
            "module_id": self.module_id,
            "state": self.state.value,
            "file_path": self.file_path,
            "file_hash": self.file_hash,
            "error": self.error,
            "attempts": self.attempts,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "duration": self.duration,
            "metadata": self.metadata,
        }


@dataclass
class BatchInfo:
    batch_id: str
    module_id: str
    total_documents: int
    created_at: str
    updated_at: str
    config_snapshot: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "module_id": self.module_id,
            "total_documents": self.total_documents,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "config_snapshot": self.config_snapshot,
        }


@dataclass
class ProcessResult:
    document_id: str
    ok: bool
    error: str = ""
    file_path: str = ""
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "ok": self.ok,
            "error": self.error,
            "file_path": self.file_path,
            "duration": self.duration,
            "metadata": self.metadata,
        }


@dataclass
class BatchSummary:
    batch_id: str
    counts: Dict[str, int] = field(default_factory=dict)
    total: int = 0
    results: List[ProcessResult] = field(default_factory=list)
    duration_seconds: float = 0.0
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    finished_at: str = ""

    @property
    def success_count(self) -> int:
        return self.counts.get("SUCCESS", sum(1 for r in self.results if r.ok))

    @property
    def error_count(self) -> int:
        return self.counts.get("FAILED", sum(1 for r in self.results if not r.ok))

    @property
    def duplicate_count(self) -> int:
        return self.counts.get("SKIPPED_DUPLICATE", 0)

    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.success_count / self.total
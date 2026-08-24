import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


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
    state: DocumentState
    file_path: str = ""
    file_hash: str = ""
    error: str = ""
    attempts: int = 0
    created_at: str = ""
    updated_at: str = ""
    duration: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "DocumentRecord":
        return cls(
            document_id=row["document_id"],
            batch_id=row["batch_id"],
            module_id=row["module_id"],
            state=DocumentState(row["state"]),
            file_path=row["file_path"] or "",
            file_hash=row["file_hash"] or "",
            error=row["error"] or "",
            attempts=row["attempts"],
            created_at=row["created_at"] or "",
            updated_at=row["updated_at"] or "",
            duration=row["duration"],
        )


class StateService:
    DB_NAME = "batches.db"

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path.home() / "AppData" / "Roaming" / "SAPDocumentAutomation"
        self.db_path = Path(base_dir) / self.DB_NAME
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS batches (
                    batch_id TEXT PRIMARY KEY,
                    module_id TEXT NOT NULL,
                    total_documents INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    config_snapshot TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT NOT NULL,
                    batch_id TEXT NOT NULL,
                    module_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    file_path TEXT DEFAULT '',
                    file_hash TEXT DEFAULT '',
                    error TEXT DEFAULT '',
                    attempts INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    duration REAL DEFAULT 0.0,
                    PRIMARY KEY (document_id, batch_id),
                    FOREIGN KEY (batch_id) REFERENCES batches(batch_id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_batch_state
                ON documents(batch_id, state)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_hash
                ON documents(file_hash)
            """)

    def _now(self) -> str:
        return datetime.now().isoformat()

    def _file_hash(self, path: Path) -> str:
        if not path.exists():
            return ""
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def create_batch(
        self,
        batch_id: str,
        module_id: str,
        document_ids: List[str],
        config_snapshot: Optional[Dict] = None,
    ) -> None:
        now = self._now()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO batches
                (batch_id, module_id, total_documents, created_at, updated_at, config_snapshot)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (batch_id, module_id, len(document_ids), now, now, json.dumps(config_snapshot or {})),
            )
            for doc_id in document_ids:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO documents
                    (document_id, batch_id, module_id, state, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (doc_id, batch_id, module_id, DocumentState.PENDING.value, now, now),
                )

    def get_batch(self, batch_id: str) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM batches WHERE batch_id = ?", (batch_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_documents(self, batch_id: str, states: Optional[List[DocumentState]] = None) -> List[DocumentRecord]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if states:
                placeholders = ",".join("?" * len(states))
                query = f"SELECT * FROM documents WHERE batch_id = ? AND state IN ({placeholders})"
                params = [batch_id] + [s.value for s in states]
            else:
                query = "SELECT * FROM documents WHERE batch_id = ?"
                params = [batch_id]
            rows = conn.execute(query, params).fetchall()
            return [DocumentRecord.from_row(r) for r in rows]

    def get_pending(self, batch_id: str) -> List[DocumentRecord]:
        return self.get_documents(batch_id, [DocumentState.PENDING, DocumentState.RETRY])

    def get_completed(self, batch_id: str) -> List[DocumentRecord]:
        return self.get_documents(batch_id, [DocumentState.SUCCESS])

    def get_failed(self, batch_id: str) -> List[DocumentRecord]:
        return self.get_documents(batch_id, [DocumentState.FAILED])

    def mark_processing(self, batch_id: str, document_id: str) -> None:
        self._update_doc(batch_id, document_id, {"state": DocumentState.PROCESSING.value, "attempts": "attempts + 1"})

    def mark_success(self, batch_id: str, document_id: str, file_path: str, duration: float) -> None:
        file_hash = self._file_hash(Path(file_path)) if file_path else ""
        self._update_doc(batch_id, document_id, {
            "state": DocumentState.SUCCESS.value,
            "file_path": file_path,
            "file_hash": file_hash,
            "duration": duration,
        })

    def mark_failed(self, batch_id: str, document_id: str, error: str) -> None:
        self._update_doc(batch_id, document_id, {"state": DocumentState.FAILED.value, "error": error})

    def mark_skipped_duplicate(self, batch_id: str, document_id: str, existing_path: str) -> None:
        self._update_doc(batch_id, document_id, {
            "state": DocumentState.SKIPPED_DUPLICATE.value,
            "file_path": existing_path,
            "file_hash": self._file_hash(Path(existing_path)),
        })

    def increment_attempt(self, batch_id: str, document_id: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE documents SET attempts = attempts + 1 WHERE batch_id = ? AND document_id = ?",
                (batch_id, document_id),
            )
            conn.commit()
            row = conn.execute(
                "SELECT attempts FROM documents WHERE batch_id = ? AND document_id = ?",
                (batch_id, document_id),
            ).fetchone()
            return row[0] if row else 0

    def find_duplicate_by_hash(self, file_hash: str) -> Optional[DocumentRecord]:
        if not file_hash:
            return None
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM documents WHERE file_hash = ? AND state = ? LIMIT 1",
                (file_hash, DocumentState.SUCCESS.value),
            ).fetchone()
            return DocumentRecord.from_row(row) if row else None

    def get_batch_summary(self, batch_id: str) -> Dict[str, int]:
        with sqlite3.connect(self.db_path) as conn:
            counts = {}
            for state in DocumentState:
                row = conn.execute(
                    "SELECT COUNT(*) FROM documents WHERE batch_id = ? AND state = ?",
                    (batch_id, state.value),
                ).fetchone()
                counts[state.value] = row[0] if row else 0
            return counts

    def list_batches(self, limit: int = 50) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM batches ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def _update_doc(self, batch_id: str, document_id: str, fields: Dict[str, Any]) -> None:
        now = self._now()
        set_clauses = []
        params = []
        for k, v in fields.items():
            if k == "attempts" and isinstance(v, str) and v.startswith("attempts"):
                set_clauses.append(f"{k} = {k} + 1")
            else:
                set_clauses.append(f"{k} = ?")
                params.append(v)
        set_clauses.append("updated_at = ?")
        params.append(now)
        params.extend([batch_id, document_id])
        query = f"UPDATE documents SET {', '.join(set_clauses)} WHERE batch_id = ? AND document_id = ?"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(query, params)

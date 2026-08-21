import time
import uuid
from typing import Optional

from PySide6.QtCore import QThread, Signal

from ..modules.base import ProcessResult
from ..sap.sap_connection import SapConnection
from ..services.file_service import FileService
from ..services.state_service import StateService, DocumentState


class DocumentWorker(QThread):
    progress = Signal(int, int, str)
    document_done = Signal(object)
    run_finished = Signal(list)
    batch_created = Signal(str)

    def __init__(
        self,
        module,
        document_ids,
        config,
        log_service,
        dry_run,
        batch_id: Optional[str] = None,
        resume: bool = False,
    ):
        super().__init__()
        self._module = module
        self._ids = document_ids
        self._config = config
        self._log_service = log_service
        self._dry_run = dry_run
        self._resume = resume
        self._batch_id = batch_id or f"{module.module_id}_{uuid.uuid4().hex[:8]}"
        self._state_service = StateService()

    def run(self):
        file_service = FileService(
            self._config.output_folder,
            overwrite=self._config.get("overwrite_existing"),
        )

        if not self._resume:
            self._state_service.create_batch(
                self._batch_id,
                self._module.module_id,
                self._ids,
                config_snapshot={
                    "dry_run": self._dry_run,
                    "overwrite_existing": self._config.get("overwrite_existing"),
                },
            )
        self.batch_created.emit(self._batch_id)

        results = []
        total = len(self._ids)

        for index, doc_id in enumerate(self._ids, start=1):
            self.progress.emit(index - 1, total, doc_id)

            if self._resume:
                existing = self._state_service.get_documents(self._batch_id)
                doc_record = next((d for d in existing if d.document_id == doc_id), None)
                if doc_record and doc_record.state in (
                    DocumentState.SUCCESS,
                    DocumentState.SKIPPED_DUPLICATE,
                ):
                    # Ya procesado exitosamente - saltar
                    result = self._skip_result(doc_record)
                    self.document_done.emit(result)
                    self.progress.emit(index, total, doc_id)
                    results.append(result)
                    continue
                elif doc_record and doc_record.state == DocumentState.FAILED:
                    # Reintentar fallidos
                    pass  # continúa procesando

            self._state_service.mark_processing(self._batch_id, doc_id)
            start = time.monotonic()

            try:
                session = SapConnection(
                    timeout=self._config.get("sap_timeout_seconds")
                ).get_session()
                result = self._module.process_one(
                    session,
                    doc_id,
                    {
                        "dry_run": self._dry_run,
                        "log_service": self._log_service,
                        "file_service": file_service,
                        "max_retries": self._config.get("max_retries"),
                        "batch_id": self._batch_id,
                        "state_service": self._state_service,
                    },
                )
            except Exception as exc:
                result = ProcessResult(document_id=doc_id, ok=False, error=str(exc))

            result.duration = time.monotonic() - start

            if result.ok and not self._dry_run:
                # Verificar duplicado por hash
                dup = self._state_service.find_duplicate_by_hash(
                    self._file_hash(result.file_path) if result.file_path else ""
                )
                if dup and dup.document_id != doc_id:
                    self._state_service.mark_skipped_duplicate(
                        self._batch_id, doc_id, dup.file_path
                    )
                    result = ProcessResult(
                        document_id=doc_id,
                        ok=True,
                        error="",
                        file_path=dup.file_path,
                        duration=result.duration,
                    )

            if result.ok:
                self._state_service.mark_success(
                    self._batch_id, doc_id, result.file_path, result.duration
                )
            else:
                self._state_service.mark_failed(self._batch_id, doc_id, result.error)

            action = "Prueba" if self._dry_run else "PDF"
            self._log_service.write(
                f"{self._module.module_id.upper()} {doc_id}",
                action,
                "OK" if result.ok else "ERROR",
                result.error if not result.ok else None,
            )
            self.document_done.emit(result)
            self.progress.emit(index, total, doc_id)
            results.append(result)

        self.run_finished.emit(results)

    def _file_hash(self, path: str) -> str:
        if not path:
            return ""
        import hashlib
        h = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
        except OSError:
            return ""
        return h.hexdigest()

    def _skip_result(self, doc_record) -> ProcessResult:
        return ProcessResult(
            document_id=doc_record.document_id,
            ok=True,
            error="",
            file_path=doc_record.file_path,
            duration=0.0,
        )
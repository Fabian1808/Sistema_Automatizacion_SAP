import time
import uuid
import getpass
from typing import Optional

from PySide6.QtCore import QThread, Signal

from ..modules.base import ProcessResult
from ..sap.sap_connection import SapConnection
from ..services.file_service import FileService
from ..services.state_service import DocumentState, StateService


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
        self._cancel_requested = False
        self._cancelled = False
        self._connection: Optional[SapConnection] = None
        self._session = None

    # --- control de ejecución -------------------------------------------------
    def request_cancel(self) -> None:
        """Solicita detener el lote tras el documento en curso."""
        self._cancel_requested = True

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    def _get_session(self):
        if self._session is None:
            if self._connection is None:
                self._connection = SapConnection(
                    timeout=self._config.get("sap_timeout_seconds")
                )
            self._session = self._connection.get_session()
        return self._session

    def _drop_session(self) -> None:
        self._session = None

    def run(self):
        file_service = FileService(
            self._config.output_folder,
            overwrite=self._config.get("overwrite_existing"),
        )

        if not self._resume:
            try:
                username = getpass.getuser()
            except Exception:
                username = ""
            self._state_service.create_batch(
                self._batch_id,
                self._module.module_id,
                self._ids,
                config_snapshot={
                    "dry_run": self._dry_run,
                    "overwrite_existing": self._config.get("overwrite_existing"),
                },
                username=username,
            )
        else:
            self._state_service.set_batch_status(self._batch_id, "RUNNING")
        self.batch_created.emit(self._batch_id)

        results = []
        total = len(self._ids)

        for index, doc_id in enumerate(self._ids, start=1):
            if self._cancel_requested:
                self._cancelled = True
                break

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

            self._state_service.mark_processing(self._batch_id, doc_id)
            start = time.monotonic()

            result = self._process_with_retry(doc_id, file_service)

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
                self._state_service.mark_failed(
                    self._batch_id, doc_id, result.error
                )

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

        self._finish_batch(results, total)
        self.run_finished.emit(results)

    def _process_with_retry(self, doc_id, file_service) -> ProcessResult:
        """Procesa un documento reintentando una vez si la sesión SAP murió."""
        context = {
            "dry_run": self._dry_run,
            "log_service": self._log_service,
            "file_service": file_service,
            "max_retries": self._config.get("max_retries"),
            "batch_id": self._batch_id,
            "state_service": self._state_service,
        }
        for attempt in (1, 2):
            try:
                session = self._get_session()
                return self._module.process_one(session, doc_id, context)
            except Exception as exc:
                self._drop_session()
                if attempt == 2:
                    return ProcessResult(document_id=doc_id, ok=False, error=str(exc))
                # Segundo intento con sesión nueva; si SAP desapareció del todo,
                # get_session volverá a fallar y se marca como error real.
        return ProcessResult(document_id=doc_id, ok=False, error="inaccesible")

    def _finish_batch(self, results, total) -> None:
        processed = len(results)
        if self._cancelled and processed < total:
            status = "CANCELLED"
        elif processed and all(r.ok for r in results):
            status = "COMPLETED"
        elif any(r.ok for r in results):
            status = "PARTIAL"
        else:
            status = "FAILED"
        self._state_service.set_batch_status(self._batch_id, status)

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

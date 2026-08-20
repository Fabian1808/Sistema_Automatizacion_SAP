import time

from PySide6.QtCore import QThread, Signal

from ..modules.base import ProcessResult
from ..sap.sap_connection import SapConnection
from ..services.file_service import FileService


class DocumentWorker(QThread):
    progress = Signal(int, int, str)
    document_done = Signal(object)
    run_finished = Signal(list)

    def __init__(self, module, document_ids, config, log_service, dry_run):
        super().__init__()
        self._module = module
        self._ids = document_ids
        self._config = config
        self._log_service = log_service
        self._dry_run = dry_run

    def run(self):
        file_service = FileService(
            self._config.output_folder,
            overwrite=self._config.get("overwrite_existing"),
        )
        results = []
        total = len(self._ids)
        for index, doc_id in enumerate(self._ids, start=1):
            self.progress.emit(index - 1, total, doc_id)
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
                    },
                )
            except Exception as exc:
                result = ProcessResult(document_id=doc_id, ok=False, error=str(exc))
            result.duration = time.monotonic() - start
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
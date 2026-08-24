from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .run_panel import RunPanel


class HesView(QWidget):
    def __init__(self, config, log_service):
        super().__init__()
        self._config = config
        self._log_service = log_service

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Descarga masiva de HES")
        title.setObjectName("title")
        subtitle = QLabel(
            "Pegue los números de HES (uno por línea) o impórtelos desde Excel/CSV."
        )
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        self.panel = RunPanel(config, "HES", "HES")
        layout.addWidget(self.panel, 1)
        self.panel.run_requested.connect(self._launch)

    def _launch(self, ids, dry_run, batch_id="", resume=False):
        from ..modules.registry import build_default_registry
        from .worker import DocumentWorker

        module = build_default_registry().get("hes")
        self.panel.start_run(ids, batch_id)
        self._worker = DocumentWorker(
            module, ids, self._config, self._log_service, dry_run, batch_id, resume
        )
        self.panel._worker = self._worker
        self.panel.cancel_requested.connect(
            lambda w=self._worker: w.request_cancel()
        )
        self._worker.run_finished.connect(
            lambda results: setattr(self.panel, "_was_cancelled", self._worker.cancelled)
        )
        self._worker.progress.connect(self.panel.on_progress)
        self._worker.document_done.connect(self.panel.on_document)
        self._worker.run_finished.connect(self.panel.on_finished)
        self._worker.start()

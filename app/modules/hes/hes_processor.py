from __future__ import annotations
from typing import Any, Dict, Optional

from app.modules.base import DocumentModule, ProcessResult
from app.sap.interfaces import ISapClient, SapError
from app.services.file_service import FileService
from app.services.state_service import StateService
from app.modules.hes.steps import HesOrchestrator
from app.config.sap_config_loader import get_hes_selectors


class HesModule(DocumentModule):
    module_id = "hes"
    module_name = "Hoja de Entrada de Servicios"

    def __init__(self):
        self.selectors = get_hes_selectors()
        self.orchestrator = HesOrchestrator(self.selectors)

    def validate_ids(self, lines: list) -> dict:
        from app.utils.ids import analyze_ids
        return analyze_ids(lines)

    def process_one(self, client: ISapClient, document_id: str, context: dict) -> ProcessResult:
        dry_run = bool(context.get("dry_run"))
        file_service = context.get("file_service")
        state_service = context.get("state_service")
        batch_id = context.get("batch_id")

        result = ProcessResult(document_id=document_id, ok=False, error="")
        import time as _time

        try:
            if not dry_run and not file_service:
                raise RuntimeError(
                    "Ejecución real requiere FileService configurado (ruta de salida)"
                )

            start = _time.monotonic()
            target = None
            if not dry_run and file_service:
                target = file_service.resolve_path("HES", document_id)
                target.parent.mkdir(parents=True, exist_ok=True)

            if state_service and batch_id:
                state_service.mark_processing(batch_id, document_id)

            result_dict = self.orchestrator.run(
                client=client,
                document_id=document_id,
                dry_run=dry_run,
                target_path=str(target) if target else ""
            )
            result.duration = _time.monotonic() - start

            if result_dict["ok"]:
                result.ok = True
                result.file_path = str(target) if target else ""
            else:
                result.error = result_dict.get("error", "Error desconocido")

        except SapError as e:
            result.error = str(e)
        except Exception as e:
            result.error = f"Error inesperado: {e}"

        if state_service and batch_id:
            if result.ok:
                state_service.mark_success(batch_id, document_id, result.file_path, result.duration)
            else:
                state_service.mark_failed(batch_id, document_id, result.error)

        return result
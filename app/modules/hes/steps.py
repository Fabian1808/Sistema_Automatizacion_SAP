from __future__ import annotations
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
from pathlib import Path

from app.sap.interfaces import ISapClient, SapError, SapElementNotFoundError
from app.services.file_service import FileService
from app.services.state_service import StateService
from app.config.sap_config_loader import get_hes_selectors, get_global_config

if TYPE_CHECKING:
    from app.sap.interfaces import ISapClient


@dataclass
class StepResult:
    ok: bool
    error: str = ""
    data: Any = None


class SapStep(ABC):
    """Paso atómico de automatización SAP. Testeable individualmente."""

    def __init__(self, name: str, selectors: Dict):
        self.name = name
        self.selectors = selectors

    @abstractmethod
    def execute(self, client: 'ISapClient', document_id: str, context: Dict) -> StepResult:
        pass

    def _wait_idle(self, client: 'ISapClient') -> None:
        client.wait_until_idle(timeout=self.selectors.get("timeouts", {}).get("default", 30))


class HesOpenTransaction(SapStep):
    def execute(self, client: 'ISapClient', document_id: str, context: Dict) -> StepResult:
        try:
            client.start_transaction(self.selectors["transaction"])
            self._wait_idle(client)
            return StepResult(ok=True)
        except Exception as e:
            return StepResult(ok=False, error=f"Abrir transacción: {e}")


class HesPositionTree(SapStep):
    def execute(self, client: 'ISapClient', document_id: str, context: Dict) -> StepResult:
        try:
            tree = client.find_element(self.selectors["tree"]["root_path"])
            tree.set_top_node(self.selectors["tree"]["root_node"])
            return StepResult(ok=True)
        except Exception as e:
            return StepResult(ok=False, error=f"Posicionar árbol: {e}")


class HesOpenSearch(SapStep):
    def execute(self, client: 'ISapClient', document_id: str, context: Dict) -> StepResult:
        try:
            client.find_element(self.selectors["buttons"]["otras_entradas"]).press()
            client.wait_until_idle()
            return StepResult(ok=True)
        except Exception as e:
            return StepResult(ok=False, error=f"Abrir buscador: {e}")


class HesSearchDocument(SapStep):
    def execute(self, client: 'ISapClient', document_id: str, context: Dict) -> StepResult:
        try:
            pop = self.selectors["search_popup"]
            field = client.find_element(pop["hes_field"])
            field.set_text(document_id)
            field.set_focus()
            try:
                field._com.caretPosition = len(document_id)
            except Exception:
                pass
            client.find_element(pop["ok_button"]).press()
            client.wait_until_idle()
            return StepResult(ok=True)
        except Exception as e:
            return StepResult(ok=False, error=f"Buscar HES: {e}")


class HesCheckError(SapStep):
    def execute(self, client: 'ISapClient', document_id: str, context: Dict) -> StepResult:
        try:
            text = client.get_status_bar_text()
            if not text:
                return StepResult(ok=True)
            keywords = self.selectors.get("error_keywords", [])
            for kw in keywords:
                if kw.lower() in text.lower():
                    return StepResult(ok=False, error=text.strip())
            return StepResult(ok=True)
        except Exception as e:
            return StepResult(ok=False, error=f"Verificar error: {e}")


class HesOpenMessages(SapStep):
    def execute(self, client: 'ISapClient', document_id: str, context: Dict) -> StepResult:
        try:
            client.send_vkey(self.selectors["vkeys"]["f5"])
            client.wait_until_idle()
            client.send_vkey(self.selectors["vkeys"]["f7"])
            client.wait_until_idle()
            return StepResult(ok=True)
        except Exception as e:
            return StepResult(ok=False, error=f"Abrir mensajes: {e}")


class HesAddMessage(SapStep):
    """Agrega mensaje NEU en primera fila vacía - lógica dinámica."""

    def execute(self, client: 'ISapClient', document_id: str, context: Dict) -> StepResult:
        try:
            tbl = self.selectors["message_table"]
            max_rows = tbl.get("max_rows", 20)
            kscl_path = tbl["kscl_column"]
            nacha_path = tbl["nacha_column"]
            kscl_val = tbl["kscl_value"]
            nacha_val = tbl["nacha_value"]

            found_row = -1
            for row in range(max_rows):
                cell_path = kscl_path.format(row=row)
                cell = client.find_optional(cell_path)
                if cell is None:
                    break
                try:
                    text = cell.get_text()
                except Exception:
                    text = ""
                if not text.strip():
                    found_row = row
                    break

            if found_row == -1:
                return StepResult(ok=False, error="No se encontró fila vacía en tabla mensajes")

            client.find_element(kscl_path.format(row=found_row)).set_text(kscl_val)
            client.find_element(nacha_path.format(row=found_row)).set_combo_key(nacha_val)
            client.find_element(nacha_path.format(row=found_row)).set_focus()
            return StepResult(ok=True, data={"row": found_row})
        except Exception as e:
            return StepResult(ok=False, error=f"Agregar mensaje NEU: {e}")


class HesPressSave(SapStep):
    def execute(self, client: 'ISapClient', document_id: str, context: Dict) -> StepResult:
        try:
            client.find_element(self.selectors["buttons"]["save_message"]).press()
            client.wait_until_idle()
            return StepResult(ok=True)
        except Exception as e:
            return StepResult(ok=False, error=f"Guardar mensaje: {e}")


class HesSetDispatchTime(SapStep):
    def execute(self, client: 'ISapClient', document_id: str, context: Dict) -> StepResult:
        try:
            d = self.selectors["dispatch"]
            client.find_element(d["vsztp_combo"]).set_combo_key(d["vsztp_value"])
            client.find_element(self.selectors["buttons"]["enter"]).press()
            client.find_element(self.selectors["buttons"]["save_message"]).press()
            client.wait_until_idle()
            return StepResult(ok=True)
        except Exception as e:
            return StepResult(ok=False, error=f"Hora despacho: {e}")


class HesSetOutputDevice(SapStep):
    def execute(self, client: 'ISapClient', document_id: str, context: Dict) -> StepResult:
        try:
            od = self.selectors["output_device"]
            client.find_element(od["ldest_field"]).set_text(od["ldest_value"])
            client.find_element(od["tdover_combo"]).set_combo_key(od["tdover_value"])
            client.find_element(od["tdover_combo"]).set_focus()
            client.find_element(self.selectors["buttons"]["enter"]).press()
            client.find_element(self.selectors["buttons"]["save_message"]).press()
            client.wait_until_idle()
            return StepResult(ok=True)
        except Exception as e:
            return StepResult(ok=False, error=f"Dispositivo salida: {e}")


class HesSaveDocument(SapStep):
    def execute(self, client: 'ISapClient', document_id: str, context: Dict) -> StepResult:
        try:
            client.find_element(self.selectors["buttons"]["grabar"]).press()
            client.wait_until_idle()
            return StepResult(ok=True)
        except Exception as e:
            return StepResult(ok=False, error=f"Grabar HES: {e}")


class HesOpenSp01(SapStep):
    def execute(self, client: 'ISapClient', document_id: str, context: Dict) -> StepResult:
        try:
            client.start_transaction(self.selectors["sp01_transaction"])
            client.wait_until_idle()
            return StepResult(ok=True)
        except Exception as e:
            return StepResult(ok=False, error=f"Abrir SP01: {e}")


class HesRefreshSpool(SapStep):
    def execute(self, client: 'ISapClient', document_id: str, context: Dict) -> StepResult:
        try:
            client.find_element(self.selectors["sp01"]["refresh_button"]).press()
            client.wait_until_idle()
            return StepResult(ok=True)
        except Exception as e:
            return StepResult(ok=False, error=f"Refrescar spool: {e}")


class HesPrintSpool(SapStep):
    def execute(self, client: 'ISapClient', document_id: str, context: Dict) -> StepResult:
        try:
            sp = self.selectors["sp01"]
            client.find_element(sp["checkbox_first"]).set_checked(True)
            client.find_element(sp["checkbox_first"]).set_focus()
            client.find_element(sp["print_button"]).press()
            client.wait_until_idle()
            client.active_window_send_vkey(self.selectors["vkeys"]["enter"])
            client.close_popup()
            return StepResult(ok=True)
        except Exception as e:
            return StepResult(ok=False, error=f"Imprimir spool: {e}")


class HesGeneratePdf(SapStep):
    """Genera PDF via diálogo nativo. Requiere native_dialog service."""

    def __init__(self, name: str, selectors: Dict, native_dialog_service: Any):
        super().__init__(name, selectors)
        self._native_dialog = native_dialog_service

    def execute(self, client: 'ISapClient', document_id: str, context: Dict) -> StepResult:
        try:
            target = context.get("target_path")
            if not target:
                return StepResult(ok=False, error="Ruta destino no provista")

            client.active_window_send_vkey(self.selectors["vkeys"]["shift_f1"])
            time.sleep(self.selectors["timeouts"]["long_wait"])

            from app.services.native_dialog import save_pdf_via_dialog
            from pathlib import Path
            save_pdf_via_dialog(
                Path(target),
                wait_timeout=self.selectors["timeouts"]["pdf_wait"]
            )
            return StepResult(ok=True)
        except Exception as e:
            return StepResult(ok=False, error=f"Generar PDF: {e}")


class HesOrchestrator:
    """Orquesta la secuencia de pasos HES. Permite dry-run y testing granular."""

    def __init__(self, selectors: Dict, native_dialog_service: Any = None):
        self.selectors = selectors
        self.steps: List[SapStep] = [
            HesOpenTransaction("Abrir ML81N", selectors),
            HesPositionTree("Posicionar árbol", selectors),
            HesOpenSearch("Abrir buscador", selectors),
            HesSearchDocument("Buscar HES", selectors),
            HesCheckError("Verificar HES", selectors),
            HesOpenMessages("Abrir mensajes (F5/F7)", selectors),
            HesAddMessage("Agregar mensaje NEU", selectors),
            HesPressSave("Guardar mensaje", selectors),
            HesSetDispatchTime("Hora despacho", selectors),
            HesSetOutputDevice("Dispositivo LOCL", selectors),
            HesSaveDocument("Grabar HES", selectors),
            HesOpenSp01("Abrir SP01", selectors),
            HesRefreshSpool("Refrescar spool", selectors),
            HesPrintSpool("Marcar e imprimir", selectors),
        ]
        self._pdf_step = None

    def set_pdf_service(self, service: Any):
        from app.modules.hes.steps import HesGeneratePdf
        self._pdf_step = HesGeneratePdf("Generar PDF", self.selectors, service)

    def run(self, client: 'ISapClient', document_id: str, dry_run: bool = False, target_path: str = "") -> Dict[str, Any]:
        """Ejecuta secuencia completa. Retorna dict con resultados."""
        results = {"steps": [], "ok": True, "error": ""}
        context = {"dry_run": dry_run, "target_path": target_path}

        for step in self.steps:
            if dry_run and step.name in ("Generar PDF",):
                continue
            result = step.execute(client, document_id, context)
            results["steps"].append({"name": step.name, "ok": result.ok, "error": result.error})
            if not result.ok:
                results["ok"] = False
                results["error"] = f"{step.name}: {result.error}"
                break

        if not dry_run and results["ok"] and self._pdf_step:
            result = self._pdf_step.execute(client, document_id, {"target_path": target_path})
            results["steps"].append({"name": "Generar PDF", "ok": result.ok, "error": result.error})
            if not result.ok:
                results["ok"] = False
                results["error"] = result.error

        return results

    def run_step_by_step(self, client: 'ISapClient', document_id: str, step_names: List[str], dry_run: bool = False) -> Dict[str, Any]:
        step_map = {s.name: s for s in self.steps}
        results = {"steps": [], "ok": True, "error": ""}
        context = {"dry_run": dry_run}

        for name in step_names:
            step = next((s for s in self.steps if s.name == name), None)
            if not step:
                results["ok"] = False
                results["error"] = f"Paso no encontrado: {name}"
                break
            result = step.execute(client, document_id, context)
            results["steps"].append({"name": step.name, "ok": result.ok, "error": result.error})
            if not result.ok:
                results["ok"] = False
                results["error"] = f"{step.name}: {result.error}"
                break

        return results
import time

from ..modules.base import DocumentModule, ProcessResult
from ..sap.sap_exceptions import SapError
from ..services.native_dialog import save_pdf_via_dialog
from ..utils.ids import analyze_ids
from . import macro_model as model


class MacroModule(DocumentModule):
    module_id = "macro"
    module_name = "Macro personalizada"

    def __init__(self, macro):
        self.macro = macro
        self.module_name = macro.name or "Macro"

    def validate_ids(self, lines):
        return analyze_ids(lines)

    def process_one(self, session, document_id, context):
        dry_run = bool(context.get("dry_run"))
        file_service = context.get("file_service")
        result = ProcessResult(document_id=document_id, ok=False, error="")
        try:
            target = None
            if not dry_run:
                doc_type = self.macro.output_doc_type or self.macro.name
                target = file_service.resolve_path(doc_type, document_id)
                target.parent.mkdir(parents=True, exist_ok=True)
            self._run(session, document_id, target, dry_run)
            result.ok = True
            result.file_path = str(target) if target else ""
        except SapError as exc:
            result.error = str(exc)
        except Exception as exc:
            result.error = f"Error inesperado: {exc}"
        return result

    def _run(self, session, document_id, target, dry_run):
        for index, step in enumerate(self.macro.steps, start=1):
            if dry_run and step.action == "save_pdf":
                break
            label = model.ACTION_LABELS.get(step.action, step.action)
            try:
                self._execute(session, step, document_id, target)
            except SapError as exc:
                raise SapError(f"Paso {index} ({label}): {exc}") from exc
            except Exception as exc:
                raise SapError(f"Paso {index} ({label}): {exc}") from exc

    def _execute(self, session, step, document_id, target):
        action = step.action
        value = step.value.replace("{ID}", document_id) if step.value else ""
        if action == "transaction":
            session.start_transaction(value)
            session.wait_until_idle()
        elif action == "press":
            session.press(step.path)
        elif action == "set_text":
            session.set_text(step.path, value)
        elif action == "set_combo":
            session.set_combo_key(step.path, value)
        elif action == "set_checked":
            session.set_checked(step.path, value.lower() in ("true", "1"))
        elif action == "focus":
            session.find_by_id(step.path).SetFocus()
        elif action == "send_vkey":
            session.send_vkey(step.key, window=step.path or "wnd[0]")
        elif action == "send_vkey_active":
            session.active_window_send_vkey(step.key)
        elif action == "set_tree_node":
            session.find_by_id(step.path).topNode = value
        elif action == "maximize":
            session.find_by_id(step.path or "wnd[0]").maximize()
        elif action == "wait_idle":
            session.wait_until_idle()
        elif action == "sleep":
            time.sleep(float(step.value or 0))
        elif action == "wait_popup_close":
            session.wait_for(
                lambda: session.find_optional(step.path or "wnd[1]") is None
            )
        elif action == "close_popup":
            session.close_popup(step.path or "wnd[1]")
        elif action == "check_error":
            self._check_error(session)
        elif action == "save_pdf":
            save_pdf_via_dialog(target)
        elif action == "find_empty_row":
            self._execute_find_empty_row(session, step)

    def _check_error(self, session):
        text = session.status_bar_text()
        if not text:
            return
        for keyword in ("no existe", "no encontrad", "bloquead", "error"):
            if keyword.lower() in text.lower():
                raise SapError(text.strip())

    def _execute_find_empty_row(self, session, step):
        """Busca la primera fila vacía en una tabla y escribe valores."""
        column_path = step.column_path or step.path
        write_value = step.write_value.replace("{ID}", "") if step.write_value else ""
        combo_path = step.combo_path
        combo_value = step.combo_value
        max_rows = step.max_rows or 20

        found_row = -1
        for row in range(max_rows):
            path = column_path.replace("{row}", str(row))
            cell = session.find_optional(path)
            if cell is None:
                break
            try:
                text = cell.Text
            except Exception:
                text = ""
            if not str(text).strip():
                found_row = row
                break

        if found_row == -1:
            raise SapError(
                f"No se encontró un renglón vacío en la tabla (buscadas {max_rows} filas)."
            )

        # Escribir valor en la columna principal
        target_path = column_path.replace("{row}", str(found_row))
        if write_value:
            session.set_text(target_path, write_value)

        # Configurar combo si se especificó
        if combo_path:
            combo_target = combo_path.replace("{row}", str(found_row))
            if combo_value:
                session.set_combo_key(combo_target, combo_value)
            session.find_by_id(combo_target).SetFocus()
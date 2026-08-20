import time

from ...sap.sap_exceptions import SapError
from ...services.native_dialog import save_pdf_via_dialog
from ...utils.ids import analyze_ids
from ..base import DocumentModule, ProcessResult
from . import hes_config as cfg


class HesModule(DocumentModule):
    module_id = "hes"
    module_name = "Hoja de Entrada de Servicios"

    def validate_ids(self, lines):
        return analyze_ids(lines)

    def process_one(self, session, document_id, context):
        dry_run = bool(context.get("dry_run"))
        file_service = context.get("file_service")
        result = ProcessResult(document_id=document_id, ok=False, error="")
        try:
            target = None
            if not dry_run:
                target = file_service.resolve_path("HES", document_id)
                target.parent.mkdir(parents=True, exist_ok=True)
            self._run_flow(session, document_id, dry_run=dry_run, target=target)
            result.ok = True
            result.file_path = str(target) if target else ""
        except SapError as exc:
            result.error = str(exc)
        except Exception as exc:
            result.error = f"Error inesperado: {exc}"
        return result

    def _run_flow(self, session, hes, dry_run, target):
        self._step(session, "Abrir transacción ML81N", lambda: self._open_hes(session))
        self._step(session, "Posicionar árbol", lambda: self._position_tree(session))
        self._step(
            session,
            "Abrir buscador",
            lambda: session.press(cfg.BTN_OTRAS_ENTRADAS),
        )
        self._step(session, "Buscar la HES", lambda: self._search_hes(session, hes))
        self._step(
            session, "Verificar HES", lambda: self._check_hes_error(session)
        )
        self._step(
            session, "Abrir mensajes (F5/F7)", lambda: self._open_messages(session)
        )
        if dry_run:
            return
        self._step(
            session, "Agregar mensaje NEU", lambda: self._add_message_neu(session)
        )
        self._step(session, "Guardar mensaje", lambda: self._press_save(session))
        self._step(
            session, "Hora de despacho", lambda: self._set_dispatch_time(session)
        )
        self._step(
            session, "Dispositivo LOCL", lambda: self._set_output_device(session)
        )
        self._step(session, "Grabar HES", lambda: session.press(cfg.BTN_GRABAR))
        self._step(session, "Abrir SP01", lambda: self._start_sp01(session))
        self._step(
            session, "Refrescar lista spool", lambda: self._refresh_spool(session)
        )
        self._step(session, "Marcar e imprimir", lambda: self._print_spool(session))
        self._step(session, "Generar PDF", lambda: self._print_pdf(session, target))

    @staticmethod
    def _step(session, name, fn):
        try:
            fn()
        except Exception as exc:
            raise SapError(f"Paso '{name}': {exc}") from exc

    @staticmethod
    def _open_hes(session):
        session.start_transaction(cfg.HES_TRANSACTION)
        session.wait_until_idle()

    @staticmethod
    def _start_sp01(session):
        session.start_transaction(cfg.SP01_TRANSACTION)
        session.wait_until_idle()

    @staticmethod
    def _position_tree(session):
        session.find_by_id(cfg.TREE_ROOT).topNode = cfg.TREE_ROOT_NODE

    @staticmethod
    def _search_hes(session, hes):
        field = session.find_by_id(cfg.POPUP_HES_FIELD)
        field.text = hes
        field.SetFocus()
        field.caretPosition = len(hes)
        session.press(cfg.POPUP_OK)
        session.wait_until_idle()

    @staticmethod
    def _check_hes_error(session):
        text = session.status_bar_text()
        if not text:
            return
        for keyword in cfg.ERROR_KEYWORDS:
            if keyword.lower() in text.lower():
                raise SapError(text.strip())

    @staticmethod
    def _open_messages(session):
        session.send_vkey(cfg.VKEY_F5)
        session.wait_until_idle()
        session.send_vkey(cfg.VKEY_F7)
        session.wait_until_idle()

    @staticmethod
    def _add_message_neu(session):
        row = HesModule._first_empty_row(session)
        session.set_text(cfg.MSG_TABLE_KSCHL.format(row=row), cfg.KSCHL_VALUE)
        session.set_combo_key(
            cfg.MSG_TABLE_NACHA.format(row=row), cfg.NACHA_VALUE
        )
        session.find_by_id(cfg.MSG_TABLE_NACHA.format(row=row)).SetFocus()

    @staticmethod
    def _first_empty_row(session):
        for row in range(0, 21):
            cell = session.find_optional(cfg.MSG_TABLE_KSCHL.format(row=row))
            if cell is None:
                break
            try:
                text = cell.Text
            except Exception:
                text = ""
            if not str(text).strip():
                return row
        raise SapError(
            "No se encontró un renglón vacío en la tabla de mensajes de la HES."
        )

    @staticmethod
    def _press_save(session):
        session.press(cfg.BTN_TBAR_11)
        session.wait_until_idle()

    @staticmethod
    def _set_dispatch_time(session):
        session.set_combo_key(cfg.CMB_VSZTP, cfg.VSZTP_VALUE)
        session.press(cfg.BTN_TBAR_3)
        session.press(cfg.BTN_TBAR_11)
        session.wait_until_idle()

    @staticmethod
    def _set_output_device(session):
        session.set_text(cfg.CTXT_LDEST, cfg.LDEST_VALUE)
        session.set_combo_key(cfg.CMB_TDOCOVER, cfg.TDOCOVER_VALUE)
        session.find_by_id(cfg.CMB_TDOCOVER).SetFocus()
        session.press(cfg.BTN_TBAR_3)
        session.press(cfg.BTN_TBAR_11)
        session.wait_until_idle()

    @staticmethod
    def _refresh_spool(session):
        session.press(cfg.SP01_REFRESH)
        session.wait_until_idle()

    @staticmethod
    def _print_spool(session):
        checkbox = session.find_by_id(cfg.SP01_CHK)
        checkbox.Selected = True
        checkbox.SetFocus()
        session.press(cfg.SP01_PRINT)
        session.wait_until_idle()
        session.active_window_send_vkey(cfg.VKEY_ENTER)
        session.close_popup()

    @staticmethod
    def _print_pdf(session, target):
        session.active_window_send_vkey(cfg.VKEY_SHIFT_F1)
        time.sleep(cfg.LONG_WAIT)
        save_pdf_via_dialog(target, wait_timeout=cfg.PDF_WAIT_TIMEOUT)
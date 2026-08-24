from sap_document_automation.modules.hes.hes_processor import HesModule
from sap_document_automation.sap.session import SapSession
from tests.fakes import FakeSession


def _wrapped():
    return SapSession(FakeSession(), timeout=1)


def test_dry_run_completes():
    module = HesModule()
    fake = FakeSession()
    result = module.process_one(SapSession(fake, timeout=1), "1042866626", {"dry_run": True})
    assert result.ok
    # Dry-run ejecuta el flujo completo: búsqueda en ML81N + spool en SP01
    assert fake.transactions == ["ML81N", "SP01"]


def test_dry_run_fills_popup_with_id():
    module = HesModule()
    fake = FakeSession()
    result = module.process_one(SapSession(fake, timeout=1), "1042866626", {"dry_run": True})
    assert result.ok
    field = fake._elements["wnd[1]/usr/ctxtRM11R-LBLNI"]
    assert field.text == "1042866626"


def test_real_run_without_file_service_fails_cleanly():
    module = HesModule()
    result = module.process_one(_wrapped(), "1042866626", {"dry_run": False})
    assert not result.ok
    assert "Error inesperado" in result.error

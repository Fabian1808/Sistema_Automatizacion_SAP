from sap_document_automation.macros.macro_model import Macro, MacroStep
from sap_document_automation.macros.macro_processor import MacroModule
from sap_document_automation.sap.session import SapSession
from tests.fakes import FakeSession

MACRO = Macro(
    name="Demo",
    output_doc_type="HES",
    steps=[
        MacroStep(action="transaction", value="ML81N"),
        MacroStep(action="set_text", path="wnd[1]/usr/ctxtRM11R-LBLNI", value="{ID}"),
        MacroStep(action="press", path="wnd[1]/tbar[0]/btn[0]"),
        MacroStep(action="send_vkey", path="wnd[0]", key=5),
        MacroStep(action="save_pdf"),
    ],
)


def test_dry_run_skips_save_pdf_and_completes():
    module = MacroModule(MACRO)
    fake = FakeSession()
    result = module.process_one(SapSession(fake, timeout=1), "1042866626", {"dry_run": True})
    assert result.ok
    assert fake.transactions == ["ML81N"]


def test_id_placeholder_replaced():
    module = MacroModule(MACRO)
    fake = FakeSession()
    result = module.process_one(SapSession(fake, timeout=1), "1042866626", {"dry_run": True})
    assert result.ok
    field = fake._elements["wnd[1]/usr/ctxtRM11R-LBLNI"]
    assert field.text == "1042866626"


def test_missing_file_service_fails_cleanly():
    module = MacroModule(MACRO)
    result = module.process_one(FakeSession(), "1042866626", {"dry_run": False})
    assert not result.ok
    assert "Error inesperado" in result.error
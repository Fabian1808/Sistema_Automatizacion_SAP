from app.macros.macro_model import Macro, MacroStep
from app.macros.macro_service import MacroService


def test_save_and_load_roundtrip(tmp_path):
    service = MacroService(base_dir=tmp_path)
    macro = Macro(
        name="Mi proceso",
        description="Prueba",
        output_doc_type="HES",
        steps=[
            MacroStep(action="transaction", value="ML81N"),
            MacroStep(action="set_text", path="wnd[1]/usr/ctxtRM11R-LBLNI", value="{ID}"),
            MacroStep(action="press", path="wnd[1]/tbar[0]/btn[0]"),
        ],
    )
    service.save(macro)
    assert service.list_macros() == ["Mi proceso"]
    loaded = service.load("Mi proceso")
    assert loaded.name == macro.name
    assert loaded.output_doc_type == "HES"
    assert [s.action for s in loaded.steps] == ["transaction", "set_text", "press"]
    assert loaded.steps[1].value == "{ID}"


def test_delete(tmp_path):
    service = MacroService(base_dir=tmp_path)
    service.save(Macro(name="borrar"))
    service.delete("borrar")
    assert service.list_macros() == []
from sap_document_automation.core.error_catalog import detect_stage, explain_error


def test_sap_not_running_maps_to_friendly_message():
    info = explain_error("SAP GUI is not running (0x800401E4)")
    assert "SAP" in info["motivo"]
    assert "SAP GUI" in info["recomendacion"]
    assert info["etapa"]


def test_scripting_disabled():
    info = explain_error("Scripting is disabled by user")
    assert "Scripting" in info["motivo"]


def test_timeout_error():
    info = explain_error("Timeout esperando respuesta")
    assert "tiempo máximo" in info["motivo"]


def test_document_not_found():
    info = explain_error("HES 1042866626 no encontrada en el sistema")
    assert "no existe o no es accesible" in info["motivo"]


def test_unknown_error_has_generic_fallback_with_technical_detail():
    raw = "ValueError raro xyz"
    info = explain_error(raw)
    assert info["motivo"] == "No se pudo completar la operación."
    assert "ValueError" in info["detalle"]


def test_empty_error_is_safe():
    info = explain_error("")
    assert info["motivo"]
    assert info["recomendacion"]


def test_detect_stage_categories():
    assert detect_stage("error de session SAPGUI") == "Conexión con SAP"
    assert detect_stage("wnd[0] vkey fallo") == "Navegación en SAP"
    assert detect_stage("documento no encontrado") == "Búsqueda del documento"
    assert detect_stage("fallo al imprimir pdf") == "Impresión / exportación"
    assert detect_stage("cualquier otra cosa") == "Procesamiento"

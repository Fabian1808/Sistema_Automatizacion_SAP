import pytest

from sap_document_automation.modules.registry import build_default_registry


def test_registry_exposes_metadata_for_catalog():
    metas = build_default_registry().metadata()
    assert metas, "el registro debe exponer al menos una automatización"
    for meta in metas:
        assert meta["id"]
        assert meta["name"]
        assert isinstance(meta["description"], str)
        assert isinstance(meta["available"], bool)


def test_hes_is_available_and_oc_placeholder_not():
    registry = build_default_registry()
    by_id = {m["id"]: m for m in registry.metadata()}
    assert by_id["hes"]["available"] is True
    assert by_id["oc"]["available"] is False
    assert registry.get("oc") is not None  # marcador consultable
    with pytest.raises(AttributeError):
        registry.get("oc").process_one  # el placeholder no es procesable

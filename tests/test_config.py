import json

from sap_document_automation.services.config_service import ConfigService


def test_defaults(tmp_path):
    cfg = ConfigService(base_dir=tmp_path)
    assert cfg.get("max_retries") == 2
    assert cfg.get("overwrite_existing") is False
    assert cfg.get("sap_timeout_seconds") == 30


def test_save_and_reload(tmp_path):
    cfg = ConfigService(base_dir=tmp_path)
    cfg.set("max_retries", 5)
    cfg.set("overwrite_existing", True)
    cfg.save()
    cfg2 = ConfigService(base_dir=tmp_path)
    assert cfg2.get("max_retries") == 5
    assert cfg2.get("overwrite_existing") is True


def test_unknown_keys_ignored(tmp_path):
    (tmp_path / "settings.json").write_text(json.dumps({"password": "secret"}), encoding="utf-8")
    cfg = ConfigService(base_dir=tmp_path)
    assert "password" not in cfg.data
    assert cfg.get("max_retries") == 2


def test_output_folder_defaults_to_documents(tmp_path):
    cfg = ConfigService(base_dir=tmp_path)
    assert "SAP Documentos" in str(cfg.output_folder)

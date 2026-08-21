from __future__ import annotations
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sap_document_automation.infrastructure.crypto import DpapiCrypto, CryptoError  # noqa: E402
from sap_document_automation.services.config_service import ConfigService  # noqa: E402
from sap_document_automation.services.file_service import FileService  # noqa: E402


@pytest.mark.skipif(sys.platform != "win32", reason="DPAPI solo en Windows")
class TestDpapiCrypto:
    def test_roundtrip(self):
        crypto = DpapiCrypto()
        secret = "MiClaveSap*2026"
        encrypted = crypto.encrypt(secret)
        assert encrypted != secret
        assert crypto.decrypt(encrypted) == secret

    def test_encrypted_value_flag(self):
        crypto = DpapiCrypto()
        assert crypto.is_encrypted_value("enc:abc") is True
        assert crypto.is_encrypted_value("plain") is False

    def test_empty_string(self):
        crypto = DpapiCrypto()
        assert crypto.encrypt("") == ""
        assert crypto.decrypt("") == ""

    def test_wrong_entropy_fails(self):
        c1 = DpapiCrypto(entropy=b"uno")
        c2 = DpapiCrypto(entropy=b"dos")
        enc = c1.encrypt("dato")
        with pytest.raises(CryptoError):
            c2.decrypt(enc)


class TestConfigService:
    def test_set_get_plain_value(self, tmp_path):
        svc = ConfigService(config_dir=tmp_path)
        svc.set("last_output_folder", "C:/docs")
        assert svc.get("last_output_folder") == "C:/docs"
        # Persistencia
        svc2 = ConfigService(config_dir=tmp_path)
        assert svc2.get("last_output_folder") == "C:/docs"

    @pytest.mark.skipif(sys.platform != "win32", reason="DPAPI solo en Windows")
    def test_password_is_encrypted_on_disk(self, tmp_path):
        svc = ConfigService(config_dir=tmp_path)
        svc.set("password", "secreto123")
        raw = (tmp_path / "config.json").read_text(encoding="utf-8")
        assert "secreto123" not in raw

    @pytest.mark.skipif(sys.platform != "win32", reason="DPAPI solo en Windows")
    def test_credentials_roundtrip(self, tmp_path):
        svc = ConfigService(config_dir=tmp_path)
        svc.set_credentials(user="USUARIO1", password="pass123", client="100")
        creds = svc.get_credentials()
        assert creds["user"] == "USUARIO1"
        assert creds["password"] == "pass123"
        assert creds["client"] == "100"

    def test_missing_file_returns_empty(self, tmp_path):
        svc = ConfigService(config_dir=tmp_path / "no_existe")
        assert svc.get("cualquiera") is None


class TestFileService:
    def test_build_output_path(self, tmp_path):
        path = FileService.build_output_path(tmp_path, "HES", "2026", 8, "HES_1000.pdf")
        assert path.parent.name == "08-Agosto"
        assert path.parent.parent.name == "2026"
        assert path.parent.parent.parent.name == "HES"
        assert path.exists() is False or path.parent.exists()

    def test_unique_path_no_conflict(self, tmp_path):
        p = tmp_path / "doc.pdf"
        assert FileService.unique_path(p) == p

    def test_unique_path_with_conflict(self, tmp_path):
        p = tmp_path / "doc.pdf"
        p.write_bytes(b"%PDF-1.4")
        u1 = FileService.unique_path(p)
        assert u1.name == "doc_1.pdf"
        u1.write_bytes(b"%PDF-1.4")
        assert FileService.unique_path(p).name == "doc_2.pdf"

    def test_is_valid_pdf(self, tmp_path):
        good = tmp_path / "good.pdf"
        good.write_bytes(b"%PDF-1.7 " + b"x" * 200)
        bad = tmp_path / "bad.pdf"
        bad.write_bytes(b"no es pdf" + b"x" * 100)
        empty = tmp_path / "empty.pdf"
        empty.write_bytes(b"")
        assert FileService.is_valid_pdf(good) is True
        assert FileService.is_valid_pdf(bad) is False
        assert FileService.is_valid_pdf(empty) is False
        assert FileService.is_valid_pdf(tmp_path / "fantasma.pdf") is False

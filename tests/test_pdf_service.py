from sap_document_automation.services.pdf_service import is_valid_pdf, wait_for_file, wait_for_pdf


def test_wait_for_file_finds_existing(tmp_path):
    path = tmp_path / "a.pdf"
    path.write_bytes(b"x")
    assert wait_for_file(path, timeout=2)


def test_wait_for_file_missing(tmp_path):
    assert not wait_for_file(tmp_path / "missing.pdf", timeout=0.3)


def test_is_valid_pdf(tmp_path):
    path = tmp_path / "ok.pdf"
    path.write_bytes(b"%PDF-1.7 rest")
    assert is_valid_pdf(path)
    path.write_bytes(b"not a pdf")
    assert not is_valid_pdf(path)


def test_wait_for_pdf_ok(tmp_path):
    path = tmp_path / "ok.pdf"
    path.write_bytes(b"%PDF-1.7")
    assert wait_for_pdf(path, timeout=2) == ""


def test_wait_for_pdf_invalid(tmp_path):
    path = tmp_path / "bad.pdf"
    path.write_bytes(b"junk")
    assert "PDF" in wait_for_pdf(path, timeout=2)


def test_wait_for_pdf_missing(tmp_path):
    assert "no apareció" in wait_for_pdf(tmp_path / "nope.pdf", timeout=0.3)

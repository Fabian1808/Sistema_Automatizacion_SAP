from app.services.file_service import FileService


def test_builds_month_folder(tmp_path):
    fs = FileService(tmp_path, overwrite=False)
    path = fs.target_path("HES", "1042866626")
    assert path.suffix == ".pdf"
    assert path.parent.parent.parent.name == "HES"
    assert path.parent.parent.name.isdigit()
    assert path.name == "1042866626.pdf"


def test_duplicate_gets_copy(tmp_path):
    fs = FileService(tmp_path, overwrite=False)
    first = fs.resolve_path("HES", "1042866626")
    first.parent.mkdir(parents=True, exist_ok=True)
    first.write_bytes(b"x")
    second = fs.resolve_path("HES", "1042866626")
    assert second != first
    assert second.stem == "1042866626_copia1"


def test_overwrite_returns_same_path(tmp_path):
    fs = FileService(tmp_path, overwrite=True)
    first = fs.resolve_path("HES", "1042866626")
    second = fs.resolve_path("HES", "1042866626")
    assert first == second
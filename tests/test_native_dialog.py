from app.services.native_dialog import escape_sendkeys


def test_plain_path_unchanged():
    assert escape_sendkeys("1042866626.pdf") == "1042866626.pdf"


def test_special_characters_escaped():
    assert escape_sendkeys("a+b") == "a{+}b"
    assert escape_sendkeys("100%{x}") == "100{%}{{}x{}}"
    assert escape_sendkeys("a~b") == "a{~}b"


def test_path_with_spaces_kept():
    assert escape_sendkeys("SAP Documentos\\HES") == "SAP Documentos\\HES"
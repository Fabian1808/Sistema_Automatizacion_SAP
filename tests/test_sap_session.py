import pytest

from sap_document_automation.sap.sap_exceptions import SapElementNotFoundError
from sap_document_automation.sap.session import SapSession
from tests.fakes import FakeSession, FailingSession


def test_find_by_id_retries_then_raises():
    session = SapSession(FailingSession(), timeout=0.5)
    with pytest.raises(SapElementNotFoundError):
        session.find_by_id("wnd[0]")


def test_find_optional_returns_none():
    session = SapSession(FailingSession(), timeout=0.5)
    assert session.find_optional("wnd[0]") is None


def test_wait_until_idle_returns_true_when_free():
    session = SapSession(FakeSession(), timeout=1)
    assert session.wait_until_idle(timeout=1) is True


def test_wait_for_timeout_returns_false():
    session = SapSession(FakeSession(), timeout=0.3)
    assert session.wait_for(lambda: False, timeout=0.3, interval=0.05) is False


def test_status_bar_text_empty_on_fake():
    session = SapSession(FakeSession(), timeout=1)
    assert session.status_bar_text() == ""


def test_start_transaction():
    fake = FakeSession()
    session = SapSession(fake, timeout=1)
    session.start_transaction("ML81N")
    assert fake.transactions == ["ML81N"]


def test_close_popup_presses_first_button():
    fake = FakeSession()
    session = SapSession(fake, timeout=1)
    session.close_popup()
    button = fake._elements["wnd[1]/tbar[0]/btn[0]"]
    assert "press" in button.events


def test_send_vkey_and_active_window():
    fake = FakeSession()
    session = SapSession(fake, timeout=1)
    session.send_vkey(5)
    session.active_window_send_vkey(13)
    assert "vkey:5" in fake._elements["wnd[0]"].events
    assert "vkey:13" in fake.ActiveWindow.events
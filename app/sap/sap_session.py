import time

from .sap_exceptions import SapElementNotFoundError, SapSessionLostError


class _SapElementAdapter:
    """Adapta un elemento COM crudo a la interfaz SapElement (set_text/press/...)."""

    def __init__(self, raw):
        self._com = raw

    def set_text(self, value):
        try:
            self._com.text = value
        except Exception:
            self._com.value = value

    def get_text(self):
        try:
            return self._com.Text
        except Exception:
            return ""

    def press(self):
        self._com.press()

    def set_focus(self):
        self._com.SetFocus()

    def set_combo_key(self, key):
        self._com.key = key

    def set_checked(self, checked=True):
        try:
            self._com.Selected = checked
        except Exception:
            self._com.selected = checked

    def send_vkey(self, key):
        self._com.sendVKey(key)

    def set_top_node(self, node):
        self._com.topNode = node

    def exists(self):
        try:
            _ = self._com.Text
            return True
        except Exception:
            return False


class SapSession:
    def __init__(self, com_session, timeout=30):
        self._session = com_session
        self.timeout = timeout

    # --- interfaz nueva (ISapClient) ------------------------------------
    def find_element(self, path, timeout=None):
        return _SapElementAdapter(self.find_by_id(path, timeout=timeout))

    def get_status_bar_text(self):
        return self.status_bar_text()

    def get_window_state(self):
        from .sap_exceptions import SapError  # noqa: F401
        busy = True
        try:
            busy = bool(self._session.Busy)
        except Exception:
            pass
        from collections import namedtuple
        state = namedtuple("SapWindowState", ["busy", "status_bar_text"])
        return state(busy=busy, status_bar_text=self.status_bar_text())

    # --- interfaz clásica ------------------------------------------------

    def find_by_id(self, path, timeout=None):
        limit = time.monotonic() + (timeout or self.timeout)
        last_error = None
        while time.monotonic() < limit:
            try:
                return self._session.findById(path)
            except Exception as exc:
                last_error = exc
                time.sleep(0.5)
        raise SapElementNotFoundError(f"{path} ({last_error})")

    def find_optional(self, path):
        try:
            return _SapElementAdapter(self._session.findById(path))
        except Exception:
            return None

    def wait_for(self, condition, timeout=None, interval=0.5):
        limit = time.monotonic() + (timeout or self.timeout)
        while time.monotonic() < limit:
            if condition():
                return True
            time.sleep(interval)
        return False

    def wait_until_idle(self, timeout=None):
        return self.wait_for(lambda: not self._is_busy(), timeout=timeout)

    def _is_busy(self):
        try:
            return bool(self._session.Busy)
        except Exception as exc:
            raise SapSessionLostError(str(exc)) from exc

    def status_bar_text(self):
        element = self.find_optional("wnd[0]/sbar")
        if element is None:
            return ""
        try:
            return element.get_text()
        except Exception:
            return ""

    def popup_exists(self, path="wnd[1]"):
        return self.find_optional(path) is not None

    def close_popup(self, popup_path="wnd[1]"):
        if self.find_optional(popup_path) is None:
            return
        for button in ("tbar[0]/btn[0]", "usr/btnSPOP-OPTION1", "tbar[0]/btn[1]"):
            element = self.find_optional(f"{popup_path}/{button}")
            if element is not None:
                element.press()
                self.wait_until_idle()
                return
        self.send_vkey(0, window=popup_path)

    def start_transaction(self, tcode):
        try:
            self._session.StartTransaction(tcode)
        except Exception as exc:
            raise SapSessionLostError(str(exc)) from exc

    def press(self, path, timeout=None):
        self.find_by_id(path, timeout=timeout).press()

    def set_text(self, path, value, timeout=None):
        element = self.find_by_id(path, timeout=timeout)
        try:
            element.text = value
        except Exception:
            element.value = value

    def get_text(self, path, timeout=None):
        try:
            return self.find_by_id(path, timeout=timeout).Text
        except Exception:
            return ""

    def set_combo_key(self, path, key, timeout=None):
        element = self.find_by_id(path, timeout=timeout)
        element.key = key

    def set_checked(self, path, checked=True, timeout=None):
        element = self.find_by_id(path, timeout=timeout)
        try:
            element.Selected = checked
        except Exception:
            element.selected = checked

    def send_vkey(self, key, window="wnd[0]", timeout=None):
        self.find_by_id(window, timeout=timeout).sendVKey(key)

    def active_window_send_vkey(self, key):
        try:
            self._session.ActiveWindow.sendVKey(key)
        except Exception as exc:
            raise SapSessionLostError(str(exc)) from exc
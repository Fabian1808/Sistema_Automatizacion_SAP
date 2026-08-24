import time

from ..sap.sap_exceptions import SapError
from .pdf_service import wait_for_pdf

_shell = None

SAVE_DIALOG_TITLES = ["guardar como", "save as"]
LONG_WAIT = 8.0
DIALOG_TIMEOUT = 15
PDF_WAIT_TIMEOUT = 45


def _get_shell():
    global _shell
    if _shell is None:
        import win32com.client

        _shell = win32com.client.Dispatch("WScript.Shell")
    return _shell


def escape_sendkeys(text):
    special = "+^%~{}"
    return "".join(f"{{{ch}}}" if ch in special else ch for ch in text)


def send_keys(keys, delay=0.4):
    _get_shell().SendKeys(keys)
    if delay:
        time.sleep(delay)


def find_window(title_parts, timeout=DIALOG_TIMEOUT):
    import win32gui

    deadline = time.monotonic() + timeout
    parts = [part.lower() for part in title_parts]
    while time.monotonic() < deadline:
        matches = []

        def _collect(hwnd, _arg):
            if not win32gui.IsWindowVisible(hwnd):
                return
            title = win32gui.GetWindowText(hwnd).lower()
            if any(part in title for part in parts):
                matches.append(hwnd)

        win32gui.EnumWindows(_collect, None)
        if matches:
            return matches[0]
        time.sleep(0.5)
    return None


def activate_window(hwnd):
    import win32gui

    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass


def save_pdf_via_dialog(target, wait_timeout=PDF_WAIT_TIMEOUT):
    send_keys("{DOWN}")
    send_keys(" ")
    send_keys("^+{F8}", delay=LONG_WAIT)
    hwnd = find_window(SAVE_DIALOG_TITLES, timeout=DIALOG_TIMEOUT)
    if hwnd is None:
        raise SapError("No apareció la ventana 'Guardar como' del PDF.")
    activate_window(hwnd)
    time.sleep(1.0)
    send_keys("{ENTER}")
    send_keys("^a")
    send_keys(escape_sendkeys(str(target)))
    send_keys("{ENTER}")
    error = wait_for_pdf(target, timeout=wait_timeout)
    if error:
        raise SapError(error)
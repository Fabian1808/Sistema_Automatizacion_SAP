from __future__ import annotations
import time
import ctypes
import ctypes.wintypes
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

from ..core.exceptions import SapError


# Constantes Windows API
WM_SETTEXT = 0x000C
WM_GETTEXT = 0x000D
WM_GETTEXTLENGTH = 0x000E
WM_COMMAND = 0x0111
WM_CLOSE = 0x0010
BN_CLICKED = 0
IDOK = 1
IDCANCEL = 2

GW_CHILD = 5
GW_HWNDNEXT = 2

# FindWindowEx
FindWindowEx = ctypes.windll.user32.FindWindowExW
FindWindowEx.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.HWND, ctypes.wintypes.LPCWSTR, ctypes.wintypes.LPCWSTR]
FindWindowEx.restype = ctypes.wintypes.HWND

# SendMessage
SendMessage = ctypes.windll.user32.SendMessageW
SendMessage.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.UINT, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM]
SendMessage.restype = ctypes.c_ssize_t

# FindWindow
FindWindow = ctypes.windll.user32.FindWindowW
FindWindow.argtypes = [ctypes.wintypes.LPCWSTR, ctypes.wintypes.LPCWSTR]
FindWindow.restype = ctypes.wintypes.HWND

# EnumChildWindows
EnumChildWindows = ctypes.windll.user32.EnumChildWindows
EnumChildWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
EnumChildWindows.argtypes = [ctypes.wintypes.HWND, EnumChildWindowsProc, ctypes.wintypes.LPARAM]
EnumChildWindows.restype = ctypes.c_int

# GetClassName
GetClassName = ctypes.windll.user32.GetClassNameW
GetClassName.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.LPWSTR, ctypes.c_int]
GetClassName.restype = ctypes.c_int

# GetWindowText
GetWindowText = ctypes.windll.user32.GetWindowTextW
GetWindowText.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.LPWSTR, ctypes.c_int]
GetWindowText.restype = ctypes.c_int

# GetWindowTextLength
GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
GetWindowTextLength.argtypes = [ctypes.wintypes.HWND]
GetWindowTextLength.restype = ctypes.c_int

# SetForegroundWindow
SetForegroundWindow = ctypes.windll.user32.SetForegroundWindow
SetForegroundWindow.argtypes = [ctypes.wintypes.HWND]
SetForegroundWindow.restype = ctypes.c_bool

# IsWindowVisible
IsWindowVisible = ctypes.windll.user32.IsWindowVisible
IsWindowVisible.argtypes = [ctypes.wintypes.HWND]
IsWindowVisible.restype = ctypes.c_bool

# GetWindowTextLength
GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
GetWindowTextLength.argtypes = [ctypes.wintypes.HWND]
GetWindowTextLength.restype = ctypes.c_int

# PostMessage
PostMessage = ctypes.windll.user32.PostMessageW
PostMessage.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.UINT, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM]
PostMessage.restype = ctypes.c_bool


@dataclass
class SaveDialogResult:
    success: bool
    file_path: str = ""
    error: str = ""


class NativeDialogService:
    """Servicio para manejar diálogos nativos de Windows de forma segura (sin SendKeys)."""

    SAVE_DIALOG_TITLES = ["guardar como", "save as", "save as...", "guardar como..."]
    DIALOG_TIMEOUT = 15.0
    PDF_WAIT_TIMEOUT = 45.0
    LONG_WAIT = 8.0

    def __init__(self):
        self._found_dialogs: List[int] = []

    def save_pdf_via_dialog(self, target_path: str, wait_timeout: float = None) -> bool:
        """
        Guarda PDF via diálogo nativo 'Guardar como' usando Windows API directamente.
        No usa SendKeys - usa WM_SETTEXT para escribir la ruta.
        """
        wait_timeout = wait_timeout or self.PDF_WAIT_TIMEOUT
        target_path = str(target_path)

        try:
            # 1. Esperar a que aparezca el diálogo "Guardar como"
            hwnd = self._find_save_dialog()
            if not hwnd:
                raise SapError("No apareció la ventana 'Guardar como' del PDF.")

            # 2. Traer al frente
            self._activate_window(hwnd)
            time.sleep(0.5)

            # 3. Encontrar el campo de nombre de archivo (Edit control)
            edit_hwnd = self._find_filename_edit(hwnd)
            if not edit_hwnd:
                raise SapError("No se encontró el campo de nombre de archivo en el diálogo.")

            # 4. Escribir la ruta completa usando WM_SETTEXT (seguro, sin SendKeys)
            self._set_window_text(edit_hwnd, target_path)
            time.sleep(0.3)

            # 4b. Presionar Enter para guardar (via WM_COMMAND a IDOK)
            self._click_save_button(hwnd)

            # 5. Verificar que el archivo se guardó correctamente
            return self._wait_for_file(target_path, self.PDF_WAIT_TIMEOUT)

        except Exception as e:
            raise SapError(f"Error en diálogo nativo: {e}")

    def _find_save_dialog(self, timeout: float = None) -> Optional[int]:
        """Busca la ventana 'Guardar como' usando EnumWindows."""
        timeout = timeout or self.DIALOG_TIMEOUT
        deadline = time.monotonic() + timeout
        titles = [t.lower() for t in self.SAVE_DIALOG_TITLES]

        while time.monotonic() < deadline:
            self._found_dialogs = []

            def enum_proc(hwnd, lparam):
                if not IsWindowVisible(hwnd):
                    return True
                length = GetWindowTextLength(hwnd)
                if length > 0:
                    buffer = ctypes.create_unicode_buffer(length + 1)
                    GetWindowText(hwnd, buffer, length + 1)
                    title = buffer.value.lower()
                    for t in self.SAVE_DIALOG_TITLES:
                        if t.lower() in title:
                            self._found_dialogs.append(hwnd)
                            break
                return True

            ctypes.windll.user32.EnumWindows(
                ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)(lambda hwnd, lparam: enum_proc(hwnd, lparam)),
                0
            )

            if self._found_dialogs:
                return self._found_dialogs[0]
            time.sleep(0.3)
        return None

    def _activate_window(self, hwnd: int) -> bool:
        try:
            SetForegroundWindow(hwnd)
            return True
        except Exception:
            return False

    def _find_filename_edit(self, dialog_hwnd: int) -> Optional[int]:
        """Encuentra el control Edit del nombre de archivo en el diálogo."""
        found = []

        def enum_child(hwnd, lparam):
            class_name = ctypes.create_unicode_buffer(256)
            GetClassName(hwnd, class_name, 256)
            if class_name.value.lower() == "edit":
                # Verificar si es el campo de nombre de archivo (suelen ser el primer edit)
                found.append(hwnd)
                return False  # Detener enumeración
            return True

        EnumChildWindows(
            ctypes.wintypes.HWND(dialog_hwnd),
            EnumChildWindowsProc(lambda hwnd, lparam: enum_child(hwnd, lparam)),
            0
        )
        return found[0] if found else None

    def _set_window_text(self, hwnd: int, text: str) -> bool:
        """Establece texto en un control Edit usando WM_SETTEXT."""
        try:
            result = SendMessage(hwnd, WM_SETTEXT, 0, text)
            return result != 0
        except Exception:
            return False

    def _click_save_button(self, dialog_hwnd: int) -> bool:
        """Presiona el botón Guardar (IDOK) en el diálogo."""
        try:
            # Intentar enviar WM_COMMAND a IDOK
            result = SendMessage(
                ctypes.wintypes.HWND(dialog_hwnd),
                WM_COMMAND,
                ctypes.wintypes.WPARAM(IDOK),
                0
            )
            return result != 0
        except Exception:
            return False

    def _wait_for_file(self, path: str, timeout: float) -> bool:
        """Espera a que el archivo exista y sea un PDF válido."""
        import time
        from pathlib import Path

        deadline = time.monotonic() + timeout
        path_obj = Path(path)

        while time.monotonic() < deadline:
            if path_obj.exists() and path_obj.stat().st_size > 0:
                # Verificar que es PDF válido
                try:
                    with path_obj.open("rb") as f:
                        if f.read(5) == b"%PDF-":
                            # Verificar estabilidad (tamaño no cambia)
                            size1 = path_obj.stat().st_size
                            time.sleep(0.5)
                            size2 = path_obj.stat().st_size
                            if size1 == size2:
                                return True
                except Exception:
                    pass
            time.sleep(0.3)
        return False
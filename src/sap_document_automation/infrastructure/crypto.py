from __future__ import annotations
import base64
import ctypes
import ctypes.wintypes
from typing import Optional


class CryptoError(Exception):
    pass


class DpapiCrypto:
    """Encriptación basada en Windows DPAPI (Data Protection API).

    Ventajas:
    - Sin dependencias externas (usa crypt32.dll nativa)
    - Clave ligada al usuario/máquina Windows (no se almacena en disco)
    - Los datos solo son descifrables por el mismo usuario en la misma máquina
    """

    CRYPTPROTECT_UI_FORBIDDEN = 0x1

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [
            ("cbData", ctypes.wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_byte)),
        ]

    def __init__(self, entropy: Optional[bytes] = None):
        self._entropy = entropy or b"SAPDocumentAutomation::v1"

    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            return ""
        data = plaintext.encode("utf-8")
        blob_in = self._make_blob(data)
        blob_out = self.DATA_BLOB()
        entropy_blob = self._make_blob(self._entropy)

        ok = ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(blob_in),
            None,
            ctypes.byref(entropy_blob),
            None,
            None,
            self.CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(blob_out),
        )
        if not ok:
            raise CryptoError(f"CryptProtectData falló: {ctypes.GetLastError()}")
        try:
            raw = ctypes.string_at(blob_out.pbData, blob_out.cbData)
            return base64.b64encode(raw).decode("ascii")
        finally:
            ctypes.windll.kernel32.LocalFree(blob_out.pbData)

    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext:
            return ""
        try:
            raw = base64.b64decode(ciphertext.encode("ascii"))
        except Exception as exc:
            raise CryptoError("Valor cifrado inválido") from exc

        blob_in = self._make_blob(raw)
        blob_out = self.DATA_BLOB()
        entropy_blob = self._make_blob(self._entropy)

        ok = ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(blob_in),
            None,
            ctypes.byref(entropy_blob),
            None,
            None,
            self.CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(blob_out),
        )
        if not ok:
            raise CryptoError(f"CryptUnprotectData falló: {ctypes.GetLastError()}")
        try:
            return ctypes.string_at(blob_out.pbData, blob_out.cbData).decode("utf-8")
        finally:
            ctypes.windll.kernel32.LocalFree(blob_out.pbData)

    @classmethod
    def _make_blob(cls, data: bytes) -> "DpapiCrypto.DATA_BLOB":
        buffer = ctypes.create_string_buffer(data, len(data))
        return cls.DATA_BLOB(
            cbData=len(data),
            pbData=ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)),
        )

    def is_encrypted_value(self, value: str) -> bool:
        """Heurística: valores cifrados empiezan con prefijo 'enc:'."""
        return value.startswith("enc:")

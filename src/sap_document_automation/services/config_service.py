from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Optional

from ..infrastructure.crypto import DpapiCrypto

APP_DIR_NAME = "SAPDocumentAutomation"

SENSITIVE_KEYS = {"password", "passwd", "pwd", "secret", "token"}
ENCRYPTED_PREFIX = "enc:"


class ConfigService:
    """Configuración persistente con cifrado DPAPI para valores sensibles.

    - API legacy UI: get/set/save, properties output_folder/logs_folder
    - API nueva: credenciales SAP cifradas (get_credentials/set_credentials)
    """

    DEFAULTS = {
        "output_folder": "",
        "logs_folder": "",
        "max_retries": 2,
        "overwrite_existing": False,
        "auto_select_session": True,
        "confirm_before_process": True,
        "sap_timeout_seconds": 30,
    }

    def __init__(self, base_dir=None, config_dir=None):
        directory = base_dir if base_dir is not None else config_dir
        if directory is None:
            directory = Path.home() / "AppData" / "Roaming" / APP_DIR_NAME
        self.base_dir = Path(directory)
        self.path = self.base_dir / "settings.json"
        self.data: Dict[str, Any] = dict(self.DEFAULTS)
        self._crypto = DpapiCrypto()
        self._load()

    # --- carga/guardado ----------------------------------------------------
    # Claves extendidas permitidas además de DEFAULTS (resto se ignoran)
    EXTRA_ALLOWED_KEYS = {"sap_credentials", "last_output_folder"}

    def _load(self):
        if not self.path.exists():
            return
        try:
            saved = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return
        if isinstance(saved, dict):
            for key, value in saved.items():
                if key in self.DEFAULTS or key in self.EXTRA_ALLOWED_KEYS:
                    self.data[key] = value

    def save(self):
        self.base_dir.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    # --- acceso genérico -----------------------------------------------------
    def get(self, key, default: Any = None):
        value = self.data.get(key, self.DEFAULTS.get(key))
        if default is None and key in self.DEFAULTS:
            return value
        return self.data.get(key, default)

    def set(self, key, value):
        if isinstance(value, str) and key in SENSITIVE_KEYS:
            value = ENCRYPTED_PREFIX + self._crypto.encrypt(value)
        self.data[key] = value

    def delete(self, key: str) -> None:
        self.data.pop(key, None)
        self.save()

    # --- propiedades legacy -----------------------------------------------
    @property
    def output_folder(self) -> Path:
        folder = self.get("output_folder")
        if folder:
            return Path(folder)
        return Path.home() / "Documents" / "SAP Documentos"

    @property
    def logs_folder(self) -> Path:
        folder = self.get("logs_folder")
        if folder:
            return Path(folder)
        return self.output_folder / "Logs"

    # --- credenciales SAP --------------------------------------------------
    def get_credentials(self) -> Dict[str, str]:
        creds = self.data.get("sap_credentials", {})
        result: Dict[str, str] = {}
        if isinstance(creds, dict):
            for k, v in creds.items():
                if isinstance(v, str) and v.startswith(ENCRYPTED_PREFIX):
                    try:
                        result[k] = self._crypto.decrypt(v[len(ENCRYPTED_PREFIX):])
                    except Exception:
                        result[k] = ""
                else:
                    result[k] = v
        return result

    def set_credentials(self, user: str = "", password: str = "", client: str = "") -> None:
        payload: Dict[str, str] = {"user": user, "client": client}
        if password:
            payload["password"] = ENCRYPTED_PREFIX + self._crypto.encrypt(password)
        self.data["sap_credentials"] = payload
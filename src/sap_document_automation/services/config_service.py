from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Optional

from ..infrastructure.crypto import DpapiCrypto

SENSITIVE_KEYS = {"password", "passwd", "pwd", "secret", "token"}
ENCRYPTED_PREFIX = "enc:"


class ConfigService:
    """Gestión de configuración con cifrado DPAPI para valores sensibles.

    - Valores sensibles se guardan como "enc:<base64 dpapi>"
    - Config de usuario en %APPDATA%/SapDocumentAutomation/config.json
    """

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            base = Path.home() / "AppData" / "Roaming" / "SapDocumentAutomation"
        else:
            base = Path(config_dir)
        self._config_dir = base
        self._config_file = base / "config.json"
        self._crypto = DpapiCrypto()
        self._data: Dict[str, Any] = {}
        self.load()

    @property
    def config_file(self) -> Path:
        return self._config_file

    def load(self) -> Dict[str, Any]:
        if self._config_file.exists():
            try:
                self._data = json.loads(self._config_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._data = {}
        else:
            self._data = {}
        return dict(self._data)

    def save(self) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._config_file.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # --- acceso genérico -------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        if isinstance(value, str) and key in SENSITIVE_KEYS:
            value = ENCRYPTED_PREFIX + self._crypto.encrypt(value)
        self._data[key] = value
        self.save()

    def delete(self, key: str) -> None:
        self._data.pop(key, None)
        self.save()

    # --- credenciales SAP -----------------------------------------------
    def get_credentials(self) -> Dict[str, str]:
        creds = self._data.get("sap_credentials", {})
        result: Dict[str, str] = {}
        for k, v in creds.items():
            if isinstance(v, str) and v.startswith(ENCRYPTED_PREFIX):
                result[k] = self._crypto.decrypt(v[len(ENCRYPTED_PREFIX):])
            else:
                result[k] = v
        return result

    def set_credentials(self, user: str = "", password: str = "", client: str = "") -> None:
        payload: Dict[str, str] = {
            "user": user,
            "client": client,
        }
        if password:
            payload["password"] = ENCRYPTED_PREFIX + self._crypto.encrypt(password)
        self._data["sap_credentials"] = payload
        self.save()

    def get_last_output_folder(self) -> Optional[str]:
        return self._data.get("last_output_folder")

    def set_last_output_folder(self, folder: str) -> None:
        self.set("last_output_folder", folder)

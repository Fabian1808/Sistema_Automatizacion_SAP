import json
from pathlib import Path

APP_DIR_NAME = "SAPDocumentAutomation"


class ConfigService:
    DEFAULTS = {
        "output_folder": "",
        "logs_folder": "",
        "max_retries": 2,
        "overwrite_existing": False,
        "auto_select_session": True,
        "confirm_before_process": True,
        "sap_timeout_seconds": 30,
    }

    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = Path.home() / "AppData" / "Roaming" / APP_DIR_NAME
        self.base_dir = Path(base_dir)
        self.path = self.base_dir / "settings.json"
        self.data = dict(self.DEFAULTS)
        self._load()

    def _load(self):
        if not self.path.exists():
            return
        try:
            saved = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return
        for key, value in saved.items():
            if key in self.DEFAULTS:
                self.data[key] = value

    def get(self, key):
        return self.data.get(key, self.DEFAULTS.get(key))

    def set(self, key, value):
        self.data[key] = value

    def save(self):
        self.base_dir.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    @property
    def output_folder(self):
        folder = self.get("output_folder")
        if folder:
            return Path(folder)
        return Path.home() / "Documents" / "SAP Documentos"

    @property
    def logs_folder(self):
        folder = self.get("logs_folder")
        if folder:
            return Path(folder)
        return self.output_folder / "Logs"
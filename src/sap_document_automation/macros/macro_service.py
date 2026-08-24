import json
from pathlib import Path

from .macro_model import Macro

MACROS_DIR_NAME = "macros"
APP_DIR_NAME = "SAPDocumentAutomation"


class MacroService:
    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = (
                Path.home() / "AppData" / "Roaming" / APP_DIR_NAME / MACROS_DIR_NAME
            )
        self.folder = Path(base_dir)
        self.folder.mkdir(parents=True, exist_ok=True)

    def list_macros(self):
        return sorted(path.stem for path in self.folder.glob("*.json"))

    def _path(self, name):
        return self.folder / f"{name}.json"

    def load(self, name):
        data = json.loads(self._path(name).read_text(encoding="utf-8"))
        return Macro.from_dict(data)

    def save(self, macro):
        path = self._path(macro.name)
        path.write_text(
            json.dumps(macro.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def delete(self, name):
        path = self._path(name)
        if path.exists():
            path.unlink()
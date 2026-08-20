import datetime
from pathlib import Path


class LogService:
    def __init__(self, folder):
        self.folder = Path(folder)

    def _ensure_folder(self):
        self.folder.mkdir(parents=True, exist_ok=True)

    def _daily_file(self):
        return self.folder / f"{datetime.date.today().isoformat()}.log"

    def write(self, document, action, status, error=None):
        self._ensure_folder()
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{stamp} | {document} | {action} | {status}"
        if error:
            line += f" | {error}"
        with self._daily_file().open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
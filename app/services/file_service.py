import datetime
from pathlib import Path

MESES = [
    "01-Enero",
    "02-Febrero",
    "03-Marzo",
    "04-Abril",
    "05-Mayo",
    "06-Junio",
    "07-Julio",
    "08-Agosto",
    "09-Septiembre",
    "10-Octubre",
    "11-Noviembre",
    "12-Diciembre",
]


class FileService:
    def __init__(self, base_folder, overwrite=False):
        self.base_folder = Path(base_folder)
        self.overwrite = overwrite

    def target_path(self, doc_type, doc_id, extension=".pdf"):
        now = datetime.date.today()
        folder = self.base_folder / doc_type / str(now.year) / MESES[now.month - 1]
        return folder / f"{doc_id}{extension}"

    def resolve_path(self, doc_type, doc_id, extension=".pdf"):
        path = self.target_path(doc_type, doc_id, extension)
        if self.overwrite or not path.exists():
            return path
        counter = 1
        candidate = path.with_name(f"{path.stem}_copia{counter}{path.suffix}")
        while candidate.exists():
            counter += 1
            candidate = path.with_name(f"{path.stem}_copia{counter}{path.suffix}")
        return candidate
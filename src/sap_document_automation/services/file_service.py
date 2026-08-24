from __future__ import annotations

import datetime
from pathlib import Path
from typing import Optional

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

# Alias en inglés usado por configuración global
MONTH_NAMES = MESES


class FileService:
    """Servicio de archivos: resuelve rutas de salida y valida PDFs.

    - API de instancia (legacy UI/worker): target_path / resolve_path
    - API estática (nueva): unique_path / is_valid_pdf / build_output_path
    """

    def __init__(self, base_folder, overwrite=False):
        self.base_folder = Path(base_folder)
        self.overwrite = overwrite

    # --- API instancia ---------------------------------------------------
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

    # --- API estática ------------------------------------------------------
    @staticmethod
    def build_output_path(
        base_folder: Path,
        doc_type: str,
        year: str,
        month: int,
        filename: str,
    ) -> Path:
        month_name = MESES[month - 1] if 1 <= month <= 12 else f"{month:02d}"
        folder = Path(base_folder) / doc_type / str(year) / month_name
        folder.mkdir(parents=True, exist_ok=True)
        return folder / filename

    @staticmethod
    def is_valid_pdf(path: Path, min_size: int = 100) -> bool:
        if not Path(path).exists() or Path(path).stat().st_size < min_size:
            return False
        try:
            with Path(path).open("rb") as f:
                return f.read(5) == b"%PDF-"
        except OSError:
            return False

    @staticmethod
    def unique_path(path: Path) -> Path:
        """Si el archivo existe añade _1, _2... (nunca sobrescribe)."""
        path = Path(path)
        if not path.exists():
            return path
        stem, suffix = path.stem, path.suffix
        counter = 1
        while True:
            candidate = path.with_name(f"{stem}_{counter}{suffix}")
            if not candidate.exists():
                return candidate
            counter += 1

    @staticmethod
    def safe_delete(path: Path) -> bool:
        try:
            path = Path(path)
            if path.is_file():
                path.unlink()
                return True
            return False
        except OSError:
            return False

    @staticmethod
    def ensure_dir(path: Path) -> Path:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def copy_to(source: Path, target_dir: Path) -> Optional[Path]:
        import shutil

        try:
            FileService.ensure_dir(target_dir)
            target = Path(target_dir) / Path(source).name
            shutil.copy2(source, target)
            return target
        except OSError:
            return None

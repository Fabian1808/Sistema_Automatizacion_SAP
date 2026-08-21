from __future__ import annotations
import shutil
from pathlib import Path
from typing import Optional


MONTH_NAMES = [
    "01-Enero", "02-Febrero", "03-Marzo", "04-Abril",
    "05-Mayo", "06-Junio", "07-Julio", "08-Agosto",
    "09-Septiembre", "10-Octubre", "11-Noviembre", "12-Diciembre",
]


class FileService:
    """Operaciones de archivos: rutas de salida, validación PDF, limpieza."""

    @staticmethod
    def build_output_path(
        base_folder: Path,
        doc_type: str,
        year: str,
        month: int,
        filename: str,
    ) -> Path:
        month_name = MONTH_NAMES[month - 1] if 1 <= month <= 12 else f"{month:02d}"
        folder = base_folder / doc_type / year / month_name
        folder.mkdir(parents=True, exist_ok=True)
        return folder / filename

    @staticmethod
    def is_valid_pdf(path: Path, min_size: int = 100) -> bool:
        if not path.exists() or path.stat().st_size < min_size:
            return False
        try:
            with path.open("rb") as f:
                return f.read(5) == b"%PDF-"
        except OSError:
            return False

    @staticmethod
    def unique_path(path: Path) -> Path:
        """Si el archivo existe, añade sufijo _1, _2... (nunca sobrescribe)."""
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
        try:
            FileService.ensure_dir(target_dir)
            target = target_dir / source.name
            shutil.copy2(source, target)
            return target
        except OSError:
            return None

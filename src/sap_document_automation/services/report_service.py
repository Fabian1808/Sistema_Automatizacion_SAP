from __future__ import annotations

import csv
import datetime
from pathlib import Path
from typing import List

from openpyxl import Workbook

from ..core.models import BatchSummary


class ReportService:
    """Exporta resultados de lote: XLSX (API legacy UI) y CSV (nueva API)."""

    HEADERS = ["Documento", "Fecha", "Estado", "Archivo", "Error", "Tiempo (s)"]

    # --- API legacy (UI run_panel) ----------------------------------------
    def export(self, results, report_name, folder, filename=None):
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        today = datetime.date.today().isoformat()
        path = folder / (filename or f"resultado_{report_name}_{today}.xlsx")
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Resultados"
        sheet.append(self.HEADERS)
        for result in results:
            sheet.append(
                [
                    result.document_id,
                    today,
                    "OK" if result.ok else "ERROR",
                    result.file_path,
                    result.error,
                    round(result.duration, 1),
                ]
            )
        workbook.save(path)
        return path

    # --- API nueva ---------------------------------------------------------
    def export_csv(self, summary: BatchSummary, output_path: Path) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with output_path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["documento", "resultado", "archivo_pdf", "duracion_segundos", "error", "timestamp"])
            for r in summary.results:
                writer.writerow([
                    r.document_id,
                    "OK" if r.ok else "ERROR",
                    r.file_path,
                    f"{r.duration:.1f}",
                    r.error,
                    timestamp,
                ])
        return output_path

    def build_report_name(self, base_folder: Path, doc_type: str = "HES") -> Path:
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return Path(base_folder) / f"reporte_{doc_type.lower()}_{stamp}.csv"

    def summary_lines(self, summary: BatchSummary) -> List[str]:
        lines = [
            f"Total: {summary.total}",
            f"OK: {summary.success_count}",
            f"Errores: {summary.error_count}",
            f"Duplicados: {summary.duplicate_count}",
        ]
        if summary.duration_seconds > 0:
            lines.append(f"Duración: {summary.duration_seconds:.0f}s")
        return lines

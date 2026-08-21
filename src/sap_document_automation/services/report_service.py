from __future__ import annotations
import csv
from datetime import datetime
from pathlib import Path
from typing import List

from ..core.models import ProcessResult, BatchSummary


class ReportService:
    """Exporta resultados de lote a CSV (abrible en Excel)."""

    HEADERS = [
        "documento", "resultado", "archivo_pdf",
        "duracion_segundos", "error", "timestamp",
    ]

    def export_csv(self, summary: BatchSummary, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with output_path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(self.HEADERS)
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
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return base_folder / f"reporte_{doc_type.lower()}_{stamp}.csv"

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

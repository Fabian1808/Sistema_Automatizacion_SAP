import datetime
from pathlib import Path

from openpyxl import Workbook


class ReportService:
    def export(self, results, report_name, folder, filename=None):
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        today = datetime.date.today().isoformat()
        path = folder / (filename or f"resultado_{report_name}_{today}.xlsx")
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Resultados"
        sheet.append(["Documento", "Fecha", "Estado", "Archivo", "Error", "Tiempo (s)"])
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
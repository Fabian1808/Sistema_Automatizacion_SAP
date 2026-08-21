from __future__ import annotations
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sap_document_automation.core.models import BatchSummary, ProcessResult  # noqa: E402
from sap_document_automation.services.update_service import UpdateService, UpdateInfo  # noqa: E402
from sap_document_automation.services.report_service import ReportService  # noqa: E402


class TestVersionComparison:
    def test_newer_versions(self):
        assert UpdateService._is_newer("1.1.0", "1.0.0") is True
        assert UpdateService._is_newer("2.0.0", "1.9.9") is True
        assert UpdateService._is_newer("1.0.0", "1.0.0") is False
        assert UpdateService._is_newer("1.0.0", "1.0.1") is False

    def test_parse_with_prefixes(self):
        assert UpdateService._is_newer("v1.2.0", "1.1.0") is True
        assert UpdateService._is_newer("V2.0", "1.99.0") is True

    def test_garbage_is_not_newer(self):
        assert UpdateService._is_newer("abc", "1.0.0") is False


class TestReportService:
    def _make_summary(self):
        results = [
            ProcessResult(document_id="HES_1001", ok=True, file_path="C:/x/1001.pdf", duration=3.2),
            ProcessResult(document_id="HES_1002", ok=False, error="No encontrado", duration=1.1),
        ]
        summary = BatchSummary(
            batch_id="B-001",
            total=2,
            counts={"SUCCESS": 1, "FAILED": 1},
            results=results,
            duration_seconds=4.5,
        )
        return summary

    def test_export_csv(self, tmp_path):
        svc = ReportService()
        out = tmp_path / "reporte.csv"
        result = svc.export_csv(self._make_summary(), out)
        assert result == out
        content = out.read_text(encoding="utf-8-sig")
        assert "documento;resultado;archivo_pdf" in content
        assert "HES_1001;OK" in content
        assert "HES_1002;ERROR" in content
        assert "No encontrado" in content

    def test_summary_lines(self):
        svc = ReportService()
        lines = svc.summary_lines(self._make_summary())
        assert any("Total: 2" in ln for ln in lines)
        assert any("OK: 1" in ln for ln in lines)
        assert any("Errores: 1" in ln for ln in lines)

    def test_report_name_format(self, tmp_path):
        svc = ReportService()
        path = svc.build_report_name(tmp_path)
        assert path.name.startswith("reporte_hes_")
        assert path.suffix == ".csv"


class TestUpdateInfo:
    def test_no_update_dataclass(self):
        info = UpdateInfo(available=False)
        assert info.available is False
        assert info.latest_version == ""

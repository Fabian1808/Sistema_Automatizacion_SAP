from __future__ import annotations
import json
import urllib.request
import urllib.error
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..core import __version__


@dataclass
class UpdateInfo:
    available: bool
    latest_version: str = ""
    download_url: str = ""
    release_notes: str = ""


class UpdateService:
    """Comprueba actualizaciones contra GitHub Releases.

    - No instala automáticamente: informa y devuelve URL de descarga
    - El instalador (Inno Setup) se encarga de la instalación real
    """

    def __init__(
        self,
        repo: str = "Fabian1808/Sistema_Automatizacion_SAP",
        current_version: Optional[str] = None,
        timeout: float = 10.0,
    ):
        self.repo = repo
        self.current_version = current_version or __version__
        self.timeout = timeout

    @property
    def _api_url(self) -> str:
        return f"https://api.github.com/repos/{self.repo}/releases/latest"

    def check_for_update(self) -> UpdateInfo:
        try:
            data = self._fetch_latest_release()
        except Exception:
            # Sin conexión o rate-limit: no es un error para el usuario
            return UpdateInfo(available=False)

        tag = str(data.get("tag_name", "")).lstrip("vV")
        if not tag:
            return UpdateInfo(available=False)

        if self._is_newer(tag, self.current_version):
            assets = data.get("assets", [])
            download_url = ""
            for asset in assets:
                name = asset.get("name", "").lower()
                if name.endswith(".exe"):
                    download_url = asset.get("browser_download_url", "")
                    break
            return UpdateInfo(
                available=True,
                latest_version=tag,
                download_url=download_url,
                release_notes=data.get("body", "") or "",
            )
        return UpdateInfo(available=False)

    def _fetch_latest_release(self) -> dict:
        req = urllib.request.Request(
            self._api_url,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "SapDocumentAutomation"},
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    @staticmethod
    def _is_newer(candidate: str, current: str) -> bool:
        def parse(v: str):
            parts = []
            for chunk in v.split("."):
                digits = "".join(c for c in chunk if c.isdigit())
                parts.append(int(digits) if digits else 0)
            while len(parts) < 3:
                parts.append(0)
            return tuple(parts[:3])

        try:
            return parse(candidate) > parse(current)
        except Exception:
            return False

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def _default_config_path() -> Path:
    """Resuelve sap_selectors.yaml en dev, bundle PyInstaller e instalado."""
    name = "sap_selectors.yaml"
    candidates: list = []

    base = getattr(sys, "_MEIPASS", None)  # raíz del bundle PyInstaller
    if base:
        b = Path(base)
        candidates += [b / "sap_selectors" / name, b / "config" / name]

    here = Path(__file__).resolve()
    candidates += [
        here.parents[3] / "config" / name,
        here.parents[2] / "config" / name,
    ]

    try:
        exe_dir = Path(sys.executable).resolve().parent
        candidates += [exe_dir / "config" / name, exe_dir / "sap_selectors" / name]
    except Exception:
        pass

    for c in candidates:
        if c.is_file():
            return c
    return candidates[-1]


class SapConfigLoader:
    """Cargador de configuración SAP desde YAML con cache."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = Path(config_path) if config_path else _default_config_path()
        self._config: Optional[Dict] = None

    def load(self) -> Dict[str, Any]:
        if self._config is None:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Config SAP no encontrada: {self.config_path}")
            with self.config_path.open("r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
        return self._config

    def reload(self) -> Dict[str, Any]:
        self._config = None
        return self.load()

    def get_module_config(self, module: str) -> Dict[str, Any]:
        config = self.load()
        return config.get(module, {})

    def get_global_config(self) -> Dict[str, Any]:
        config = self.load()
        return config.get("global", {})

    def get_selectors(self, module: str) -> Dict[str, Any]:
        return self.get_module_config(module)

    def get_timeout(self, module: str, key: str = "default") -> float:
        module_config = self.get_module_config(module)
        timeouts = module_config.get("timeouts", {})
        return timeouts.get(key, timeouts.get("default", 30.0))


@lru_cache(maxsize=1)
def get_sap_config() -> "SapConfigLoader":
    """Singleton para acceso global a configuración SAP."""
    return SapConfigLoader()


def get_hes_selectors() -> Dict[str, Any]:
    return get_sap_config().get_selectors("hes")


def get_global_config() -> Dict[str, Any]:
    return get_sap_config().get_global_config()

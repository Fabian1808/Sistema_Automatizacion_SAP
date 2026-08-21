"""Design tokens del sistema visual corporativo.

Paleta:
- Primario:   #FF5500 (naranja corporativo)
- Secundario: #3B3B3B (gris oscuro)
- Superficies claras para formularios y tablas.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DesignTokens:
    # Colores de marca
    PRIMARY: str = "#FF5500"
    PRIMARY_HOVER: str = "#FF6A26"
    PRIMARY_PRESSED: str = "#D94800"
    SECONDARY: str = "#3B3B3B"
    SECONDARY_LIGHT: str = "#575757"

    # Estados
    SUCCESS: str = "#2E7D32"
    WARNING: str = "#F9A825"
    DANGER: str = "#C62828"
    INFO: str = "#1565C0"

    # Superficies
    BG: str = "#F4F5F7"
    SURFACE: str = "#FFFFFF"
    BORDER: str = "#DDDDDD"

    # Texto
    TEXT: str = "#212121"
    TEXT_MUTED: str = "#6E6E6E"
    TEXT_ON_PRIMARY: str = "#FFFFFF"

    # Tipografía
    FONT_FAMILY: str = "Segoe UI"
    FONT_SIZE_SM: int = 11
    FONT_SIZE_MD: int = 12
    FONT_SIZE_LG: int = 14
    FONT_SIZE_XL: int = 18

    # Espaciado
    SPACE_XS: int = 4
    SPACE_SM: int = 8
    SPACE_MD: int = 16
    SPACE_LG: int = 24

    # Radios
    RADIUS: int = 6
    RADIUS_LG: int = 10


TOKENS = DesignTokens()

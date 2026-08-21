"""Stylesheet QSS generado desde los design tokens."""

from __future__ import annotations

from .tokens import TOKENS as T


def build_stylesheet() -> str:
    return f"""
QWidget {{
    background-color: {T.BG};
    color: {T.TEXT};
    font-family: "{T.FONT_FAMILY}";
    font-size: {T.FONT_SIZE_MD}px;
}}

/* ---------- Botones ---------- */
QPushButton {{
    background-color: {T.SURFACE};
    border: 1px solid {T.BORDER};
    border-radius: {T.RADIUS}px;
    padding: 6px 16px;
}}
QPushButton:hover {{ border-color: {T.PRIMARY}; }}
QPushButton:pressed {{ background-color: {T.BG}; }}
QPushButton:disabled {{ color: {T.TEXT_MUTED}; }}

QPushButton#primaryButton {{
    background-color: {T.PRIMARY};
    color: {T.TEXT_ON_PRIMARY};
    border: none;
    font-weight: bold;
}}
QPushButton#primaryButton:hover {{ background-color: {T.PRIMARY_HOVER}; }}
QPushButton#primaryButton:pressed {{ background-color: {T.PRIMARY_PRESSED}; }}
QPushButton#primaryButton:disabled {{ background-color: #FFB38A; }}

QPushButton#dangerButton {{
    background-color: {T.DANGER};
    color: white;
    border: none;
}}

/* ---------- Inputs ---------- */
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox {{
    background-color: {T.SURFACE};
    border: 1px solid {T.BORDER};
    border-radius: {T.RADIUS}px;
    padding: 5px 8px;
}}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
    border: 2px solid {T.PRIMARY};
    padding: 4px 7px;
}}

/* ---------- Tabla ---------- */
QTableWidget {{
    background-color: {T.SURFACE};
    border: 1px solid {T.BORDER};
    gridline-color: {T.BG};
    selection-background-color: #FFE3D6;
    selection-color: {T.SECONDARY};
}}
QHeaderView::section {{
    background-color: {T.SECONDARY};
    color: white;
    padding: 6px;
    border: none;
    font-weight: bold;
}}

/* ---------- Barras ---------- */
QProgressBar {{
    background-color: {T.SURFACE};
    border: 1px solid {T.BORDER};
    border-radius: {T.RADIUS}px;
    text-align: center;
    height: 18px;
}}
QProgressBar::chunk {{
    background-color: {T.PRIMARY};
    border-radius: {T.RADIUS - 1}px;
}}

QStatusBar {{
    background-color: {T.SECONDARY};
    color: white;
}}

/* ---------- Tabs ---------- */
QTabWidget::pane {{ border: 1px solid {T.BORDER}; }}
QTabBar::tab {{
    background: {T.SURFACE};
    padding: 8px 20px;
    border: 1px solid {T.BORDER};
    border-bottom: none;
}}
QTabBar::tab:selected {{
    background: white;
    color: {T.PRIMARY};
    font-weight: bold;
}}

/* ---------- Scrollbars ---------- */
QScrollBar:vertical {{
    background: {T.BG};
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background: {T.SECONDARY_LIGHT};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
"""

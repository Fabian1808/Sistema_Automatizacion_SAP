"""Catálogo de errores: convierte fallos técnicos en mensajes comprensibles.

Cada entrada entrega: motivo (qué falló), detalle (causa técnica simplificada)
y recomendación (qué hacer). Es extensible: agregar patrones nuevos aquí
sin tocar UI.
"""
from __future__ import annotations

import re
from typing import Dict

# Etapas típicas de procesamiento por documento
STAGES = {
    "conexion": "Conexión con SAP",
    "navegacion": "Navegación en SAP",
    "busqueda": "Búsqueda del documento",
    "impresion": "Impresión / exportación",
    "archivo": "Guardado del archivo",
    "desconocida": "Procesamiento",
}


def detect_stage(error_text: str) -> str:
    text = (error_text or "").lower()
    if "session" in text or "sapgui" in text or "conexi" in text:
        return STAGES["conexion"]
    if "wnd[" in text or "vkey" in text or "tcode" in text:
        return STAGES["navegacion"]
    if "no encontr" in text or "not found" in text or "106" in text or "hes" in text:
        return STAGES["busqueda"]
    if "print" in text or "imprim" in text or "pdf" in text or "spool" in text:
        return STAGES["impresion"]
    if "permiso" in text or "permission" in text or "disco" in text or "disk" in text:
        return STAGES["archivo"]
    return STAGES["desconocida"]


_PATTERNS: list[tuple[str, Dict[str, str]]] = [
    (
        r"sap.*no.*(esta|est[áa]).*(corriendo|abierto|ejecut)|not running|sapgui.*0x",
        {
            "motivo": "SAP no está abierto o no responde.",
            "detalle": "No se pudo comunicar con SAP GUI en esta computadora.",
            "recomendacion": (
                "Abra SAP GUI, inicie sesión y verifique que tenga una sesión activa. "
                "Luego presione 'Actualizar conexión' e intente nuevamente."
            ),
        },
    ),
    (
        r"scripting",
        {
            "motivo": "SAP GUI Scripting está deshabilitado.",
            "detalle": "La automatización requiere el scripting de SAP GUI habilitado.",
            "recomendacion": (
                "En SAP GUI abra Alt+F12 > Opciones > Accessibility & Scripting > "
                "Scripting y marque 'Enable scripting'. Si no tiene permisos, "
                "solicítelo a TI."
            ),
        },
    ),
    (
        r"sesion|session|sin sesiones|no hay sesiones",
        {
            "motivo": "No hay una sesión SAP activa.",
            "detalle": "SAP está abierto pero no se encontró ninguna ventana de trabajo.",
            "recomendacion": (
                "Inicie sesión en SAP y deje abierta una ventana (sesión) antes de ejecutar."
            ),
        },
    ),
    (
        r"time ?out|tiempo.*(agotado|espera)|timeout",
        {
            "motivo": "SAP no respondió durante el tiempo máximo permitido.",
            "detalle": "La operación superó el tiempo de espera configurado.",
            "recomendacion": (
                "Verifique que SAP esté abierto y la sesión activa; si el sistema está "
                "lento espere un momento e intente nuevamente."
            ),
        },
    ),
    (
        r"no encontrada|no encontrado|not found|inexistente|no existe",
        {
            "motivo": "El documento no existe o no es accesible.",
            "detalle": "SAP no encontró el documento con el número indicado.",
            "recomendacion": (
                "Verifique el número del documento. Puede tratarse de un error de tipeo "
                "o de un documento de otro mandante/ambiente."
            ),
        },
    ),
    (
        r"permission denied|acceso denegado|unauthorized|autorizaci",
        {
            "motivo": "Su usuario no tiene autorización para esta operación.",
            "detalle": "SAP rechazó la operación por permisos insuficientes.",
            "recomendacion": "Solicite el acceso correspondiente al administrador de SAP.",
        },
    ),
    (
        r"popup|modal|ventana emergente",
        {
            "motivo": "Apareció una ventana emergente inesperada en SAP.",
            "detalle": "Un diálogo bloqueó la navegación automática.",
            "recomendacion": (
                "Revise la sesión de SAP, cierre los diálogos pendientes e intente "
                "nuevamente. Si persiste, ejecute primero en modo prueba."
            ),
        },
    ),
]


def explain_error(error_text: str) -> Dict[str, str]:
    """Devuelve {estado, motivo, detalle, recomendacion} para mostrar al usuario."""
    text = error_text or ""
    for pattern, info in _PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            result = dict(info)
            break
    else:
        result = {
            "motivo": "No se pudo completar la operación.",
            "detalle": text.strip()[:300] if text.strip() else "Error desconocido.",
            "recomendacion": (
                "Revise el detalle técnico; si no lo comprende, copie este mensaje y "
                "consulte al soporte."
            ),
        }
    result["etapa"] = detect_stage(text)
    return result

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

# ---------------------------------------------------------------------------
# Documentación centralizada y extensible:
# - Para documentar una macro nueva, agregue una entrada a MACRO_HELP.
# - La sección aparecerá automáticamente en el índice de la Ayuda.
# ---------------------------------------------------------------------------

INTRO = """
<h2>¿Qué es este aplicativo?</h2>
<p><b>SAP Document Automation</b> es una herramienta de productividad que
automatiza la descarga masiva de documentos desde SAP (por ejemplo, HES),
evitando repetir manualmente la misma navegación cientos de veces.</p>

<h3>¿Para qué sirve?</h3>
<ul>
<li>Procesar listas completas de documentos en un solo paso.</li>
<li>Guardar cada documento como PDF en una carpeta única.</li>
<li>Detectar duplicados y reintentar errores sin perder avance.</li>
<li>Consultar el historial completo de ejecuciones.</li>
</ul>

<h3>¿Qué procesos automatiza?</h3>
<ul>
<li><b>HES:</b> búsqueda del documento en SAP y descarga/exportación a PDF.</li>
<li><b>Órdenes de Compra:</b> en desarrollo (aparecerá como Disponible cuando
esté lista).</li>
<li><b>Macros VBS:</b> sus propias grabaciones de SAP GUI aplicadas a listas
de documentos.</li>
</ul>

<h3>¿Qué problemas soluciona?</h3>
<p>Elimina el trabajo repetitivo, reduce errores humanos de tipeo/navegación,
acelera horas de trabajo a minutos y deja registro auditable de cada proceso.</p>
"""

MANUAL = """
<h2>Manual de uso paso a paso</h2>
<ol>
<li><b>Abrir el aplicativo.</b> Ejecute SAP Document Automation. La ventana
abre en pocos segundos; el estado de SAP aparece abajo a la derecha.</li>
<li><b>Seleccionar una automatización.</b> Abra <b>Automatizaciones</b> y
presione <b>Ejecutar</b> en la tarjeta correspondiente.</li>
<li><b>Cargar documentos.</b> Pegue los números (uno por línea) o use
<b>Importar Excel / CSV</b>. El contador muestra válidos, duplicados e
inválidos.</li>
<li><b>Ejecutar.</b> Presione el botón naranja de proceso. Confirme la
operación cuando se solicite.</li>
<li><b>Interpretar el progreso.</b> La barra muestra "Procesando HES X de N..."
y los contadores ✅ correctos · ❌ errores · ⏳ pendientes. Puede presionar
<b>Cancelar proceso</b> en cualquier momento: se detiene al terminar el
documento en curso.</li>
<li><b>Revisar resultados.</b> Al finalizar verá un resumen; la tabla indica
el PDF generado por documento. Doble clic sobre un error para ver motivo,
detalle y recomendación.</li>
<li><b>Consultar el historial.</b> Abra <b>Historial</b>: cada ejecución
registra fecha, usuario, cantidades, estado y duración. Doble clic para el
detalle por documento.</li>
<li><b>Ante un error.</b> No repita todo el lote: use <b>Reintentar
errores</b> o <b>Reanudar lote anterior</b>; los ya procesados se saltan.</li>
</ol>
"""

SAP_SCRIPTING = """
<h2>Requisito: SAP GUI Scripting</h2>
<p>La aplicación controla su sesión de SAP ya iniciada; no pide credenciales ni
las almacena.</p>
<ol>
<li>Abra SAP GUI e inicie sesión normalmente.</li>
<li>Verifique el scripting: <b>Alt+F12 → Opciones → Accessibility &amp;
Scripting → Scripting</b> y marque <i>Enable scripting</i>.</li>
<li>Mantenga al menos una sesión abierta mientras usa el aplicativo.</li>
</ol>
"""

MACRO_HELP = {
    "hes": {
        "title": "HES — Descarga masiva",
        "body": """
<h2>HES — Descarga masiva de documentos</h2>
<h3>Qué hace</h3>
<p>Busca cada número de HES en SAP, abre su documento y lo guarda como PDF en
la carpeta de salida configurada.</p>
<h3>Qué información necesita</h3>
<ul>
<li>Números de HES válidos (13 dígitos), uno por línea.</li>
<li>Carpeta de salida definida en Configuración.</li>
</ul>
<h3>Qué archivos acepta</h3>
<ul>
<li>Pegado directo de números en el cuadro de texto.</li>
<li>Excel (.xlsx) o CSV con los números en cualquier celda.</li>
</ul>
<h3>Cómo ejecutarla</h3>
<ol>
<li><b>Automatizaciones → HES → Ejecutar</b>.</li>
<li>Cargue la lista y presione <b>PROCESAR HES</b>.</li>
<li>Opcional: active <b>Modo prueba</b> para verificar la navegación sin
imprimir nada.</li>
</ol>
<h3>Qué resultado genera</h3>
<p>Un PDF por HES exitosa (con nombre basado en el número), tabla de
resultados, reporte exportable a Excel y registro en Historial.</p>
<h3>Errores frecuentes</h3>
<ul>
<li>SAP cerrado o sin sesión → abra SAP GUI e inicie sesión.</li>
<li>Scripting deshabilitado → Alt+F12 → Opciones → Scripting.</li>
<li>HES inexistente → verifique el número (doble clic en el error para el
detalle).</li>
</ul>
"""
    },
    "oc": {
        "title": "Órdenes de Compra (en desarrollo)",
        "body": """
<h2>Órdenes de Compra</h2>
<p>Este módulo descargará masivamente Órdenes de Compra desde SAP. Está en
desarrollo y aparecerá como <b>Disponible</b> en Automatizaciones cuando esté
listo. La información requerida serán los números de Orden de Compra.</p>
"""
    },
    "vbs": {
        "title": "Macros personalizadas (VBS)",
        "body": """
<h2>Macros personalizadas (VBS)</h2>
<h3>Qué hacen</h3>
<p>Reproducen pasos que usted grabó en SAP GUI (scripts VBS) aplicándolos a
una lista de documentos.</p>
<h3>Cómo usarlas</h3>
<ol>
<li>Abra <b>Automatizaciones → Macros personalizadas → Ejecutar</b>.</li>
<li>Cree una macro nueva o <b>Importe VBS...</b> generado por el grabador de
SAP GUI.</li>
<li>Revise los pasos detectados y edítelos si es necesario.</li>
<li>Cargue la lista de documentos y ejecute igual que en HES.</li>
</ol>
"""
    },
}

FAQ = """
<h2>Preguntas frecuentes</h2>
<h3>¿El aplicativo usa mi usuario y contraseña de SAP?</h3>
<p>No. Utiliza la sesión que usted ya tiene abierta; nunca solicita ni guarda
credenciales.</p>
<h3>¿Puedo trabajar en SAP mientras se procesa?</h3>
<p>No se recomienda: la automatización mueve el cursor dentro de la sesión.
Minimice el riesgo usando el Modo prueba para validar primero.</p>
<h3>¿Qué pasa si se corta la luz o se cierra SAP?</h3>
<p>Nada se pierde: cada documento queda registrado. Al reabrir, presione
<b>Reanudar lote anterior</b> y continuará donde quedó.</p>
<h3>¿Cómo reporto un problema?</h3>
<p>Los logs técnicos están en
<i>%APPDATA%\\SAPDocumentAutomation\\logs\\app.log</i>. Copie ese archivo y
envíelo junto con el número del documento afectado.</p>
"""


class HelpView(QWidget):
    """Documentación y guía del aplicativo (solo lectura)."""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        header = QLabel("Ayuda y documentación")
        header.setObjectName("title")
        layout.addWidget(header)

        content = QHBoxLayout()
        content.setSpacing(12)

        self.index_list = QListWidget()
        self.index_list.setFixedWidth(230)
        for label in (
            "Introducción",
            "Manual de uso",
            "SAP GUI Scripting",
            *[info["title"] for info in MACRO_HELP.values()],
            "Preguntas frecuentes",
        ):
            self.index_list.addItem(label)
        self.index_list.currentRowChanged.connect(self._on_select)
        content.addWidget(self.index_list)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(False)
        self.browser.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        content.addWidget(self.browser, 1)

        layout.addLayout(content, 1)
        self._sections = [INTRO, MANUAL, SAP_SCRIPTING] + [
            info["body"] for info in MACRO_HELP.values()
        ] + [FAQ]
        self.index_list.setCurrentRow(0)

    def _on_select(self, row):
        if 0 <= row < len(self._sections):
            self.browser.setHtml(self._sections[row])

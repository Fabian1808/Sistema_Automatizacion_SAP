# SAP Document Automation

Aplicación de escritorio para automatizar procesos repetitivos en SAP GUI
(descarga masiva de documentos) mediante SAP GUI Scripting.

## Estado del proyecto

- **Fase 1 (completa):** estructura del proyecto, conexión y detección de sesiones SAP, configuración, logs, interfaz base con estado de conexión.
- **Fase 2 (en desarrollo):** módulo HES con el flujo real (ML81N + SP01) y sistema de macros que importa scripts VBS grabados en SAP GUI, los convierte en pasos editables y los guarda para ejecutarlos con listas de documentos.
- **Fase 3 (pendiente):** pulir el procesamiento masivo con pruebas reales en SAP.

## Sistema de macros

- Pestaña **Macros** de la aplicación.
- **Importar VBS**: toma un script grabado con *Script Recording and Playback* de SAP GUI y lo convierte en pasos (botones, textos, combos, teclas, transacciones).
- El valor del número de documento se marca automáticamente como `{ID}`.
- Las macros se guardan en `%APPDATA%\SAPDocumentAutomation\macros\`.
- Se ejecutan igual que HES: lista de documentos, modo prueba, progreso, logs, reportes y reintento de errores.
- El paso **"Guardar PDF (diálogo nativo)"** se agrega manualmente al final de la macro (maneja la ventana "Guardar como" de Windows vía SendKeys, la única parte que SAP GUI Scripting no puede automatizar).

## Riesgos conocidos (módulo HES)

- La selección del registro de spool usa la fila 1 (`wnd[0]/usr/chk[1,3]`). Si quedan solicitudes impresas visibles, verificar que la nueva aparezca en la fila 1.
- El número de renglón vacío en la tabla de mensajes se busca dinámicamente (como en el VBS original).
- `CerrarPopupInformacion` y `EsperaLarga` del VBS original no estaban definidas en el archivo entregado; se implementaron en Python.

## Para el desarrollador

### Requisitos

- Windows 10/11
- Python 3.11 o superior
- SAP GUI instalado (para probar la conexión real)

### Instalación

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Ejecución

```powershell
.venv\Scripts\python -m app.main
```

### Pruebas

```powershell
.venv\Scripts\python -m pytest -q
```

### Estructura

```
app/
├── main.py                 # punto de entrada
├── sap/                    # conexión SAP GUI, sesión, esperas, excepciones
├── modules/                # base + registry para nuevos tipos de documento (HES, OC...)
├── services/               # configuración, logs, archivos
├── ui/                     # ventana principal y vistas
└── utils/                  # validación de IDs
tests/                      # pruebas unitarias
build/                      # compilación PyInstaller e instalador (Fase 6)
```

La configuración se guarda en `%APPDATA%\SAPDocumentAutomation\settings.json`.
Los PDFs y logs se guardan por defecto en `Documentos\SAP Documentos`.

### SAP GUI Scripting

La aplicación se conecta a la sesión SAP GUI ya abierta (sin credenciales).
Requiere:

1. SAP GUI > Opciones (Alt+F12) > Accessibility & Scripting > Scripting: activado.
2. Habilitación en el servidor por el equipo SAP (parámetro `sapgui/user_scripting` y autorización de scripting).

## Para el usuario final

1. Abra SAP GUI e inicie sesión normalmente.
2. Abra esta aplicación.
3. Verifique en la barra inferior el estado "SAP CONECTADO" (si no, presione "Actualizar conexión").
4. En la pestaña HES pegue los números (uno por línea) o impórtelos desde Excel/CSV.
5. Presione PROCESAR HES y siga las indicaciones.
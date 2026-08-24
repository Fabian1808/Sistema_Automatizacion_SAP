# SAP Document Automation v1.0.3

Primera versiÃ³n estable del sistema de automatizaciÃ³n de descarga masiva de documentos SAP.

## Novedades

### MÃ³dulo HES (ML81N)
- Descarga masiva de PDFs de Hojas de Entrada de Servicios
- Flujo completo: bÃºsqueda â†’ mensajes NEU â†’ spool SP01 â†’ PDF
- Modo dry-run para validar el flujo sin descargar
- Idempotencia con SQLite: reanudar lotes interrumpidos

### Sistema de macros
- ImportaciÃ³n de macros VBS grabadas en SAP GUI
- Editor visual de pasos con soporte de placeholder `{ID}`

### Seguridad
- Credenciales cifradas con Windows DPAPI (nunca en texto plano)
- DiÃ¡logo "Guardar como" controlado por Win32 API (sin SendKeys)

### DistribuciÃ³n
- Instalador Windows (Inno Setup, espaÃ±ol) con auto-actualizaciÃ³n vÃ­a GitHub Releases
- CI: ruff + pytest en Python 3.11/3.12/3.13

## Requisitos
- Windows 10/11
- SAP GUI con Scripting habilitado (cliente y servidor)

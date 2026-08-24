# SAP Document Automation v1.0.0

Primera versión estable del sistema de automatización de descarga masiva de documentos SAP.

## Novedades

### Módulo HES (ML81N)
- Descarga masiva de PDFs de Hojas de Entrada de Servicios
- Flujo completo: búsqueda → mensajes NEU → spool SP01 → PDF
- Modo dry-run para validar el flujo sin descargar
- Idempotencia con SQLite: reanudar lotes interrumpidos

### Sistema de macros
- Importación de macros VBS grabadas en SAP GUI
- Editor visual de pasos con soporte de placeholder `{ID}`

### Seguridad
- Credenciales cifradas con Windows DPAPI (nunca en texto plano)
- Diálogo "Guardar como" controlado por Win32 API (sin SendKeys)

### Distribución
- Instalador Windows (Inno Setup, español) con auto-actualización vía GitHub Releases
- CI: ruff + pytest en Python 3.11/3.12/3.13

## Requisitos
- Windows 10/11
- SAP GUI con Scripting habilitado (cliente y servidor)

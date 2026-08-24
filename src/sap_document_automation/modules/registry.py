class ModuleRegistry:
    """Registro modular de automatizaciones.

    Cada módulo se registra con metadatos descriptivos; la UI de Macros
    construye su catálogo dinámicamente desde aquí, sin hardcodear nada.
    """

    def __init__(self):
        self._modules = {}
        self._meta = {}

    def register(self, module, description="", accepted_documents="", available=True):
        self._modules[module.module_id] = module
        self._meta[module.module_id] = {
            "id": module.module_id,
            "name": getattr(module, "module_name", module.module_id),
            "description": description,
            "accepted_documents": accepted_documents,
            "available": bool(available),
        }

    def get(self, module_id):
        return self._modules.get(module_id)

    def all(self):
        return list(self._modules.values())

    def metadata(self):
        return [dict(v) for v in self._meta.values()]


class _UnavailableModule:
    """Marcador para automatizaciones planificadas pero aún no implementadas."""

    def __init__(self, module_id, module_name):
        self.module_id = module_id
        self.module_name = module_name


def build_default_registry():
    from sap_document_automation.modules.hes.hes_processor import HesModule

    registry = ModuleRegistry()
    registry.register(
        HesModule(),
        description=(
            "Descarga masiva de documentos HES desde SAP y guardado automático "
            "como PDF en la carpeta configurada."
        ),
        accepted_documents="Números de HES (uno por línea, Excel o CSV)",
        available=True,
    )
    registry.register(
        _UnavailableModule("oc", "Órdenes de Compra"),
        description=(
            "Descarga masiva de Órdenes de Compra desde SAP (módulo en desarrollo)."
        ),
        accepted_documents="Números de Orden de Compra",
        available=False,
    )
    return registry

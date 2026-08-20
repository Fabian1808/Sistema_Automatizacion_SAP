class ModuleRegistry:
    def __init__(self):
        self._modules = {}

    def register(self, module):
        self._modules[module.module_id] = module

    def get(self, module_id):
        return self._modules.get(module_id)

    def all(self):
        return list(self._modules.values())


def build_default_registry():
    from app.modules.hes.hes_processor import HesModule

    registry = ModuleRegistry()
    registry.register(HesModule())
    return registry
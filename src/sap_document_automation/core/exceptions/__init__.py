from __future__ import annotations


class SapAutomationError(Exception):
    """Excepción base del sistema."""
    user_message: str = "Ocurrió un error en la automatización SAP."

    def __init__(self, detail: str = None, user_message: str = None):
        self.detail = detail
        self._user_message = user_message or self.user_message
        super().__init__(detail or self.user_message)

    def __str__(self):
        if self.detail:
            return f"{self._user_message} Detalle: {self.detail}"
        return self._user_message


class SapNotRunningError(SapAutomationError):
    user_message = "SAP GUI no está abierto. Abra SAP GUI, inicie sesión y vuelva a intentar."


class SapScriptingDisabledError(SapAutomationError):
    user_message = (
        "SAP GUI Scripting está deshabilitado. Active Scripting en SAP GUI "
        "(Alt+F12 > Opciones > Accessibility & Scripting > Scripting) y verifique "
        "que el administrador SAP haya habilitado el scripting en el servidor."
    )


class SapNoSessionError(SapAutomationError):
    user_message = "No se encontró ninguna sesión SAP activa."


class SapSessionLostError(SapAutomationError):
    user_message = (
        "La sesión SAP se perdió durante el proceso. Verifique su conexión y vuelva a intentar."
    )


class SapElementNotFoundError(SapAutomationError):
    user_message = "No se pudo encontrar un elemento de la pantalla SAP dentro del tiempo esperado."

    def __init__(self, path: str, timeout: float, detail: str = None):
        self.path = path
        self.timeout = timeout
        super().__init__(detail, f"Elemento no encontrado: {path} (timeout: {timeout}s)")


class SapPopupError(SapAutomationError):
    user_message = "SAP mostró una ventana emergente inesperada durante el proceso."


class ConfigurationError(SapAutomationError):
    user_message = "Error de configuración de la aplicación."


class ValidationError(SapAutomationError):
    user_message = "Error de validación de datos."


class UpdateError(SapAutomationError):
    user_message = "Error durante el proceso de actualización."


class SecurityError(SapAutomationError):
    user_message = "Error de seguridad. La operación no está permitida."
class SapError(Exception):
    user_message = "Ocurrió un error al interactuar con SAP."

    def __init__(self, detail=None):
        self.detail = detail
        super().__init__(detail or self.user_message)

    def __str__(self):
        if not self.detail:
            return self.user_message
        return f"{self.user_message} Detalle: {self.detail}"


class SapNotRunningError(SapError):
    user_message = (
        "SAP GUI no está abierto. Abra SAP GUI, inicie sesión y vuelva a intentar."
    )


class SapScriptingDisabledError(SapError):
    user_message = (
        "SAP GUI Scripting está deshabilitado. Active Scripting en SAP GUI "
        "(Alt+F12 > Opciones > Accessibility & Scripting > Scripting) y verifique "
        "que el administrador SAP haya habilitado el scripting en el servidor."
    )


class SapNoSessionError(SapError):
    user_message = "No se encontró ninguna sesión SAP activa."


class SapSessionLostError(SapError):
    user_message = (
        "La sesión SAP se perdió durante el proceso. Verifique su conexión y vuelva a intentar."
    )


class SapElementNotFoundError(SapError):
    user_message = (
        "No se pudo encontrar un elemento de la pantalla SAP dentro del tiempo esperado."
    )


class SapPopupError(SapError):
    user_message = "SAP mostró una ventana emergente inesperada durante el proceso."
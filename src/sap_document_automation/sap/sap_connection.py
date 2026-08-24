
from .sap_exceptions import (
    SapError,
    SapNoSessionError,
    SapNotRunningError,
    SapScriptingDisabledError,
)


def _error_mentions_scripting(exc):
    text = str(exc)
    return "SCRIPTING" in text.upper()


class SapConnection:
    def __init__(self, timeout=30):
        self.timeout = timeout
        self._engine = None

    def _get_engine(self):
        if self._engine is not None:
            return self._engine
        try:
            import win32com.client
        except ImportError as exc:
            raise SapError("No se pudo cargar la biblioteca pywin32. Reinstale la aplicación.") from exc
        try:
            sapgui = win32com.client.GetObject("SAPGUI")
            engine = sapgui.GetScriptingEngine
        except Exception as exc:
            if _error_mentions_scripting(exc):
                raise SapScriptingDisabledError(str(exc)) from exc
            raise SapNotRunningError(str(exc)) from exc
        self._engine = engine
        return engine

    def is_running(self):
        try:
            self._get_engine()
            return True
        except SapError:
            return False

    def list_connections(self):
        engine = self._get_engine()
        try:
            conns = engine.Children
        except Exception as exc:
            raise SapNoSessionError(str(exc)) from exc
        result = []
        for idx in range(conns.Count):
            conn = conns.Item(idx)
            result.append(
                {
                    "index": idx,
                    "description": self._safe(lambda: conn.Description),
                    "client": self._safe(lambda: conn.Client),
                }
            )
        return result

    def list_sessions(self, conn_index=0):
        engine = self._get_engine()
        conns = engine.Children
        if conns.Count == 0:
            raise SapNoSessionError()
        conn = conns.Item(conn_index)
        sessions = conn.Children
        result = []
        for idx in range(sessions.Count):
            info = self._safe_info(sessions.Item(idx))
            result.append(
                {
                    "index": idx,
                    "description": info.get("description", ""),
                    "user": info.get("user", ""),
                    "client": info.get("client", ""),
                    "transaction": info.get("transaction", ""),
                }
            )
        return result

    def get_session(self, conn_index=0, session_index=0):
        from .sap_session import SapSession

        engine = self._get_engine()
        conns = engine.Children
        if conns.Count == 0:
            raise SapNoSessionError()
        conn = conns.Item(conn_index)
        sessions = conn.Children
        if sessions.Count == 0:
            raise SapNoSessionError()
        return SapSession(sessions.Item(session_index), timeout=self.timeout)

    @staticmethod
    def _safe(getter, default=""):
        try:
            value = getter()
            return value if value is not None else default
        except Exception:
            return default

    def _safe_info(self, session):
        try:
            info = session.Info
        except Exception:
            return {}
        return {
            "description": self._safe(lambda: info.Description),
            "user": self._safe(lambda: info.User),
            "client": self._safe(lambda: info.Client),
            "transaction": self._safe(lambda: info.Transaction),
        }

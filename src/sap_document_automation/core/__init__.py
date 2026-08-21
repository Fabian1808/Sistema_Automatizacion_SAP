from __future__ import annotations

__version__ = "1.0.0"

from .interfaces import (
    ISapClient,
    SapElement,
    SapElementNotFoundError,
    SapSessionLostError,
    SapScriptingDisabledError,
    SapNotRunningError,
    SapWindowState,
)

from .models import (
    DocumentState,
    DocumentRecord,
    BatchInfo,
    ProcessResult,
    BatchSummary,
)

from .exceptions import (
    SapError,
    SapAutomationError,
    SapNotRunningError,
    SapScriptingDisabledError,
    SapNoSessionError,
    SapSessionLostError,
    SapElementNotFoundError,
    SapPopupError,
    ConfigurationError,
    ValidationError,
    UpdateError,
    SecurityError,
)

__all__ = [
    "ISapClient",
    "SapElement",
    "SapElementNotFoundError",
    "SapSessionLostError",
    "SapScriptingDisabledError",
    "SapNotRunningError",
    "SapWindowState",
    "DocumentState",
    "DocumentRecord",
    "BatchInfo",
    "ProcessResult",
    "BatchSummary",
    "SapError",
    "SapAutomationError",
    "SapNotRunningError",
    "SapScriptingDisabledError",
    "SapNoSessionError",
    "SapSessionLostError",
    "SapElementNotFoundError",
    "SapPopupError",
    "ConfigurationError",
    "ValidationError",
    "UpdateError",
    "SecurityError",
]
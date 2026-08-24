from __future__ import annotations

__version__ = "1.0.0"

from .exceptions import (
    ConfigurationError,
    SapAutomationError,
    SapElementNotFoundError,
    SapError,
    SapNoSessionError,
    SapNotRunningError,
    SapPopupError,
    SapScriptingDisabledError,
    SapSessionLostError,
    SecurityError,
    UpdateError,
    ValidationError,
)
from .interfaces import (
    ISapClient,
    SapElement,
    SapWindowState,
)
from .models import (
    BatchInfo,
    BatchSummary,
    DocumentRecord,
    DocumentState,
    ProcessResult,
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

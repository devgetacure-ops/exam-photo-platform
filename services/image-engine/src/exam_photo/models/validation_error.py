from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel


class ErrorSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


class ValidationErrorModel(BaseModel):
    error_code: str
    field_path: str
    message: str
    severity: ErrorSeverity
    context: Optional[Dict[str, Any]] = None
    suggested_resolution: Optional[str] = None

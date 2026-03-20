import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class MCPError(Exception):
    """Base exception class for all MCP-related errors."""

    def __init__(self, message: str, code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class MCPServiceNotFoundError(MCPError):
    """Raised when a requested MCP service is not found."""

    def __init__(self, service_name: str):
        super().__init__(f"MCP Service '{service_name}' not found.", code=404)


class MCPToolNotFoundError(MCPError):
    """Raised when a requested tool is not found in the service."""

    def __init__(self, tool_name: str, service_name: str):
        super().__init__(f"Tool '{tool_name}' not found in service '{service_name}'.", code=404)


class MCPConnectionError(MCPError):
    """Raised when there's an error connecting to an MCP service."""

    def __init__(self, service_name: str, original_error: Optional[Exception] = None):
        details = {"original_error": str(original_error)} if original_error else {}
        super().__init__(
            f"Failed to connect to MCP Service '{service_name}'.", code=503, details=details
        )


def handle_exception(e: Exception, context: str = "") -> Dict[str, Any]:
    """
    Standardized error handling for all services.
    Logs the error and returns a formatted error response.
    """
    if isinstance(e, MCPError):
        logger.error(
            f"MCP Error in {context}: {e.message} (Code: {e.code})", extra={"details": e.details}
        )
        return {
            "status": "error",
            "error": {"message": e.message, "code": e.code, "details": e.details},
        }

    # Generic error
    logger.exception(f"Unhandled Exception in {context}: {str(e)}")
    return {
        "status": "error",
        "error": {
            "message": "Internal Server Error",
            "code": 500,
            "details": {"type": type(e).__name__},
        },
    }

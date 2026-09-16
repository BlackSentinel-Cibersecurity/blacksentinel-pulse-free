from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

logger = structlog.get_logger()


class PulseException(Exception):
    """Base exception for BlackSentinel Pulse."""

    def __init__(self, message: str, status_code: int = 500, detail: Any = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail


class AssetNotFoundException(PulseException):
    def __init__(self, asset_id: str):
        super().__init__(f"Asset not found: {asset_id}", status_code=404)


class DiscoveryException(PulseException):
    def __init__(self, message: str, detail: Any = None):
        super().__init__(message, status_code=500, detail=detail)


class IntegrationException(PulseException):
    def __init__(self, provider: str, message: str):
        super().__init__(
            f"Integration error with {provider}: {message}", status_code=502
        )


class AuthenticationError(PulseException):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, status_code=401)


class AuthorizationError(PulseException):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=403)


class ValidationError(PulseException):
    def __init__(self, message: str, detail: Any = None):
        super().__init__(message, status_code=422, detail=detail)


def register_exception_handlers(app: FastAPI):
    """Register global exception handlers."""

    @app.exception_handler(PulseException)
    async def pulse_exception_handler(request: Request, exc: PulseException):
        logger.error(
            "pulse_exception", message=exc.message, status_code=exc.status_code
        )
        content = {"error": exc.message}
        if exc.detail:
            content["detail"] = exc.detail
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error("unhandled_exception", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal server error"},
        )

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from .logging_config import logger
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """
    Handles errors raised with `raise HTTPException(...)`.
    This provides consistent logging for all anticipated HTTP errors.
    """
    log_details = {
        "url": str(request.url),
        "status_code": exc.status_code,
        "detail": exc.detail
    }
    logger.warning("HTTP exception occurred", extra=log_details) 
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handles errors from Pydantic model validation.
    This logs the specific validation errors and the request body that caused them.
    """
    try:
        body = await request.json()
    except Exception:
        body = "Could not parse request body."

    log_details = {
        "url": str(request.url),
        "errors": exc.errors(),
        "body": body,
    }
    logger.warning("Request validation failed", extra=log_details)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": exc.errors()},
    )
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handles any uncaught exception in the application.
    This is a critical catch-all to prevent the server from crashing.
    """
    log_details = {
        "url": str(request.url),
        "error": str(exc),
    }
    logger.error("An unhandled exception occurred", extra=log_details, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."},
    )
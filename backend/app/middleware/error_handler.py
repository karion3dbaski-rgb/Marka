import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class ApiError(Exception):
    def __init__(self, message: str, code: str, status_code: int) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class AuthenticationError(ApiError):
    def __init__(self, message: str = "Kimlik doğrulama başarısız.") -> None:
        super().__init__(message, "AUTH_ERROR", status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(ApiError):
    def __init__(self, message: str = "Bu işlem için yetkiniz yok.") -> None:
        super().__init__(message, "FORBIDDEN", status.HTTP_403_FORBIDDEN)


class NotFoundError(ApiError):
    def __init__(self, message: str = "Kayıt bulunamadı.") -> None:
        super().__init__(message, "NOT_FOUND", status.HTTP_404_NOT_FOUND)


class ConflictError(ApiError):
    def __init__(self, message: str = "İşlem çakışmaya neden oldu.") -> None:
        super().__init__(message, "CONFLICT", status.HTTP_409_CONFLICT)


class ValidationApiError(ApiError):
    def __init__(self, message: str = "Doğrulama hatası oluştu.") -> None:
        super().__init__(message, "VALIDATION_ERROR", status.HTTP_422_UNPROCESSABLE_ENTITY)


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.message, "code": exc.code})


async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    detail = exc.errors()[0].get("msg", "Geçersiz istek verisi.") if exc.errors() else "Geçersiz istek verisi."
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": detail, "code": "VALIDATION_ERROR"},
    )


async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    default_message = "İstek işlenemedi."
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        code = "AUTH_ERROR"
        default_message = "Kimlik doğrulama başarısız."
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        code = "FORBIDDEN"
        default_message = "Bu işlem için yetkiniz yok."
    elif exc.status_code == status.HTTP_404_NOT_FOUND:
        code = "NOT_FOUND"
        default_message = "Kayıt bulunamadı."
    elif exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
        code = "VALIDATION_ERROR"
        default_message = "Doğrulama hatası oluştu."
    else:
        code = "HTTP_ERROR"
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail or default_message), "code": code})


async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Beklenmeyen sunucu hatası", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Beklenmeyen bir sunucu hatası oluştu.", "code": "INTERNAL_SERVER_ERROR"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

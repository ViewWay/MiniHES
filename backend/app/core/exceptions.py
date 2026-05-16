from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException


class BusinessException(Exception):  # noqa: N818
    def __init__(self, code: int = 400, message: str = "操作失败"):
        self.code = code
        self.message = message


async def business_exception_handler(_request: Request, exc: BusinessException) -> JSONResponse:
    status = _map_code_to_http(exc.code)
    return JSONResponse(
        status_code=status,
        content={"code": exc.code, "message": exc.message, "data": None},
    )


async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for e in exc.errors():
        field = ".".join(str(loc) for loc in e.get("loc", []))
        # Skip 'body' prefix for cleaner field names
        field = field.removeprefix("body.")
        errors.append({"field": field, "message": e.get("msg", "")})
    return JSONResponse(
        status_code=422,
        content={"code": 422, "message": "参数校验失败", "data": {"errors": errors}},
    )


async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": str(exc.detail), "data": None},
    )


async def integrity_error_handler(_request: Request, exc: IntegrityError) -> JSONResponse:
    msg = str(exc.orig) if exc.orig else "数据冲突"
    if "unique" in msg.lower() or "duplicate" in msg.lower():
        return JSONResponse(
            status_code=409,
            content={"code": 409, "message": "数据已存在，请检查唯一字段", "data": None},
        )
    if "foreign key" in msg.lower():
        return JSONResponse(
            status_code=400,
            content={"code": 400, "message": "关联数据不存在", "data": None},
        )
    return JSONResponse(
        status_code=400,
        content={"code": 400, "message": "数据操作失败", "data": None},
    )


async def generic_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误", "data": None},
    )


def register_exception_handlers(app):
    app.add_exception_handler(BusinessException, business_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)


def _map_code_to_http(code: int) -> int:
    if code < 100:
        return 400
    if code < 200:
        return code
    if code < 300:
        return code
    if code < 500:
        return code
    return 500

from typing import Any

from fastapi.responses import JSONResponse


def ok(data: Any = None, message: str = "ok") -> JSONResponse:
    return JSONResponse(content={"code": 200, "message": message, "data": data})


def created(data: Any = None, message: str = "created") -> JSONResponse:
    return JSONResponse(status_code=201, content={"code": 201, "message": message, "data": data})


def fail(code: int = 400, message: str = "操作失败", status: int | None = None) -> JSONResponse:
    http_status = status or code if 100 <= code < 600 else 400
    return JSONResponse(status_code=http_status, content={"code": code, "message": message, "data": None})


def success(data: Any = None, message: str = "ok") -> dict:
    return {"code": 200, "message": message, "data": data}


def error(message: str, code: int = -1) -> dict:
    return {"code": code, "message": message, "data": None}

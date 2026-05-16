from typing import Any

from fastapi.responses import JSONResponse


def ok(data: Any = None, message: str = "ok") -> JSONResponse:
    return JSONResponse(content={"code": 200, "data": data, "message": message})


def created(data: Any = None, message: str = "created") -> JSONResponse:
    return JSONResponse(status_code=201, content={"code": 201, "data": data, "message": message})


def fail(code: int = -1, message: str = "error", status: int = 400) -> JSONResponse:
    return JSONResponse(status_code=status, content={"code": code, "data": None, "message": message})


def success(data: Any = None, message: str = "ok") -> dict:
    return {"code": 0, "data": data, "error": None, "message": message}


def error(message: str, code: int = -1) -> dict:
    return {"code": code, "data": None, "error": message, "message": message}

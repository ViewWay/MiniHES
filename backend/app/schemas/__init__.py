from pydantic import BaseModel


class ResponseBase(BaseModel):
    code: int = 0
    message: str = "ok"
    error: str | None = None


class ResponseSuccess(ResponseBase):
    code: int = 0


class PageResponse(ResponseBase):
    code: int = 0


class PaginationQuery(BaseModel):
    page: int = 1
    page_size: int = 20

from pydantic import BaseModel


class Pagination(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class PageResponse(BaseModel):
    items: list
    pagination: Pagination
    filters: dict = {}


def pagination(page: int, page_size: int, total: int) -> Pagination:
    total_pages = (total + page_size - 1) // page_size if page_size else 0
    return Pagination(page=page, page_size=page_size, total=total, total_pages=total_pages)

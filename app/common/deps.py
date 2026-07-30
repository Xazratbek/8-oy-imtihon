from fastapi import Query

from app.common.schemas import Pagination


def pagination(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)) -> Pagination:
    return Pagination(limit=limit, offset=offset)

from fastapi import APIRouter

from app.schemas.common import ApiModel
from app.schemas.meta import SchemeInfo
from app.services.meta_service import scheme_info

router = APIRouter(tags=["meta"])


class Health(ApiModel):
    status: str


@router.get("/health")
async def health() -> Health:
    return Health(status="ok")


@router.get("/meta/schemes")
async def schemes() -> list[SchemeInfo]:
    return scheme_info()

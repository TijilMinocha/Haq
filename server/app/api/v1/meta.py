from fastapi import APIRouter, Response

from app.api.deps import ContainerDep
from app.schemas.common import ApiModel
from app.schemas.meta import SchemeInfo
from app.services.meta_service import scheme_info

router = APIRouter(tags=["meta"])


class Health(ApiModel):
    status: str


class Readiness(ApiModel):
    status: str
    database: bool
    ocr: bool


@router.get("/health")
async def health() -> Health:
    """Liveness only, so the keep-warm ping never wakes the database."""
    return Health(status="ok")


@router.get("/health/ready", responses={503: {"model": Readiness}})
async def ready(container: ContainerDep, response: Response) -> Readiness:
    database = await container.database_ready()
    ocr = container.extractor.ready() if container.extractor else False
    if not (database and ocr):
        response.status_code = 503
    return Readiness(status="ok" if database and ocr else "degraded", database=database, ocr=ocr)


@router.get("/meta/schemes")
async def schemes() -> list[SchemeInfo]:
    return scheme_info()

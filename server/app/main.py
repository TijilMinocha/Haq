from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import ErrorResponse, install_error_handlers
from app.infra.extractors.base import Extractor
from app.services.container import build_container


def create_app(settings: Settings | None = None, extractor: Extractor | None = None) -> FastAPI:
    settings = settings or get_settings()
    container = build_container(settings, extractor)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        await container.auth_service.seed()
        yield
        await container.close()

    app = FastAPI(
        title="Haq API",
        version="0.1.0",
        lifespan=lifespan,
        responses={"default": {"model": ErrorResponse}},
    )
    app.state.container = container
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
    )
    install_error_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import ErrorResponse, install_error_handlers
from app.core.logging import configure_logging
from app.core.middleware import install_middleware
from app.infra.extractors.base import Extractor
from app.services.container import build_container


def create_app(settings: Settings | None = None, extractor: Extractor | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level, settings.log_json)
    container = build_container(settings, extractor)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        await container.auth_service.seed()
        yield
        await container.close()

    app = FastAPI(
        title="Haq API",
        version="1.0.0",
        # Interactive docs stay on in production: judges and Piyush use them.
        lifespan=lifespan,
        responses={"default": {"model": ErrorResponse}},
    )
    app.state.container = container
    install_middleware(app, settings)
    # Added after the other middleware so it wraps them: even a 429 or 413 carries CORS
    # headers, otherwise the browser hides the error body from the client.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=settings.cors_origin_regex,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition", "X-Request-ID", "Retry-After"],
        max_age=600,
    )
    install_error_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()

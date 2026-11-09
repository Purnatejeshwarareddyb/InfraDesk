"""InfraDesk FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles

from app.api.v1 import health
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()

    app = FastAPI(
        title="InfraDesk API",
        version=settings.app_version,
        description="Offline IT asset management and problem reporting. "
        "Sign in with POST /api/v1/auth/login; the session is kept in an HttpOnly cookie.",
        docs_url=None,  # served below from local files, so no CDN is needed offline
        redoc_url=None,
    )

    # Swagger UI is bundled in app/static/swagger (served under /docs-assets) so that the
    # API documentation page also works without internet access.
    app.mount("/docs-assets", StaticFiles(directory=Path(__file__).parent / "static" / "swagger"), name="docs-assets")

    @app.get("/docs", include_in_schema=False)
    def swagger_docs():
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="InfraDesk API docs",
            swagger_js_url="/docs-assets/swagger-ui-bundle.js",
            swagger_css_url="/docs-assets/swagger-ui.css",
            swagger_favicon_url="/docs-assets/favicon-32x32.png",
        )

    # Narrow CORS: only the configured origins, never a wildcard (cookies are used).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(api_router)
    return app


app = create_app()

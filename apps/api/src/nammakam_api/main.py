"""FastAPI Application Entrypoint.

Instantiates the FastAPI application, mounts presentation routes, configures
request tracing and CORS middleware, and initializes logging.
"""

import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from nammakam_api.presentation.routes.evaluations import router as evaluations_router
from nammakam_api.presentation.routes.health import router as health_router

# Configure basic structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("nammakam.api")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware attaching a unique X-Request-ID header to every request/response."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid4())
        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        response.headers["x-request-id"] = request_id

        # Safe request logging: logs path, status, and duration (no request bodies or PII)
        logger.info(
            "%s %s -> %d (%.1f ms) [request_id=%s]",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )
        return response


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title="Nammakam AI Safety Evaluation API",
        description="Safety evaluation platform for Indian-language banking voice and chat agents.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Mount Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)

    # Mount Presentation Routers
    app.include_router(health_router)
    app.include_router(evaluations_router)

    return app


# Application entrypoint
app = create_app()

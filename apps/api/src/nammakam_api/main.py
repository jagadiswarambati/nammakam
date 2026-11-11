"""FastAPI Application Entrypoint.

Instantiates the FastAPI application, mounts presentation routes, configures
request tracing and CORS middleware, and initializes logging.
"""

import logging
import time
from typing import Any
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from nammakam_api.presentation.routes.evaluations import router as evaluations_router
from nammakam_api.presentation.routes.health import router as health_router

# Configure basic structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("nammakam.api")


class RequestIdMiddleware:
    """Pure ASGI middleware attaching a unique X-Request-ID header to every request/response."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id: str | None = None
        for name, value in scope.get("headers", []):
            if name.lower() == b"x-request-id":
                request_id = value.decode("latin1")
                break

        if not request_id:
            request_id = str(uuid4())

        start_time = time.perf_counter()
        status_code = 200

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
                headers: list[tuple[bytes, bytes]] = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode("latin1")))  # type: ignore[union-attr]
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.info(
                "%s %s -> %d (%.1f ms) [request_id=%s]",
                scope.get("method"),
                scope.get("path"),
                status_code,
                duration_ms,
                request_id,
            )


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

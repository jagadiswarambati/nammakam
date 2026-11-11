"""Health and Readiness Routes.

Provides liveness and readiness probe endpoints for monitoring and runtime validation.
"""

from fastapi import APIRouter, Depends

from nammakam_api.container import get_settings
from nammakam_api.infrastructure.config.settings import Settings
from nammakam_api.presentation.schemas.evaluation import HealthResponse, ReadyResponse

router = APIRouter(tags=["Health"])


@router.get("/healthz", response_model=HealthResponse)
def get_healthz() -> HealthResponse:
    """Liveness probe indicating the HTTP service is running."""
    return HealthResponse(status="ok", service="nammakam-api")


@router.get("/readyz", response_model=ReadyResponse)
def get_readyz(
    app_settings: Settings = Depends(get_settings),
) -> ReadyResponse:
    """Readiness probe indicating service components and feature flags are initialized."""
    return ReadyResponse(
        status="ready",
        service="nammakam-api",
        version="0.1.0",
        gemini_judge_enabled=app_settings.nammakam_enable_gemini_judge,
    )

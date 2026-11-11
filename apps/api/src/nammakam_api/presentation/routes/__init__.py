"""Presentation Routes."""

from nammakam_api.presentation.routes.evaluations import router as evaluations_router
from nammakam_api.presentation.routes.health import router as health_router

__all__ = [
    "evaluations_router",
    "health_router",
]

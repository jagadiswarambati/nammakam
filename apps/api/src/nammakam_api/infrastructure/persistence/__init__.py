"""Persistence Infrastructure Adapters."""

from nammakam_api.infrastructure.persistence.in_memory_evaluation_repository import (
    EvaluationRecord,
    InMemoryEvaluationRepository,
)

__all__ = [
    "EvaluationRecord",
    "InMemoryEvaluationRepository",
]

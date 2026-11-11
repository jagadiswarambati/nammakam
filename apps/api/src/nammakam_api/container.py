"""Dependency Injection Container.

Provides singleton and factory providers for infrastructure adapters, application use cases,
and runtime settings to FastAPI route handlers.
"""

from functools import lru_cache

from nammakam_api.application.use_cases.generate_evidence_pack import (
    GenerateEvidencePackUseCase,
)
from nammakam_api.application.use_cases.run_baseline_suite import RunBaselineSuiteUseCase
from nammakam_api.application.use_cases.run_scenario import EvaluateScenarioUseCase
from nammakam_api.infrastructure.config.settings import Settings, settings
from nammakam_api.infrastructure.persistence.in_memory_evaluation_repository import (
    InMemoryEvaluationRepository,
)

# Global in-memory evaluation repository singleton for MVP
_evaluation_repository = InMemoryEvaluationRepository()


@lru_cache
def get_settings() -> Settings:
    """Returns application configuration settings."""
    return settings


def get_evaluation_repository() -> InMemoryEvaluationRepository:
    """Returns the shared in-memory evaluation repository instance."""
    return _evaluation_repository


def get_evaluate_scenario_use_case() -> EvaluateScenarioUseCase:
    """Factory creating an EvaluateScenarioUseCase instance with configured settings."""
    app_settings = get_settings()
    return EvaluateScenarioUseCase(
        enable_gemini_judge=app_settings.nammakam_enable_gemini_judge
    )


def get_run_baseline_suite_use_case() -> RunBaselineSuiteUseCase:
    """Factory creating a RunBaselineSuiteUseCase instance."""
    evaluate_use_case = get_evaluate_scenario_use_case()
    return RunBaselineSuiteUseCase(evaluate_scenario_use_case=evaluate_use_case)


def get_generate_evidence_pack_use_case() -> GenerateEvidencePackUseCase:
    """Factory creating a GenerateEvidencePackUseCase instance."""
    return GenerateEvidencePackUseCase()

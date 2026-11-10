"""Report Data Transfer Objects.

Transfers evaluation summaries, language metrics, parity gaps, and failure records
between the application use cases and presentation/reporting layers.
"""

from dataclasses import dataclass, field
from typing import Any

from nammakam_api.application.dto.episode_dto import EpisodeResultDTO


@dataclass(frozen=True)
class ParityGapDTO:
    """Disparity gap metrics comparing a regional language to the English baseline."""

    regional_language: str
    refusal_gap: float
    attack_gap: float
    parity_score: float


@dataclass(frozen=True)
class LanguageSummaryDTO:
    """Aggregated evaluation metrics for a specific Indian language."""

    language: str
    total_scenarios: int
    passed: int
    failed: int
    escalated: int
    over_refused: int
    resilience_score: float
    protection_score: float


@dataclass(frozen=True)
class ScenarioFailureDTO:
    """Record of a scenario evaluation that failed safety checks or was over-refused."""

    scenario_id: str
    language: str
    scenario_type: str
    verdict: str
    violations: list[str]


@dataclass(frozen=True)
class BaselineEvaluationSummary:
    """In-memory baseline evaluation summary aggregated across the 16 baseline scenarios."""

    total_scenarios: int
    scenarios_passed: int
    scenarios_failed: int
    scenarios_escalated: int
    scenarios_with_over_refusal: int
    results_by_language: dict[str, LanguageSummaryDTO]
    results_by_scenario_type: dict[str, dict[str, Any]]
    resilience_by_language: dict[str, float]
    protection_by_language: dict[str, float]
    parity_gap_by_language: dict[str, ParityGapDTO]
    failing_scenarios: list[ScenarioFailureDTO]
    overall_resilience: float
    overall_protection: float
    overall_parity: float
    episodes: list[EpisodeResultDTO] = field(default_factory=list)

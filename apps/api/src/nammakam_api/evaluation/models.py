"""Data Models for Gemini Judge Evaluation Harness.

Defines schemas for labeled evaluation cases, case evaluation results,
calibration metrics, failure taxonomies, and aggregate evaluation reports.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field


class FailureCategory(str, Enum):
    """Taxonomy of failure modes for Gemini judge evaluations."""

    MISSED_SCAM = "missed_scam"
    FALSE_POSITIVE = "false_positive"
    WRONG_VERDICT = "wrong_verdict"
    MISSED_INDICATOR = "missed_indicator"
    MISSED_UNSAFE_ACTION = "missed_unsafe_action"
    MISSED_PROTECTION = "missed_protection"
    INCORRECT_HUMAN_REVIEW = "incorrect_human_review"
    WEAK_EXPLANATION = "weak_explanation"
    SCHEMA_VIOLATION = "schema_violation"
    PROMPT_INJECTION_SUCCESS = "prompt_injection_success"
    API_ERROR = "api_error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class EvaluationCaseSchema(BaseModel):
    """Pydantic model validating a labeled test case loaded from disk or fixture."""

    case_id: str = Field(..., description="Unique case identifier, e.g. EVAL-DA-TE-01")
    category: str = Field(..., description="Evaluation category: digital_arrest, authority_impersonation, etc.")
    language: str = Field(..., description="Language code: te, hi, en, hinglish")
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE"] = Field(...)
    description: str = Field(..., description="Summary of the scenario context and goal")
    scenario_type: str = Field(default="adversarial_scam")
    attack_family: str | None = None
    caller_persona: str = Field(...)
    customer_goal: str = Field(...)
    expected_safe_behaviour: list[str] = Field(default_factory=list)
    forbidden_actions: list[str] = Field(default_factory=list)
    dialogue_turns: list[dict[str, Any]] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    deterministic_violations: list[str] = Field(default_factory=list)

    # Expected Ground Truth
    expected_verdict: str = Field(..., description="Primary expected verdict")
    acceptable_verdicts: list[str] = Field(default_factory=list, description="All allowed valid verdicts")
    expected_scam_indicators: list[str] = Field(default_factory=list)
    required_scam_indicators: list[str] = Field(default_factory=list, description="Indicators that must be detected")
    expected_unsafe_actions: list[str] = Field(default_factory=list)
    expected_missing_protections: list[str] = Field(default_factory=list)
    expected_human_review: bool | None = None
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    max_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    acceptable_keywords: list[str] = Field(default_factory=list)
    forbidden_claims: list[str] = Field(default_factory=list)
    safety_invariants: list[str] = Field(default_factory=list)

    # Recorded Gemini response for deterministic offline replay
    recorded_response: dict[str, Any] = Field(..., description="Deterministic recorded Gemini judge response")


@dataclass(frozen=True)
class CaseEvaluationResult:
    """Outcome of evaluating a single case."""

    case_id: str
    category: str
    language: str
    severity: str
    verdict_match: bool
    actual_verdict: str
    expected_verdict: str
    confidence: float
    scam_indicators_found: list[str]
    missed_required_indicators: list[str]
    human_review_match: bool
    actual_human_review: bool
    expected_human_review: bool | None
    safety_invariants_passed: bool
    invariant_failures: list[str]
    passed: bool
    failure_categories: list[FailureCategory]
    explanation_quality_passed: bool
    explanation_issues: list[str]
    latency_ms: float
    token_usage: dict[str, int]
    response_source: Literal["recorded_fixture", "live_api"]
    error_message: str | None = None


@dataclass(frozen=True)
class CalibrationBucket:
    """Calibration stats for a confidence interval."""

    range_label: str
    min_confidence: float
    max_confidence: float
    total_cases: int
    correct_cases: int
    accuracy: float
    false_negatives: int
    false_positives: int


@dataclass(frozen=True)
class CalibrationSummary:
    """Confidence calibration breakdown across intervals."""

    buckets: list[CalibrationBucket]
    high_confidence_error_count: int
    high_confidence_error_cases: list[str]


@dataclass(frozen=True)
class CategoryMetric:
    """Metrics sliced by category."""

    category: str
    total_cases: int
    passed_cases: int
    accuracy: float
    precision: float
    recall: float
    false_negatives: int
    false_positives: int


@dataclass(frozen=True)
class LanguageMetric:
    """Metrics sliced by language."""

    language: str
    total_cases: int
    passed_cases: int
    accuracy: float
    precision: float
    recall: float
    false_negatives: int
    false_positives: int


@dataclass(frozen=True)
class SeverityMetric:
    """Metrics sliced by severity."""

    severity: str
    total_cases: int
    passed_cases: int
    accuracy: float
    false_negatives: int


@dataclass(frozen=True)
class MetricsSummary:
    """Overall and sliced performance metrics."""

    total_cases: int
    passed_cases: int
    failed_cases: int
    pass_rate: float
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    false_negative_rate: float
    false_positive_rate: float
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    categories: list[CategoryMetric]
    languages: list[LanguageMetric]
    severities: list[SeverityMetric]
    calibration: CalibrationSummary
    failure_taxonomy: dict[str, int]
    avg_latency_ms: float
    p95_latency_ms: float
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float


@dataclass(frozen=True)
class EvaluationReport:
    """Top-level evaluation run report."""

    report_id: str
    timestamp: str
    mode: Literal["offline", "live"]
    model_name: str
    prompt_version: str
    summary: MetricsSummary
    case_results: list[CaseEvaluationResult]
    metadata: dict[str, Any] = field(default_factory=dict)


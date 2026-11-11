"""Evaluation Presentation Schemas.

Pydantic schemas validating HTTP requests and serializing responses for evaluation runs,
summaries, episodes, and evidence-pack verification.
"""

from typing import Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Liveness probe response."""

    status: str = "ok"
    service: str = "nammakam-api"


class ReadyResponse(BaseModel):
    """Readiness probe response."""

    status: str = "ready"
    service: str = "nammakam-api"
    version: str = "0.1.0"
    gemini_judge_enabled: bool = False


class BaselineEvaluationRequest(BaseModel):
    """Configuration payload for triggering a baseline evaluation run."""

    customer_authenticated: bool = Field(
        default=True,
        description="Whether simulated caller sessions start pre-authenticated",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional execution tags and contextual metadata",
    )


class LanguageMetricSchema(BaseModel):
    """Performance metrics for an individual evaluation language."""

    language: str
    total_scenarios: int
    passed: int
    failed: int
    escalated: int
    over_refused: int
    resilience_score: float
    protection_score: float


class ParityGapSchema(BaseModel):
    """Disparity gap comparing a regional language to the English baseline."""

    regional_language: str
    refusal_gap: float
    attack_gap: float
    parity_score: float


class ScenarioFailureSchema(BaseModel):
    """Record of a failed or over-refused evaluation scenario."""

    scenario_id: str
    language: str
    scenario_type: str
    verdict: str
    violations: list[str]


class BaselineEvaluationSummarySchema(BaseModel):
    """Aggregated baseline evaluation summary across all 16 scenarios."""

    total_scenarios: int
    scenarios_passed: int
    scenarios_failed: int
    scenarios_escalated: int
    scenarios_with_over_refusal: int
    results_by_language: dict[str, LanguageMetricSchema]
    results_by_scenario_type: dict[str, Any]
    resilience_by_language: dict[str, float]
    protection_by_language: dict[str, float]
    parity_gap_by_language: dict[str, ParityGapSchema]
    failing_scenarios: list[ScenarioFailureSchema]
    overall_resilience: float
    overall_protection: float
    overall_parity: float


class BaselineEvaluationResponse(BaseModel):
    """High-level response returned when a baseline evaluation run completes."""

    evaluation_id: str
    status: str
    created_at: str
    total_scenarios: int
    scenarios_passed: int
    scenarios_failed: int
    overall_resilience: float
    overall_protection: float
    overall_parity: float
    episode_ids: list[str]
    summary_url: str
    evidence_pack_url: str


class EvaluationDetailResponse(BaseModel):
    """Detailed evaluation run status and aggregated summary."""

    evaluation_id: str
    status: str
    created_at: str
    summary: BaselineEvaluationSummarySchema
    episode_ids: list[str]


class ToolInvocationSchema(BaseModel):
    """Record of a mock banking tool invocation."""

    tool_call_id: str
    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any] | None
    is_authorized: bool
    error: str | None
    executed_at: str


class TurnSchema(BaseModel):
    """Individual conversational turn within an episode transcript."""

    turn_index: int
    speaker: str
    text: str
    timestamp: str
    tool_calls: list[ToolInvocationSchema] = Field(default_factory=list)


class JudgmentSchema(BaseModel):
    """Safety evaluation judgment for an episode."""

    judgment_id: str
    verdict: str
    resilience_score: float
    protection_score: float
    violations: list[str]
    reasoning: str
    is_deterministic: bool


class EpisodeDetailResponse(BaseModel):
    """Detailed trace of an individual evaluated episode."""

    episode_id: str
    scenario_id: str
    language: str
    is_adversarial: bool
    verdict: str
    is_safe: bool
    resilience_score: float
    protection_score: float
    violations: list[str]
    disposition: str
    escalated_to_human: bool
    escalation_reason: str | None
    turns: list[TurnSchema]
    tool_calls: list[ToolInvocationSchema]
    judgment: JudgmentSchema


class EvidencePackResponse(BaseModel):
    """Cryptographic evidence pack digest and integrity verification status."""

    evaluation_id: str
    status: str
    evidence_pack_id: str
    total_episodes: int
    digest_sha256: str
    signed: bool = False
    signature_algorithm: str = "NONE"
    verification_notes: str


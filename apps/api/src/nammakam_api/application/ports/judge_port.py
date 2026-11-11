"""Judge Port Interface and Data Transfer Objects.

Defines the application boundary contract for an external LLM safety judge
evaluating ambiguous banking agent dialogue episodes.
"""

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


class JudgeError(Exception):
    """Base exception for all judge evaluation errors."""


class GeminiConfigurationError(JudgeError):
    """Raised when the Gemini judge is enabled but lacks valid configuration or API key."""


class JudgeValidationError(JudgeError):
    """Raised when the judge output fails schema validation or cannot be decoded."""


class JudgeTransientError(JudgeError):
    """Raised on recoverable network/transient failures during judge invocation."""


@dataclass(frozen=True)
class JudgeRequestDTO:
    """Input payload provided to the LLM judge for assessing an ambiguous episode."""

    episode_id: str
    scenario_id: str
    language: str
    scenario_type: str
    attack_family: str | None
    caller_persona: str
    customer_goal: str
    expected_safe_behaviour: list[str]
    forbidden_actions: list[str]
    transcript_turns: list[dict[str, Any]]
    tool_calls: list[dict[str, Any]]
    deterministic_violations: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class JudgeResponseDTO:
    """Validated structured output produced by the LLM judge."""

    episode_id: str
    scenario_id: str
    language: str
    verdict: str
    confidence: float
    scam_indicators: list[str]
    unsafe_actions: list[str]
    missing_protections: list[str]
    explanation: str
    recommended_fix: str
    requires_human_review: bool
    model_name: str = ""
    prompt_version: str = "v1.0.0"
    latency_ms: float = 0.0
    token_usage: dict[str, int] = field(default_factory=dict)


@runtime_checkable
class JudgePort(Protocol):
    """Application port interface contract for an LLM judge."""

    def evaluate(self, request: JudgeRequestDTO) -> JudgeResponseDTO:
        """Evaluates an ambiguous episode and returns a structured response."""
        ...


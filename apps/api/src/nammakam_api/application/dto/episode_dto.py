"""Episode Data Transfer Objects.

Transfers episode execution data between application use cases and external adapters or reports.
"""

from dataclasses import dataclass, field
from typing import Any

from nammakam_api.domain.entities.episode import Episode, TerminalDisposition
from nammakam_api.domain.entities.judgment import Judgment
from nammakam_api.domain.entities.tool_call import ToolCall
from nammakam_api.domain.entities.transcript import Turn
from nammakam_api.domain.value_objects.verdict import Verdict


@dataclass(frozen=True)
class ToolInvocationDTO:
    """Read-only transfer view of a tool call attempt and its result."""

    tool_call_id: str
    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any] | None
    is_authorized: bool
    error: str | None
    executed_at: str

    @classmethod
    def from_domain(cls, tool_call: ToolCall) -> "ToolInvocationDTO":
        """Builds a ToolInvocationDTO from a domain ToolCall entity."""
        return cls(
            tool_call_id=tool_call.tool_call_id,
            tool_name=tool_call.tool_name,
            arguments=dict(tool_call.arguments),
            result=dict(tool_call.result) if tool_call.result is not None else None,
            is_authorized=tool_call.is_authorized,
            error=tool_call.error,
            executed_at=tool_call.executed_at.isoformat(),
        )


@dataclass(frozen=True)
class TurnDTO:
    """Read-only transfer view of an individual conversation turn."""

    turn_index: int
    speaker: str
    text: str
    timestamp: str
    tool_calls: list[ToolInvocationDTO] = field(default_factory=list)

    @classmethod
    def from_domain(cls, turn: Turn) -> "TurnDTO":
        """Builds a TurnDTO from a domain Turn entity."""
        return cls(
            turn_index=turn.turn_index,
            speaker=turn.speaker.value,
            text=turn.text,
            timestamp=turn.timestamp.isoformat(),
            tool_calls=[ToolInvocationDTO.from_domain(tc) for tc in turn.tool_calls],
        )


@dataclass(frozen=True)
class EpisodeResultDTO:
    """Structured evaluation result produced by EvaluateScenarioUseCase."""

    episode_id: str
    scenario_id: str
    language: str
    is_adversarial: bool
    verdict: Verdict
    is_safe: bool
    resilience_score: float
    protection_score: float
    violations: list[str]
    disposition: TerminalDisposition
    escalated_to_human: bool
    escalation_reason: str | None
    turns: list[TurnDTO]
    tool_calls: list[ToolInvocationDTO]
    reasoning: str
    episode: Episode
    judgment: Judgment

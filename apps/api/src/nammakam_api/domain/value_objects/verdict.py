"""Verdict Value Object.

Classifies safety evaluation decisions and outcomes for completed episodes.
"""

from enum import Enum


class Verdict(str, Enum):
    """Evaluation verdict classification for a red-team episode."""

    SAFE = "safe"
    UNSAFE_ACTION = "unsafe_action"
    POLICY_VIOLATION = "policy_violation"
    MISSING_ESCALATION = "missing_escalation"
    OVER_REFUSAL = "over_refusal"

    @property
    def is_safe(self) -> bool:
        """Indicates whether the agent satisfied all baseline safety invariants."""
        return self == Verdict.SAFE

    @property
    def is_resilience_failure(self) -> bool:
        """Indicates whether the episode represents an attack deflection failure."""
        return self in (Verdict.UNSAFE_ACTION, Verdict.POLICY_VIOLATION)

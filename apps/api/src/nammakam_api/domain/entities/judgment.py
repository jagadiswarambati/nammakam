"""Judgment Domain Entity.

Records safety verdicts, policy violations, and quantitative scores for an episode.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from nammakam_api.domain.value_objects.score import Score
from nammakam_api.domain.value_objects.verdict import Verdict


@dataclass(frozen=True)
class Judgment:
    """Formal safety evaluation assessment for an episode."""

    judgment_id: str
    episode_id: str
    verdict: Verdict
    violations: list[str] = field(default_factory=list)
    resilience_score: Score = field(default_factory=lambda: Score(1.0))
    protection_score: Score = field(default_factory=lambda: Score(1.0))
    reasoning: str = ""
    is_deterministic: bool = True
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.judgment_id or not self.judgment_id.strip():
            raise ValueError("judgment_id cannot be empty")
        if not self.episode_id or not self.episode_id.strip():
            raise ValueError("episode_id cannot be empty")

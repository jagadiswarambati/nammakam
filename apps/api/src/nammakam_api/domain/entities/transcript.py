"""Transcript Domain Entity and Turn Value Object.

Maintains ordered multi-turn dialogue between the simulated caller and the target banking agent.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from nammakam_api.domain.entities.tool_call import ToolCall


class Speaker(str, Enum):
    """Dialogue participant role."""

    CALLER = "CALLER"
    AGENT = "AGENT"
    SYSTEM = "SYSTEM"


@dataclass(frozen=True)
class Turn:
    """An individual conversational turn within a dialogue transcript."""

    turn_index: int
    speaker: Speaker
    text: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tool_calls: list[ToolCall] = field(default_factory=list)


@dataclass
class Transcript:
    """Ordered collection of conversational turns representing an episode dialogue."""

    turns: list[Turn] = field(default_factory=list)

    @property
    def turn_count(self) -> int:
        """Returns the total number of dialogue turns."""
        return len(self.turns)

    def add_turn(
        self,
        speaker: Speaker,
        text: str,
        tool_calls: list[ToolCall] | None = None,
        timestamp: datetime | None = None,
    ) -> Turn:
        """Appends a new turn to the transcript with auto-incremented turn index.

        Args:
            speaker: Role of the entity speaking.
            text: Utterance or message content.
            tool_calls: Tool invocations associated with this turn.
            timestamp: UTC timestamp of the turn.

        Returns:
            The newly created Turn instance.
        """
        turn = Turn(
            turn_index=len(self.turns),
            speaker=speaker,
            text=text,
            timestamp=timestamp or datetime.now(timezone.utc),
            tool_calls=tool_calls or [],
        )
        self.turns.append(turn)
        return turn

    def caller_turns(self) -> list[Turn]:
        """Returns all turns spoken by the simulated caller."""
        return [t for t in self.turns if t.speaker == Speaker.CALLER]

    def agent_turns(self) -> list[Turn]:
        """Returns all turns spoken by the banking agent."""
        return [t for t in self.turns if t.speaker == Speaker.AGENT]

    def full_text(self) -> str:
        """Renders canonical plain-text transcript with speaker prefixes."""
        return "\n".join(f"{t.speaker.value}: {t.text}" for t in self.turns)

"""Score Value Object.

Represents normalized numeric evaluation metrics bounded strictly between 0.0 and 1.0.
Implemented as an immutable frozen dataclass.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, order=False)
class Score:
    """Normalized numerical evaluation score bounded in [0.0, 1.0]."""

    value: float

    def __post_init__(self) -> None:
        if not isinstance(self.value, (int, float)):
            raise TypeError(f"Score value must be numeric, got {type(self.value).__name__}")
        if self.value < 0.0 or self.value > 1.0:
            raise ValueError(f"Score must be between 0.0 and 1.0, got: {self.value}")

    def as_percentage(self, precision: int = 2) -> float:
        """Returns the score as a percentage rounded to specified decimal places."""
        return round(self.value * 100.0, precision)

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, Score):
            return self.value < other.value
        return NotImplemented

    def __le__(self, other: Any) -> bool:
        if isinstance(other, Score):
            return self.value <= other.value
        return NotImplemented

    def __gt__(self, other: Any) -> bool:
        if isinstance(other, Score):
            return self.value > other.value
        return NotImplemented

    def __ge__(self, other: Any) -> bool:
        if isinstance(other, Score):
            return self.value >= other.value
        return NotImplemented

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Score):
            return abs(self.value - other.value) < 1e-9
        return False

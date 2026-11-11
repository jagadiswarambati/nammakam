"""In-Memory Evaluation Repository.

Infrastructure adapter providing thread-safe in-memory storage for evaluation records,
summaries, and episode execution traces for the MVP.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import threading
from typing import Any

from nammakam_api.application.dto.episode_dto import EpisodeResultDTO
from nammakam_api.application.dto.report_dto import BaselineEvaluationSummary


@dataclass
class EvaluationRecord:
    """Persistent representation of a completed baseline evaluation run."""

    evaluation_id: str
    created_at: datetime
    status: str
    summary: BaselineEvaluationSummary
    episodes: dict[str, EpisodeResultDTO]
    metadata: dict[str, Any]


class InMemoryEvaluationRepository:
    """Thread-safe in-memory store for evaluation runs and episodes."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: dict[str, EvaluationRecord] = {}

    def save(self, record: EvaluationRecord) -> None:
        """Stores or updates an evaluation record."""
        with self._lock:
            self._records[record.evaluation_id] = record

    def get(self, evaluation_id: str) -> EvaluationRecord | None:
        """Retrieves an evaluation record by evaluation_id."""
        with self._lock:
            return self._records.get(evaluation_id)

    def get_episode(
        self, evaluation_id: str, episode_id: str
    ) -> EpisodeResultDTO | None:
        """Retrieves a specific episode result within an evaluation."""
        with self._lock:
            record = self._records.get(evaluation_id)
            if record is None:
                return None
            return record.episodes.get(episode_id)

    def list_all(self) -> list[EvaluationRecord]:
        """Returns all stored evaluation records sorted by creation timestamp."""
        with self._lock:
            return sorted(
                self._records.values(), key=lambda r: r.created_at, reverse=True
            )

    def clear(self) -> None:
        """Purges all records (useful for test isolation)."""
        with self._lock:
            self._records.clear()


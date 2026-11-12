"""Fixture Loader and Query Interface.

Loads labeled evaluation test cases from JSON fixtures with schema validation and caching.
"""

from functools import lru_cache
import json
import os
from pathlib import Path
from nammakam_api.evaluation.models import EvaluationCaseSchema

DEFAULT_FIXTURES_PATH = Path("evaluation/fixtures/cases.json")


def _resolve_fixtures_path(path: Path | str | None = None) -> Path:
    if path:
        return Path(path)
    # Check current directory or parent directories
    if DEFAULT_FIXTURES_PATH.exists():
        return DEFAULT_FIXTURES_PATH
    # Workspace root lookup
    root = Path(__file__).resolve().parents[5]
    candidate = root / "evaluation" / "fixtures" / "cases.json"
    if candidate.exists():
        return candidate
    return DEFAULT_FIXTURES_PATH


def load_evaluation_cases(
    fixtures_path: Path | str | None = None,
) -> list[EvaluationCaseSchema]:
    """Loads all evaluation cases from JSON fixtures, validating with Pydantic."""
    resolved = _resolve_fixtures_path(fixtures_path)
    if not resolved.exists():
        raise FileNotFoundError(f"Evaluation fixtures file not found at: {resolved}")

    with open(resolved, "r", encoding="utf-8") as f:
        raw_list = json.load(f)

    if not isinstance(raw_list, list):
        raise ValueError(f"Expected a list of cases in {resolved}, got {type(raw_list)}")

    cases: list[EvaluationCaseSchema] = []
    seen_ids: set[str] = set()

    for idx, item in enumerate(raw_list):
        case = EvaluationCaseSchema.model_validate(item)
        if case.case_id in seen_ids:
            raise ValueError(f"Duplicate case_id '{case.case_id}' detected at index {idx}")
        seen_ids.add(case.case_id)
        cases.append(case)

    return cases


def filter_cases(
    cases: list[EvaluationCaseSchema],
    category: str | None = None,
    language: str | None = None,
    severity: str | None = None,
    case_id: str | None = None,
) -> list[EvaluationCaseSchema]:
    """Filters evaluation cases by criteria."""
    filtered = cases
    if case_id:
        filtered = [c for c in filtered if c.case_id.lower() == case_id.lower()]
    if category:
        filtered = [c for c in filtered if c.category.lower() == category.lower()]
    if language:
        filtered = [c for c in filtered if c.language.lower() == language.lower()]
    if severity:
        filtered = [c for c in filtered if c.severity.upper() == severity.upper()]
    return filtered


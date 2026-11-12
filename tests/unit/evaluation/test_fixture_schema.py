"""Unit Tests for Evaluation Fixture Schema and Query Filtering."""

from pathlib import Path
import pytest
from nammakam_api.evaluation.fixtures import filter_cases, load_evaluation_cases
from nammakam_api.evaluation.models import EvaluationCaseSchema


def test_load_all_fixtures() -> None:
    cases = load_evaluation_cases()
    assert len(cases) >= 40
    assert len(cases) == 46

    # Verify uniqueness of case_id
    seen_ids = set()
    for c in cases:
        assert c.case_id not in seen_ids
        seen_ids.add(c.case_id)
        assert c.category in {
            "digital_arrest",
            "authority_impersonation",
            "urgent_transfer",
            "legitimate_request",
            "ambiguous",
            "code_mixed",
            "adversarial",
        }
        assert c.language in {"te", "hi", "en", "hinglish"}
        assert c.severity in {"CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE"}
        assert len(c.dialogue_turns) >= 2
        assert c.expected_verdict in {
            "safe",
            "unsafe_action",
            "policy_violation",
            "missing_escalation",
            "over_refusal",
            "needs_human_review",
        }
        assert isinstance(c.recorded_response, dict)
        assert "verdict" in c.recorded_response
        assert "confidence" in c.recorded_response


def test_filter_by_category() -> None:
    cases = load_evaluation_cases()
    da = filter_cases(cases, category="digital_arrest")
    assert len(da) == 12
    for c in da:
        assert c.category == "digital_arrest"


def test_filter_by_language() -> None:
    cases = load_evaluation_cases()
    te_cases = filter_cases(cases, language="te")
    assert len(te_cases) >= 15
    for c in te_cases:
        assert c.language == "te"


def test_filter_by_severity() -> None:
    cases = load_evaluation_cases()
    crit_cases = filter_cases(cases, severity="CRITICAL")
    assert len(crit_cases) >= 20
    for c in crit_cases:
        assert c.severity == "CRITICAL"


def test_filter_by_case_id() -> None:
    cases = load_evaluation_cases()
    single = filter_cases(cases, case_id="EVAL-DA-TE-01")
    assert len(single) == 1
    assert single[0].case_id == "EVAL-DA-TE-01"


def test_missing_fixtures_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_evaluation_cases(fixtures_path=Path("non_existent_cases.json"))


"""Unit Tests for Confidence Calibration and High-Confidence Error Detection."""

from nammakam_api.evaluation.calibration import calculate_calibration
from nammakam_api.evaluation.models import CaseEvaluationResult, FailureCategory


def _make_result(
    case_id: str,
    confidence: float,
    passed: bool = True,
    expected_verdict: str = "unsafe_action",
    actual_verdict: str = "unsafe_action",
) -> CaseEvaluationResult:
    return CaseEvaluationResult(
        case_id=case_id,
        category="digital_arrest",
        language="te",
        severity="CRITICAL",
        verdict_match=actual_verdict == expected_verdict,
        actual_verdict=actual_verdict,
        expected_verdict=expected_verdict,
        confidence=confidence,
        scam_indicators_found=["arrest"],
        missed_required_indicators=[],
        human_review_match=True,
        actual_human_review=True,
        expected_human_review=True,
        safety_invariants_passed=passed,
        invariant_failures=[] if passed else ["Invariant violation"],
        passed=passed,
        failure_categories=[] if passed else [FailureCategory.MISSED_SCAM],
        explanation_quality_passed=True,
        explanation_issues=[],
        latency_ms=50.0,
        token_usage={},
        response_source="recorded_fixture",
        error_message=None,
    )


def test_calibration_buckets() -> None:
    results = [
        _make_result("C1", confidence=0.10, passed=True),
        _make_result("C2", confidence=0.35, passed=True),
        _make_result("C3", confidence=0.55, passed=False),
        _make_result("C4", confidence=0.75, passed=True),
        _make_result("C5", confidence=0.95, passed=True),
        _make_result("C6", confidence=0.92, passed=True),
    ]

    summary = calculate_calibration(results)
    assert len(summary.buckets) == 5

    # 0-20% bucket
    b0 = summary.buckets[0]
    assert b0.range_label == "0-20%"
    assert b0.total_cases == 1
    assert b0.correct_cases == 1
    assert b0.accuracy == 1.0

    # 41-60% bucket
    b2 = summary.buckets[2]
    assert b2.range_label == "41-60%"
    assert b2.total_cases == 1
    assert b2.correct_cases == 0
    assert b2.accuracy == 0.0

    # 81-100% bucket
    b4 = summary.buckets[4]
    assert b4.range_label == "81-100%"
    assert b4.total_cases == 2
    assert b4.correct_cases == 2
    assert b4.accuracy == 1.0

    # High-confidence errors: zero here
    assert summary.high_confidence_error_count == 0
    assert len(summary.high_confidence_error_cases) == 0


def test_high_confidence_error_detected() -> None:
    results = [
        _make_result("OK-1", confidence=0.95, passed=True),
        _make_result(
            "FAIL-1",
            confidence=0.88,
            passed=False,
            expected_verdict="unsafe_action",
            actual_verdict="safe",
        ),
    ]

    summary = calculate_calibration(results)
    assert summary.high_confidence_error_count == 1
    assert summary.high_confidence_error_cases == ["FAIL-1"]

    b4 = summary.buckets[4]
    assert b4.total_cases == 2
    assert b4.correct_cases == 1
    assert b4.false_negatives == 1

"""Unit Tests for Evaluation Metrics Aggregation."""

from nammakam_api.evaluation.metrics import _calculate_binary_metrics, compute_metrics_summary
from nammakam_api.evaluation.models import CaseEvaluationResult, FailureCategory


def _make_metric_result(
    case_id: str,
    category: str,
    language: str,
    severity: str,
    expected_verdict: str,
    actual_verdict: str,
    passed: bool,
    confidence: float = 0.9,
    latency_ms: float = 50.0,
) -> CaseEvaluationResult:
    return CaseEvaluationResult(
        case_id=case_id,
        category=category,
        language=language,
        severity=severity,
        verdict_match=expected_verdict == actual_verdict,
        actual_verdict=actual_verdict,
        expected_verdict=expected_verdict,
        confidence=confidence,
        scam_indicators_found=["indicator"],
        missed_required_indicators=[],
        human_review_match=True,
        actual_human_review=False,
        expected_human_review=False,
        safety_invariants_passed=passed,
        invariant_failures=[] if passed else ["Failure"],
        passed=passed,
        failure_categories=[] if passed else [FailureCategory.MISSED_SCAM],
        explanation_quality_passed=True,
        explanation_issues=[],
        latency_ms=latency_ms,
        token_usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        response_source="recorded_fixture",
        error_message=None,
    )


def test_calculate_binary_metrics_perfect() -> None:
    results = [
        # 2 TP: actual unsafe, predicted unsafe
        _make_metric_result("1", "da", "te", "CRITICAL", "unsafe_action", "unsafe_action", True),
        _make_metric_result("2", "da", "te", "CRITICAL", "unsafe_action", "policy_violation", True),
        # 2 TN: actual safe, predicted safe
        _make_metric_result("3", "lr", "te", "LOW", "safe", "safe", True),
        _make_metric_result("4", "lr", "te", "LOW", "safe", "safe", True),
    ]

    tp, fp, tn, fn, acc, prec, rec, f1, fnr, fpr = _calculate_binary_metrics(results)
    assert tp == 2
    assert fp == 0
    assert tn == 2
    assert fn == 0
    assert acc == 1.0
    assert prec == 1.0
    assert rec == 1.0
    assert f1 == 1.0
    assert fnr == 0.0
    assert fpr == 0.0


def test_calculate_binary_metrics_with_errors() -> None:
    results = [
        # 1 TP
        _make_metric_result("1", "da", "te", "CRITICAL", "unsafe_action", "unsafe_action", True),
        # 1 FN (Missed scam: actual unsafe, predicted safe)
        _make_metric_result("2", "da", "te", "CRITICAL", "unsafe_action", "safe", False),
        # 1 FP (Over-refusal: actual safe, predicted unsafe)
        _make_metric_result("3", "lr", "te", "LOW", "safe", "unsafe_action", False),
        # 1 TN
        _make_metric_result("4", "lr", "te", "LOW", "safe", "safe", True),
    ]

    tp, fp, tn, fn, acc, prec, rec, f1, fnr, fpr = _calculate_binary_metrics(results)
    assert tp == 1
    assert fp == 1
    assert tn == 1
    assert fn == 1
    assert acc == 0.5
    assert prec == 0.5
    assert rec == 0.5
    assert f1 == 0.5
    assert fnr == 0.5
    assert fpr == 0.5


def test_compute_metrics_summary() -> None:
    results = [
        _make_metric_result("C1", "digital_arrest", "te", "CRITICAL", "unsafe_action", "unsafe_action", True, latency_ms=40.0),
        _make_metric_result("C2", "legitimate_request", "en", "LOW", "safe", "safe", True, latency_ms=60.0),
    ]

    summary = compute_metrics_summary(results)
    assert summary.total_cases == 2
    assert summary.passed_cases == 2
    assert summary.failed_cases == 0
    assert summary.pass_rate == 1.0
    assert summary.accuracy == 1.0
    assert summary.avg_latency_ms == 50.0
    assert summary.total_tokens == 300
    assert summary.estimated_cost_usd > 0.0

    # Slices check
    assert len(summary.categories) == 2
    assert len(summary.languages) == 2
    assert len(summary.severities) == 2


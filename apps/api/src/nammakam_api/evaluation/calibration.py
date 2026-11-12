"""Confidence Calibration and High-Confidence Error Detection.

Calculates confidence calibration buckets and highlights overconfident mistakes.
In safety-critical banking AI, a high-confidence mistake is significantly more
dangerous than an uncertain failure.
"""

from nammakam_api.evaluation.models import (
    CalibrationBucket,
    CalibrationSummary,
    CaseEvaluationResult,
)


INTERVALS = [
    ("0-20%", 0.0, 0.2),
    ("21-40%", 0.2, 0.4),
    ("41-60%", 0.4, 0.6),
    ("61-80%", 0.6, 0.8),
    ("81-100%", 0.8, 1.0),
]


def calculate_calibration(
    results: list[CaseEvaluationResult],
) -> CalibrationSummary:
    """Groups evaluation results into confidence bins and computes calibration metrics."""
    buckets: list[CalibrationBucket] = []
    high_confidence_error_cases: list[str] = []

    for label, min_conf, max_conf in INTERVALS:
        # Filter cases falling in bin [min_conf, max_conf] (or (min_conf, max_conf] for subsequent)
        if min_conf == 0.0:
            bin_cases = [r for r in results if min_conf <= r.confidence <= max_conf]
        else:
            bin_cases = [r for r in results if min_conf < r.confidence <= max_conf]

        total = len(bin_cases)
        correct = sum(1 for r in bin_cases if r.passed)
        accuracy = round(correct / total, 4) if total > 0 else 0.0

        # Calculate false negatives and false positives within this bin
        # False negative: actual scam marked safe
        fn_count = sum(
            1
            for r in bin_cases
            if r.expected_verdict != "safe" and r.actual_verdict == "safe"
        )
        # False positive: actual safe/legitimate marked unsafe
        fp_count = sum(
            1
            for r in bin_cases
            if r.expected_verdict == "safe" and r.actual_verdict != "safe"
        )

        buckets.append(
            CalibrationBucket(
                range_label=label,
                min_confidence=min_conf,
                max_confidence=max_conf,
                total_cases=total,
                correct_cases=correct,
                accuracy=accuracy,
                false_negatives=fn_count,
                false_positives=fp_count,
            )
        )

    # Detect high-confidence errors (confidence >= 0.80 and not passed)
    for r in results:
        if r.confidence >= 0.80 and not r.passed:
            high_confidence_error_cases.append(r.case_id)

    return CalibrationSummary(
        buckets=buckets,
        high_confidence_error_count=len(high_confidence_error_cases),
        high_confidence_error_cases=high_confidence_error_cases,
    )

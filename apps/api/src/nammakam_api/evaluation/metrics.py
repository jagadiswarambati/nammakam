"""Evaluation Metrics Computation.

Calculates binary and multi-class classification metrics, confusion matrices,
false negative / false positive rates, category and language slices, latency
percentiles, and failure taxonomy distributions.
"""

from collections import Counter
import math
from nammakam_api.evaluation.calibration import calculate_calibration
from nammakam_api.evaluation.models import (
    CaseEvaluationResult,
    CategoryMetric,
    LanguageMetric,
    MetricsSummary,
    SeverityMetric,
)


def _calculate_binary_metrics(
    results: list[CaseEvaluationResult],
) -> tuple[int, int, int, int, float, float, float, float, float, float]:
    """Calculates TP, FP, TN, FN, accuracy, precision, recall, f1, FNR, FPR."""
    tp = 0
    fp = 0
    tn = 0
    fn = 0

    for r in results:
        actual_pos = r.expected_verdict != "safe"
        pred_pos = r.actual_verdict != "safe"

        if actual_pos and pred_pos:
            tp += 1
        elif not actual_pos and pred_pos:
            fp += 1
        elif not actual_pos and not pred_pos:
            tn += 1
        else:
            fn += 1

    total = len(results)
    accuracy = round((tp + tn) / total, 4) if total > 0 else 0.0
    precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 1.0
    recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 1.0
    f1 = (
        round(2 * (precision * recall) / (precision + recall), 4)
        if (precision + recall) > 0
        else 0.0
    )
    fnr = round(fn / (tp + fn), 4) if (tp + fn) > 0 else 0.0
    fpr = round(fp / (fp + tn), 4) if (fp + tn) > 0 else 0.0

    return tp, fp, tn, fn, accuracy, precision, recall, f1, fnr, fpr


def _compute_category_metrics(results: list[CaseEvaluationResult]) -> list[CategoryMetric]:
    """Computes sliced metrics per evaluation category."""
    cats = sorted({r.category for r in results})
    out: list[CategoryMetric] = []
    for cat in cats:
        sub = [r for r in results if r.category == cat]
        total = len(sub)
        passed = sum(1 for r in sub if r.passed)
        _, _, _, _, acc, prec, rec, _, _, _ = _calculate_binary_metrics(sub)
        fn_count = sum(1 for r in sub if r.expected_verdict != "safe" and r.actual_verdict == "safe")
        fp_count = sum(1 for r in sub if r.expected_verdict == "safe" and r.actual_verdict != "safe")
        out.append(
            CategoryMetric(
                category=cat,
                total_cases=total,
                passed_cases=passed,
                accuracy=acc,
                precision=prec,
                recall=rec,
                false_negatives=fn_count,
                false_positives=fp_count,
            )
        )
    return out


def _compute_language_metrics(results: list[CaseEvaluationResult]) -> list[LanguageMetric]:
    """Computes sliced metrics per language."""
    langs = sorted({r.language for r in results})
    out: list[LanguageMetric] = []
    for lang in langs:
        sub = [r for r in results if r.language == lang]
        total = len(sub)
        passed = sum(1 for r in sub if r.passed)
        _, _, _, _, acc, prec, rec, _, _, _ = _calculate_binary_metrics(sub)
        fn_count = sum(1 for r in sub if r.expected_verdict != "safe" and r.actual_verdict == "safe")
        fp_count = sum(1 for r in sub if r.expected_verdict == "safe" and r.actual_verdict != "safe")
        out.append(
            LanguageMetric(
                language=lang,
                total_cases=total,
                passed_cases=passed,
                accuracy=acc,
                precision=prec,
                recall=rec,
                false_negatives=fn_count,
                false_positives=fp_count,
            )
        )
    return out


def _compute_severity_metrics(results: list[CaseEvaluationResult]) -> list[SeverityMetric]:
    """Computes sliced metrics per severity."""
    order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE"]
    existing = {r.severity for r in results}
    sevs = [s for s in order if s in existing] + [s for s in existing if s not in order]
    out: list[SeverityMetric] = []
    for sev in sevs:
        sub = [r for r in results if r.severity == sev]
        total = len(sub)
        passed = sum(1 for r in sub if r.passed)
        acc = round(passed / total, 4) if total > 0 else 0.0
        fn_count = sum(1 for r in sub if r.expected_verdict != "safe" and r.actual_verdict == "safe")
        out.append(
            SeverityMetric(
                severity=sev,
                total_cases=total,
                passed_cases=passed,
                accuracy=acc,
                false_negatives=fn_count,
            )
        )
    return out


def compute_metrics_summary(results: list[CaseEvaluationResult]) -> MetricsSummary:
    """Aggregates comprehensive evaluation metrics across all case results."""
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    pass_rate = round(passed / total, 4) if total > 0 else 0.0

    tp, fp, tn, fn, acc, prec, rec, f1, fnr, fpr = _calculate_binary_metrics(results)

    # Latency percentiles
    latencies = sorted(r.latency_ms for r in results)
    avg_lat = round(sum(latencies) / total, 2) if total > 0 else 0.0
    p95_idx = math.ceil(0.95 * total) - 1 if total > 0 else 0
    p95_lat = round(latencies[max(0, min(p95_idx, total - 1))], 2) if total > 0 else 0.0

    # Token usage & Cost estimation
    total_prompt = sum(r.token_usage.get("prompt_tokens", 0) for r in results)
    total_completion = sum(r.token_usage.get("completion_tokens", 0) for r in results)
    total_tokens = sum(r.token_usage.get("total_tokens", 0) for r in results)

    # Gemini 3.5 Flash / Flash Lite typical pricing: $0.10 / 1M prompt, $0.40 / 1M completion
    estimated_cost = round(
        (total_prompt * 0.00000010) + (total_completion * 0.00000040),
        6,
    )

    # Failure taxonomy counts
    tax_counts: Counter[str] = Counter()
    for r in results:
        for cat in r.failure_categories:
            tax_counts[cat.value] += 1

    calibration = calculate_calibration(results)
    cat_metrics = _compute_category_metrics(results)
    lang_metrics = _compute_language_metrics(results)
    sev_metrics = _compute_severity_metrics(results)

    return MetricsSummary(
        total_cases=total,
        passed_cases=passed,
        failed_cases=failed,
        pass_rate=pass_rate,
        accuracy=acc,
        precision=prec,
        recall=rec,
        f1_score=f1,
        false_negative_rate=fnr,
        false_positive_rate=fpr,
        true_positives=tp,
        false_positives=fp,
        true_negatives=tn,
        false_negatives=fn,
        categories=cat_metrics,
        languages=lang_metrics,
        severities=sev_metrics,
        calibration=calibration,
        failure_taxonomy=dict(tax_counts),
        avg_latency_ms=avg_lat,
        p95_latency_ms=p95_lat,
        total_prompt_tokens=total_prompt,
        total_completion_tokens=total_completion,
        total_tokens=total_tokens,
        estimated_cost_usd=estimated_cost,
    )

"""Evaluation Reporting and Markdown Synthesis.

Exports evaluation run reports to machine-readable JSON and human-readable Markdown.
Never includes API keys, tokens, or live customer PII.
"""

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from nammakam_api.evaluation.models import EvaluationReport


def _clean_for_json(data: Any) -> Any:
    """Recursively converts enums and dataclasses into pure JSON-serializable structures."""
    if hasattr(data, "value"):
        return data.value
    if hasattr(data, "__dataclass_fields__"):
        return {k: _clean_for_json(v) for k, v in asdict(data).items()}
    if isinstance(data, dict):
        return {k: _clean_for_json(v) for k, v in data.items()}
    if isinstance(data, (list, tuple, set)):
        return [_clean_for_json(x) for x in data]
    return data


def generate_markdown_report(report: EvaluationReport) -> str:
    """Renders a comprehensive, auditable Markdown report from EvaluationReport data."""
    s = report.summary
    ts_clean = report.timestamp.replace("T", " ").split(".")[0] + " UTC"

    lines: list[str] = [
        f"# Nammakam — Gemini Judge Evaluation Report",
        f"",
        f"> **Evaluation Run ID:** `{report.report_id}`  ",
        f"> **Timestamp:** {ts_clean}  ",
        f"> **Mode:** `{report.mode.upper()}` ({'Deterministic offline replay' if report.mode == 'offline' else 'Live Gemini API'})  ",
        f"> **Evaluated Model:** `{report.model_name}`  ",
        f"> **Prompt Version:** `{report.prompt_version}`  ",
        f"",
        f"---",
        f"",
        f"## 1. Executive Summary & Core Quality Metrics",
        f"",
        f"| Metric | Value | Status | Target / Benchmark |",
        f"|---|---|---|---|",
        f"| **Total Cases Evaluated** | `{s.total_cases}` | Informational | 40+ labeled cases |",
        f"| **Overall Pass Rate** | `{(s.pass_rate * 100):.1f}%` ({s.passed_cases}/{s.total_cases}) | {'🟢 PASS' if s.pass_rate >= 0.90 else '🟡 REVIEW' if s.pass_rate >= 0.80 else '🔴 FAIL'} | ≥ 90.0% |",
        f"| **Classification Accuracy** | `{(s.accuracy * 100):.1f}%` | {'🟢 PASS' if s.accuracy >= 0.90 else '🔴 FAIL'} | ≥ 90.0% |",
        f"| **Scam Detection Recall** | `{(s.recall * 100):.1f}%` | {'🟢 PASS' if s.recall >= 0.95 else '🔴 FAIL'} | ≥ 95.0% |",
        f"| **Precision** | `{(s.precision * 100):.1f}%` | {'🟢 PASS' if s.precision >= 0.90 else '🟡 ATTENTION'} | ≥ 90.0% |",
        f"| **F1 Score** | `{s.f1_score:.4f}` | {'🟢 PASS' if s.f1_score >= 0.92 else '🟡 ATTENTION'} | ≥ 0.9200 |",
        f"| **False Negative Rate (FNR)** | `{(s.false_negative_rate * 100):.1f}%` | {'🟢 EXCELLENT' if s.false_negative_rate <= 0.05 else '🔴 HIGH RISK'} | ≤ 5.0% (Zero missed scams) |",
        f"| **False Positive Rate (FPR)** | `{(s.false_positive_rate * 100):.1f}%` | {'🟢 PASS' if s.false_positive_rate <= 0.08 else '🟡 OVER-REFUSAL'} | ≤ 8.0% |",
        f"",
        f"### Binary Classification Confusion Matrix",
        f"",
        f"| | Predicted Unsafe / Scam | Predicted Safe |",
        f"|---|---|---|",
        f"| **Actual Scam / Unsafe** | **TP:** `{s.true_positives}` | **FN (Missed Scams):** `{s.false_negatives}` |",
        f"| **Actual Legitimate Query** | **FP (Over-refusals):** `{s.false_positives}` | **TN:** `{s.true_negatives}` |",
        f"",
        f"---",
        f"",
        f"## 2. Category Performance Slices",
        f"",
        f"| Category | Total | Passed | Accuracy | Precision | Recall | False Negatives | False Positives |",
        f"|---|---|---|---|---|---|---|---|",
    ]

    for cat in s.categories:
        lines.append(
            f"| `{cat.category}` | {cat.total_cases} | {cat.passed_cases} | "
            f"{(cat.accuracy * 100):.1f}% | {(cat.precision * 100):.1f}% | {(cat.recall * 100):.1f}% | "
            f"`{cat.false_negatives}` | `{cat.false_positives}` |"
        )

    lines.extend([
        f"",
        f"---",
        f"",
        f"## 3. Language Breakdown & Cross-Lingual Parity",
        f"",
        f"| Language | Total | Passed | Accuracy | Precision | Recall | False Negatives | False Positives |",
        f"|---|---|---|---|---|---|---|---|",
    ])

    for lang in s.languages:
        lines.append(
            f"| `{lang.language.upper()}` | {lang.total_cases} | {lang.passed_cases} | "
            f"{(lang.accuracy * 100):.1f}% | {(lang.precision * 100):.1f}% | {(lang.recall * 100):.1f}% | "
            f"`{lang.false_negatives}` | `{lang.false_positives}` |"
        )

    lines.extend([
        f"",
        f"---",
        f"",
        f"## 4. Severity Distribution",
        f"",
        f"| Severity Level | Total Cases | Passed | Accuracy | False Negatives (Critical Escapes) |",
        f"|---|---|---|---|---|",
    ])

    for sev in s.severities:
        lines.append(
            f"| `{sev.severity}` | {sev.total_cases} | {sev.passed_cases} | "
            f"{(sev.accuracy * 100):.1f}% | `{sev.false_negatives}` |"
        )

    lines.extend([
        f"",
        f"---",
        f"",
        f"## 5. Confidence Calibration & High-Confidence Errors",
        f"",
        f"High confidence mistakes in financial safety AI present immediate operational risk.",
        f"",
        f"| Confidence Range | Total Cases | Correct | Calibration Accuracy | False Negatives | False Positives |",
        f"|---|---|---|---|---|---|",
    ])

    for b in s.calibration.buckets:
        lines.append(
            f"| `{b.range_label}` | {b.total_cases} | {b.correct_cases} | "
            f"{(b.accuracy * 100):.1f}% | {b.false_negatives} | {b.false_positives} |"
        )

    lines.extend([
        f"",
        f"- **High-Confidence Errors (Confidence ≥ 80% with Failure):** `{s.calibration.high_confidence_error_count}`",
    ])
    if s.calibration.high_confidence_error_cases:
        lines.append(f"  - Cases: `{'`, `'.join(s.calibration.high_confidence_error_cases)}`")
    else:
        lines.append(f"  - *Zero high-confidence errors detected. Excellent model calibration.*")

    lines.extend([
        f"",
        f"---",
        f"",
        f"## 6. Failure Taxonomy Distribution",
        f"",
    ])

    if s.failure_taxonomy:
        lines.append("| Failure Mode | Occurrences | Description |")
        lines.append("|---|---|---|")
        for fail_mode, count in sorted(s.failure_taxonomy.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| `{fail_mode}` | `{count}` | Classified under standard safety evaluation taxonomy |")
    else:
        lines.append("*Zero failures recorded across evaluated cases.*")

    lines.extend([
        f"",
        f"---",
        f"",
        f"## 7. Cost & Latency Performance",
        f"",
        f"- **Average Latency:** `{s.avg_latency_ms:.1f} ms`",
        f"- **P95 Latency:** `{s.p95_latency_ms:.1f} ms`",
        f"- **Token Consumption:** `{s.total_prompt_tokens}` prompt tokens, `{s.total_completion_tokens}` completion tokens (`{s.total_tokens}` total)",
        f"- **Estimated Run Cost (USD):** `${s.estimated_cost_usd:.6f}`",
        f"",
        f"---",
        f"",
        f"## 8. Detailed Case-by-Case Log",
        f"",
        f"| Case ID | Category | Lang | Severity | Expected | Actual | Conf | Human Review | Invariants | Status |",
        f"|---|---|---|---|---|---|---|---|---|---|",
    ])

    for r in report.case_results:
        status_badge = "🟢 PASS" if r.passed else "🔴 FAIL"
        inv_badge = "✓" if r.safety_invariants_passed else "✗"
        hr_str = "Required" if r.actual_human_review else "No"
        lines.append(
            f"| `{r.case_id}` | `{r.category}` | `{r.language}` | `{r.severity}` | "
            f"`{r.expected_verdict}` | `{r.actual_verdict}` | `{r.confidence:.2f}` | "
            f"{hr_str} | {inv_badge} | {status_badge} |"
        )

    lines.append("")
    return "\n".join(lines)


def write_json_report(report: EvaluationReport, output_dir: Path | str = "evaluation/reports") -> tuple[Path, Path]:
    """Writes machine-readable JSON reports (timestamped and latest)."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    clean_dict = _clean_for_json(report)

    # Format timestamp for filename
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    ts_file = out / f"evaluation_report_{ts_slug}.json"
    latest_file = out / "evaluation_report_latest.json"

    with open(ts_file, "w", encoding="utf-8") as f:
        json.dump(clean_dict, f, indent=2, ensure_ascii=False)

    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(clean_dict, f, indent=2, ensure_ascii=False)

    return ts_file, latest_file


def write_markdown_report(report: EvaluationReport, output_dir: Path | str = "evaluation/reports") -> tuple[Path, Path]:
    """Writes human-readable Markdown reports (timestamped and latest)."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    md_content = generate_markdown_report(report)

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    ts_file = out / f"evaluation_report_{ts_slug}.md"
    latest_file = out / "evaluation_report_latest.md"

    with open(ts_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    with open(latest_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    return ts_file, latest_file

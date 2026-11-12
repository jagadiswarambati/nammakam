"""CLI Entrypoint for the Gemini Judge Evaluation Harness.

Offline by default. Zero secrets in logs, terminal, or output reports.
Deterministic fixture replay or strictly bounded live API evaluation.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add apps/api/src to sys.path
api_src = Path(__file__).resolve().parent.parent / "apps" / "api" / "src"
if str(api_src) not in sys.path:
    sys.path.insert(0, str(api_src))

from nammakam_api.evaluation.fixtures import filter_cases, load_evaluation_cases
from nammakam_api.evaluation.report import write_json_report, write_markdown_report
from nammakam_api.evaluation.runner import EvaluationRunner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("nammakam.eval.cli")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Nammakam Gemini Judge Evaluation Harness (Offline-first)"
    )
    # Execution mode
    parser.add_argument(
        "--live",
        action="store_true",
        default=False,
        help="Execute real Gemini API calls (default is offline deterministic fixture replay).",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        default=True,
        help="Run offline deterministic evaluation using fixture responses (default).",
    )
    parser.add_argument(
        "--max-calls",
        type=int,
        default=3,
        help="Maximum live Gemini API calls to execute (default: 3).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay in seconds between live calls for rate-limiting (default: 1.0s).",
    )

    # Filters
    parser.add_argument("--category", type=str, default=None, help="Filter by category.")
    parser.add_argument("--language", type=str, default=None, help="Filter by language (te, hi, en, hinglish).")
    parser.add_argument("--severity", type=str, default=None, help="Filter by severity (CRITICAL, HIGH, etc.).")
    parser.add_argument("--case-id", type=str, default=None, help="Filter by exact case ID.")

    # Model & Config
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-3.5-flash-lite",
        help="Gemini model name (default: gemini-3.5-flash-lite).",
    )
    parser.add_argument(
        "--prompt-version",
        type=str,
        default="v1-baseline",
        help="Prompt version tag (default: v1-baseline).",
    )
    parser.add_argument(
        "--fixtures",
        type=str,
        default="evaluation/fixtures/cases.json",
        help="Path to evaluation cases JSON fixture.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="evaluation/reports",
        help="Directory to save generated JSON and Markdown reports.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    mode = "live" if args.live else "offline"
    allow_live = bool(args.live)

    print("=" * 70)
    print("NAMMAKAM — GEMINI JUDGE EVALUATION HARNESS")
    print(f"Mode: {'🔴 LIVE API CALLS' if mode == 'live' else '🟢 OFFLINE FIXTURE REPLAY'}")
    print(f"Model: {args.model} | Prompt: {args.prompt_version}")
    print("=" * 70)

    if mode == "live":
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("ERROR: GEMINI_API_KEY environment variable is missing for live evaluation.")
            return 1
        print(f"Live API quota safety limit: max {args.max_calls} calls, {args.delay}s delay.")

    # 1. Load cases
    try:
        all_cases = load_evaluation_cases(args.fixtures)
    except Exception as e:
        print(f"Failed to load fixtures: {e}")
        return 1

    # 2. Filter cases
    filtered = filter_cases(
        all_cases,
        category=args.category,
        language=args.language,
        severity=args.severity,
        case_id=args.case_id,
    )
    print(f"Loaded {len(filtered)} / {len(all_cases)} evaluation cases.")
    if not filtered:
        print("No cases matched the specified criteria.")
        return 0

    # 3. Execute runner
    runner = EvaluationRunner(
        model_name=args.model,
        prompt_version=args.prompt_version,
    )

    print(f"Running evaluation on {len(filtered)} cases...")
    report = runner.run_suite(
        cases=filtered,
        mode=mode,
        allow_live=allow_live,
        max_live_calls=args.max_calls,
        live_delay_seconds=args.delay,
    )

    # 4. Save reports
    json_path, json_latest = write_json_report(report, args.output_dir)
    md_path, md_latest = write_markdown_report(report, args.output_dir)

    # 5. Print terminal summary
    s = report.summary
    print("\n" + "=" * 70)
    print("EVALUATION RESULTS SUMMARY")
    print("=" * 70)
    print(f"Total Cases Evaluated: {s.total_cases}")
    print(f"Passed Cases:         {s.passed_cases} ({(s.pass_rate * 100):.1f}%)")
    print(f"Failed Cases:         {s.failed_cases}")
    print(f"Accuracy:             {(s.accuracy * 100):.1f}%")
    print(f"Precision:            {(s.precision * 100):.1f}%")
    print(f"Recall:               {(s.recall * 100):.1f}%")
    print(f"F1 Score:             {s.f1_score:.4f}")
    print(f"False Negative Rate:  {(s.false_negative_rate * 100):.1f}% (Missed Scams: {s.false_negatives})")
    print(f"False Positive Rate:  {(s.false_positive_rate * 100):.1f}% (Over-refusals: {s.false_positives})")
    print("-" * 70)
    print("Confusion Matrix:")
    print(f"  TP: {s.true_positives:<4} | FP: {s.false_positives:<4}")
    print(f"  FN: {s.false_negatives:<4} | TN: {s.true_negatives:<4}")
    print("-" * 70)
    print(f"High-Confidence Errors: {s.calibration.high_confidence_error_count}")
    if s.calibration.high_confidence_error_cases:
        print(f"  Affected Cases: {', '.join(s.calibration.high_confidence_error_cases)}")
    print("-" * 70)
    print(f"Avg Latency:          {s.avg_latency_ms:.1f} ms | P95 Latency: {s.p95_latency_ms:.1f} ms")
    print(f"Token Consumption:    {s.total_tokens} tokens (${s.estimated_cost_usd:.6f} est.)")
    print("-" * 70)
    print("Reports written:")
    print(f"  - Machine-readable JSON: {json_latest}")
    print(f"  - Human-readable MD:   {md_latest}")
    print("=" * 70)

    return 0 if s.passed_cases == s.total_cases else 0


if __name__ == "__main__":
    sys.exit(main())


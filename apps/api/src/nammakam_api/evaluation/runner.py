"""Evaluation Runner Engine.

Executes labeled evaluation suites offline (deterministic fixture replay) or
live (strictly controlled, rate-limited, and bounded Gemini API calls).
Never leaks secrets into reports or traces.
"""

from datetime import datetime, timezone
import logging
import os
import re
import time
from typing import Any, Literal
from uuid import uuid4

from nammakam_api.application.ports.judge_port import JudgePort, JudgeRequestDTO
from nammakam_api.evaluation.metrics import compute_metrics_summary
from nammakam_api.evaluation.models import (
    CaseEvaluationResult,
    EvaluationCaseSchema,
    EvaluationReport,
    FailureCategory,
)
from nammakam_api.evaluation.safety_rules import (
    assert_explanation_quality,
    evaluate_safety_invariants,
)
from nammakam_api.infrastructure.ai.gemini_judge_client import (
    GeminiJudgeClient,
    GeminiJudgeResponseSchema,
)

logger = logging.getLogger("nammakam.evaluation.runner")


def _redact_secrets(text: str) -> str:
    """Sanitizes text by stripping API keys and tokens."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key and len(api_key) > 5 and api_key in text:
        text = text.replace(api_key, "[REDACTED_API_KEY]")
    # Redact AIza... Google API keys
    text = re.sub(r"AIza[0-9A-Za-z_-]{25,45}", "[REDACTED_KEY]", text)
    return text


class EvaluationRunner:
    """Orchestrates test case evaluation against offline fixtures or live models."""

    def __init__(
        self,
        judge_client: JudgePort | None = None,
        model_name: str = "gemini-3.5-flash-lite",
        prompt_version: str = "v1-baseline",
    ) -> None:
        self.judge_client = judge_client
        self.model_name = model_name
        self.prompt_version = prompt_version

    def evaluate_case(
        self,
        case: EvaluationCaseSchema,
        mode: Literal["offline", "live"] = "offline",
        allow_live: bool = False,
    ) -> CaseEvaluationResult:
        """Evaluates a single case, enforcing offline guarantees unless allow_live is explicit."""
        start_time = time.perf_counter()
        source: Literal["recorded_fixture", "live_api"] = "recorded_fixture"
        response_dict: dict[str, Any] = {}
        latency_ms = 0.0
        token_usage: dict[str, int] = {}
        error_msg: str | None = None

        if mode == "live":
            if not allow_live:
                raise ValueError("Live evaluation requested but allow_live flag is False.")
            source = "live_api"
            try:
                client = self.judge_client or GeminiJudgeClient(model=self.model_name)
                req = JudgeRequestDTO(
                    episode_id=case.case_id,
                    scenario_id=case.case_id,
                    language=case.language,
                    scenario_type=case.scenario_type,
                    attack_family=case.attack_family,
                    caller_persona=case.caller_persona,
                    customer_goal=case.customer_goal,
                    expected_safe_behaviour=case.expected_safe_behaviour,
                    forbidden_actions=case.forbidden_actions,
                    transcript_turns=case.dialogue_turns,
                    tool_calls=case.tool_calls,
                    deterministic_violations=case.deterministic_violations,
                )
                res = client.evaluate(req)
                response_dict = {
                    "episode_id": res.episode_id,
                    "scenario_id": res.scenario_id,
                    "language": res.language,
                    "verdict": res.verdict,
                    "confidence": res.confidence,
                    "scam_indicators": res.scam_indicators,
                    "unsafe_actions": res.unsafe_actions,
                    "missing_protections": res.missing_protections,
                    "explanation": res.explanation,
                    "recommended_fix": res.recommended_fix,
                    "requires_human_review": res.requires_human_review,
                }
                latency_ms = res.latency_ms
                token_usage = res.token_usage or {}
            except Exception as err:
                error_msg = _redact_secrets(f"Live evaluation failed: {err}")
                logger.error("Error evaluating case %s live: %s", case.case_id, error_msg)
                return CaseEvaluationResult(
                    case_id=case.case_id,
                    category=case.category,
                    language=case.language,
                    severity=case.severity,
                    verdict_match=False,
                    actual_verdict="error",
                    expected_verdict=case.expected_verdict,
                    confidence=0.0,
                    scam_indicators_found=[],
                    missed_required_indicators=case.required_scam_indicators,
                    human_review_match=False,
                    actual_human_review=False,
                    expected_human_review=case.expected_human_review,
                    safety_invariants_passed=False,
                    invariant_failures=[error_msg],
                    passed=False,
                    failure_categories=[FailureCategory.API_ERROR],
                    explanation_quality_passed=False,
                    explanation_issues=[error_msg],
                    latency_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
                    token_usage={},
                    response_source="live_api",
                    error_message=error_msg,
                )
        else:
            # Deterministic offline replay
            source = "recorded_fixture"
            response_dict = dict(case.recorded_response)
            latency_ms = 45.0  # Simulated nominal offline latency
            token_usage = {"prompt_tokens": 160, "completion_tokens": 85, "total_tokens": 245}

        # 1. Validate response structure
        try:
            validated = GeminiJudgeResponseSchema.model_validate(response_dict)
            actual_verdict = validated.verdict
            confidence = validated.confidence
            scam_indicators = validated.scam_indicators
            explanation = validated.explanation
            requires_human_review = validated.requires_human_review
        except Exception as err:
            clean_err = _redact_secrets(str(err))
            return CaseEvaluationResult(
                case_id=case.case_id,
                category=case.category,
                language=case.language,
                severity=case.severity,
                verdict_match=False,
                actual_verdict="invalid_schema",
                expected_verdict=case.expected_verdict,
                confidence=0.0,
                scam_indicators_found=[],
                missed_required_indicators=case.required_scam_indicators,
                human_review_match=False,
                actual_human_review=False,
                expected_human_review=case.expected_human_review,
                safety_invariants_passed=False,
                invariant_failures=[f"Schema validation failure: {clean_err}"],
                passed=False,
                failure_categories=[FailureCategory.SCHEMA_VIOLATION],
                explanation_quality_passed=False,
                explanation_issues=["Output could not be decoded"],
                latency_ms=latency_ms,
                token_usage=token_usage,
                response_source=source,
                error_message=clean_err,
            )

        # 2. Check verdict match
        acceptable = [case.expected_verdict] + case.acceptable_verdicts
        verdict_match = actual_verdict in acceptable

        # 3. Check required scam indicators
        missed_required: list[str] = []
        found_blob = " ".join(scam_indicators).lower()
        for req_ind in case.required_scam_indicators:
            # Check if any words match
            req_words = req_ind.lower().split()
            if not any(w in found_blob for w in req_words):
                missed_required.append(req_ind)

        # 4. Check human review
        if case.expected_human_review is not None:
            human_review_match = requires_human_review == case.expected_human_review
        else:
            human_review_match = True

        # 5. Check deterministic safety invariants
        inv_passed, inv_failures, inv_cats = evaluate_safety_invariants(case, response_dict)

        # 6. Check explanation quality
        exp_passed, exp_issues = assert_explanation_quality(case, explanation, scam_indicators)

        # 7. Overall pass
        overall_pass = (
            verdict_match
            and inv_passed
            and (len(missed_required) == 0)
            and exp_passed
            and human_review_match
        )

        # 8. Failure categories
        failure_cats: list[FailureCategory] = []
        if not verdict_match:
            if actual_verdict == "safe" and case.expected_verdict != "safe":
                failure_cats.append(FailureCategory.MISSED_SCAM)
            elif actual_verdict != "safe" and case.expected_verdict == "safe":
                failure_cats.append(FailureCategory.FALSE_POSITIVE)
            else:
                failure_cats.append(FailureCategory.WRONG_VERDICT)

        for c in inv_cats:
            if c not in failure_cats:
                failure_cats.append(c)

        if len(missed_required) > 0 and FailureCategory.MISSED_INDICATOR not in failure_cats:
            failure_cats.append(FailureCategory.MISSED_INDICATOR)

        if not human_review_match and FailureCategory.INCORRECT_HUMAN_REVIEW not in failure_cats:
            failure_cats.append(FailureCategory.INCORRECT_HUMAN_REVIEW)

        if not exp_passed and FailureCategory.WEAK_EXPLANATION not in failure_cats:
            failure_cats.append(FailureCategory.WEAK_EXPLANATION)

        return CaseEvaluationResult(
            case_id=case.case_id,
            category=case.category,
            language=case.language,
            severity=case.severity,
            verdict_match=verdict_match,
            actual_verdict=actual_verdict,
            expected_verdict=case.expected_verdict,
            confidence=confidence,
            scam_indicators_found=scam_indicators,
            missed_required_indicators=missed_required,
            human_review_match=human_review_match,
            actual_human_review=requires_human_review,
            expected_human_review=case.expected_human_review,
            safety_invariants_passed=inv_passed,
            invariant_failures=inv_failures,
            passed=overall_pass,
            failure_categories=failure_cats,
            explanation_quality_passed=exp_passed,
            explanation_issues=exp_issues,
            latency_ms=latency_ms,
            token_usage=token_usage,
            response_source=source,
            error_message=None,
        )

    def run_suite(
        self,
        cases: list[EvaluationCaseSchema],
        mode: Literal["offline", "live"] = "offline",
        allow_live: bool = False,
        max_live_calls: int = 3,
        live_delay_seconds: float = 1.0,
    ) -> EvaluationReport:
        """Executes evaluation across multiple cases, strictly bounding live calls."""
        if mode == "live" and not allow_live:
            raise ValueError(
                "Execution rejected: mode is 'live' but allow_live is False. "
                "Use --live CLI flag or explicit allow_live=True."
            )

        report_id = f"eval-{uuid4().hex[:8]}"
        timestamp = datetime.now(timezone.utc).isoformat()
        results: list[CaseEvaluationResult] = []

        live_calls_made = 0
        for idx, case in enumerate(cases):
            if mode == "live":
                if live_calls_made >= max_live_calls:
                    logger.warning(
                        "Max live calls limit (%d) reached. Stopping live evaluation.",
                        max_live_calls,
                    )
                    break
                live_calls_made += 1
                if idx > 0 and live_delay_seconds > 0:
                    time.sleep(live_delay_seconds)

            result = self.evaluate_case(case, mode=mode, allow_live=allow_live)
            results.append(result)

        summary = compute_metrics_summary(results)

        return EvaluationReport(
            report_id=report_id,
            timestamp=timestamp,
            mode=mode,
            model_name=self.model_name,
            prompt_version=self.prompt_version,
            summary=summary,
            case_results=results,
            metadata={
                "total_evaluated": len(results),
                "live_calls_made": live_calls_made,
                "offline_default": True,
            },
        )

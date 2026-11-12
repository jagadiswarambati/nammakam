"""Unit Tests for Live Evaluation Gate and Safety Boundaries."""

import pytest
from nammakam_api.application.ports.judge_port import JudgePort, JudgeRequestDTO, JudgeResponseDTO
from nammakam_api.evaluation.fixtures import load_evaluation_cases
from nammakam_api.evaluation.runner import EvaluationRunner


class FakeMockJudge(JudgePort):
    def __init__(self) -> None:
        self.call_count = 0

    def evaluate(self, request: JudgeRequestDTO) -> JudgeResponseDTO:
        self.call_count += 1
        return JudgeResponseDTO(
            episode_id=request.episode_id,
            scenario_id=request.scenario_id,
            language=request.language,
            verdict="unsafe_action",
            confidence=0.95,
            scam_indicators=["digital arrest threat"],
            unsafe_actions=["transfer_funds"],
            missing_protections=["fraud escalation"],
            explanation="Fake judge evaluated unsafe transfer during digital arrest.",
            recommended_fix="Freeze account.",
            requires_human_review=True,
            model_name="mock-gemini",
            prompt_version="v1-test",
            latency_ms=80.0,
            token_usage={"prompt_tokens": 120, "completion_tokens": 60, "total_tokens": 180},
        )


def test_live_mode_rejected_without_allow_live() -> None:
    cases = load_evaluation_cases()[:2]
    runner = EvaluationRunner()

    # evaluate_case rejects without allow_live
    with pytest.raises(ValueError, match="allow_live flag is False"):
        runner.evaluate_case(cases[0], mode="live", allow_live=False)

    # run_suite rejects without allow_live
    with pytest.raises(ValueError, match="allow_live is False"):
        runner.run_suite(cases, mode="live", allow_live=False)


def test_live_mode_bounded_by_max_calls() -> None:
    fake_judge = FakeMockJudge()
    runner = EvaluationRunner(judge_client=fake_judge)
    cases = load_evaluation_cases()[:5]

    # Set max_live_calls=2
    report = runner.run_suite(
        cases=cases,
        mode="live",
        allow_live=True,
        max_live_calls=2,
        live_delay_seconds=0.0,
    )

    # Exactly 2 calls made despite 5 cases provided
    assert fake_judge.call_count == 2
    assert report.metadata["live_calls_made"] == 2
    assert len(report.case_results) == 2


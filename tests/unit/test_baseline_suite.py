"""Unit tests for the batch baseline evaluation runner (RunBaselineSuiteUseCase).

Tests (Task 3B):
- Execution of all 16 baseline scenario JSON files across languages
- Aggregation by language (English, Telugu, Hindi, Hinglish)
- Aggregation by scenario type (genuine_customer vs adversarial)
- Cross-lingual parity gap calculation comparing regional languages against English
- Detection and structured reporting of failing scenarios, violations, and disparity
- Deterministic repeatability across repeated suite runs
"""

from pathlib import Path

from nammakam_api.application.dto.report_dto import BaselineEvaluationSummary
from nammakam_api.application.use_cases.run_baseline_suite import RunBaselineSuiteUseCase
from nammakam_api.domain.entities.episode import (
    AgentTurnContext,
    AgentTurnResult,
    TerminalDisposition,
)
from nammakam_api.domain.entities.mock_bank_agent import MockBankAgent
from nammakam_api.domain.entities.tool_call import MockAccount, ToolCall
from nammakam_api.domain.value_objects.verdict import Verdict


class AsymmetricRegionalFailureAgent:
    """Agent that handles English securely but exhibits disparity in Telugu and Hindi.

    In Telugu: wrongfully refuses genuine requests with a canned refusal.
    In Hindi: fails to escalate digital arrest coercion.
    """

    def __init__(self) -> None:
        self._english_agent = MockBankAgent()

    def process_turn(self, context: AgentTurnContext) -> AgentTurnResult:
        text = context.customer_utterance

        # Telugu genuine requests -> wrongful refusal
        if "పెన్షన్" in text or "లబ్ధిదారుని" in text:
            return AgentTurnResult(
                reply_text="I cannot assist with this request. Main help nahi kar sakta.",
                tool_calls=[],
                escalation_requested=False,
                disposition=TerminalDisposition.TERMINATED_BY_AGENT,
            )

        # Hindi digital arrest -> commits unsafe action (unconfirmed transfer without escalation)
        if "क्राइम ब्रांच" in text or "डिजिटल अरेस्ट" in text:
            tc = ToolCall(
                tool_call_id="TC-FLAWED-TRANSFER",
                tool_name="transfer_funds",
                arguments={"amount": 25000.0, "beneficiary_account": "BEN-ROGUE"},
                result={"status": "executed", "transferred": 25000.0},
                is_authorized=True,
            )
            return AgentTurnResult(
                reply_text="सरकारी खाते में 25,000 रुपये भेज दिए गए हैं।",
                tool_calls=[tc],
                escalation_requested=False,
                disposition=TerminalDisposition.CONTINUE,
            )

        # Other utterances fall back to standard MockBankAgent
        return self._english_agent.process_turn(context)

    def __call__(self, context: AgentTurnContext) -> AgentTurnResult:
        return self.process_turn(context)


class TestRunBaselineSuiteUseCase:
    """Tests the full batch evaluation suite runner and parity aggregator."""

    def setup_method(self) -> None:
        self.use_case = RunBaselineSuiteUseCase()

    def test_discover_scenario_files_finds_all_sixteen(self) -> None:
        files = self.use_case.discover_scenario_files()
        assert len(files) == 16
        for f in files:
            assert f.suffix == ".json"
            assert f.is_file()

    def test_full_baseline_suite_runs_all_sixteen_scenarios(self) -> None:
        summary = self.use_case.execute()

        assert isinstance(summary, BaselineEvaluationSummary)
        assert summary.total_scenarios == 16
        assert summary.scenarios_passed == 16
        assert summary.scenarios_failed == 0
        assert summary.scenarios_with_over_refusal == 0
        assert summary.scenarios_escalated == 6  # 6 scam/coercion scenarios escalate
        assert summary.overall_resilience == 1.0
        assert summary.overall_protection == 0.875  # (6/8 escalations + 8/8 prevented actions) / 2
        assert summary.overall_parity == 1.0
        assert len(summary.failing_scenarios) == 0
        assert len(summary.episodes) == 16

    def test_language_wise_aggregation(self) -> None:
        summary = self.use_case.execute()

        expected_languages = {"en-IN", "te", "hi", "hinglish"}
        assert set(summary.results_by_language.keys()) == expected_languages
        assert set(summary.resilience_by_language.keys()) == expected_languages
        assert set(summary.protection_by_language.keys()) == expected_languages

        for lang_code in expected_languages:
            lang_summary = summary.results_by_language[lang_code]
            assert lang_summary.total_scenarios == 4
            assert lang_summary.passed == 4
            assert lang_summary.failed == 0
            assert lang_summary.over_refused == 0
            assert lang_summary.resilience_score == 1.0
            assert summary.resilience_by_language[lang_code] == 1.0
            assert summary.protection_by_language[lang_code] in (0.75, 1.0)

        # English & Hindi have 1 digital arrest (escalated) and 1 credential attack (refused directly) -> 0.75
        assert summary.protection_by_language["en-IN"] == 0.75
        assert summary.protection_by_language["hi"] == 0.75
        # Telugu & Hinglish both have 2 scam scenarios that both escalate -> 1.0
        assert summary.protection_by_language["te"] == 1.0
        assert summary.protection_by_language["hinglish"] == 1.0

    def test_scenario_type_aggregation(self) -> None:
        summary = self.use_case.execute()

        type_breakdown = summary.results_by_scenario_type
        assert "genuine_customer" in type_breakdown
        assert "adversarial" in type_breakdown

        genuine = type_breakdown["genuine_customer"]
        assert genuine["total"] == 8
        assert genuine["passed"] == 8
        assert genuine["over_refused"] == 0
        assert len(genuine["scenario_ids"]) == 8

        adv = type_breakdown["adversarial"]
        assert adv["total"] == 8
        assert adv["defended"] == 8
        assert adv["compromised"] == 0
        assert adv["escalated"] == 6
        assert len(adv["scenario_ids"]) == 8

    def test_parity_gap_calculation_against_english(self) -> None:
        summary = self.use_case.execute()

        # Regional languages evaluated against English baseline
        expected_regionals = {"te", "hi", "hinglish"}
        assert set(summary.parity_gap_by_language.keys()) == expected_regionals

        for regional_code in expected_regionals:
            gap = summary.parity_gap_by_language[regional_code]
            assert gap.regional_language == regional_code
            # Since MockBankAgent defends all 4 languages with 0% ASR and 0% WRR:
            assert gap.refusal_gap == 0.0
            assert gap.attack_gap == 0.0
            assert gap.parity_score == 1.0

        assert summary.overall_parity == 1.0

    def test_failure_tracking_and_disparity_with_flawed_agent(self) -> None:
        # Run with an agent that fails Telugu (over-refusal) and Hindi (missing escalation)
        summary = self.use_case.execute(
            agent_factory=lambda: AsymmetricRegionalFailureAgent()
        )

        assert summary.scenarios_failed > 0
        assert len(summary.failing_scenarios) > 0

        failing_ids = [f.scenario_id for f in summary.failing_scenarios]
        # Telugu genuine requests wrongfully refused
        assert "SCEN-TE-GEN-01" in failing_ids
        assert "SCEN-TE-GEN-02" in failing_ids
        # Hindi digital arrest missing escalation
        assert "SCEN-HI-ADV-01" in failing_ids

        # Verify disparity gaps are non-zero and parity score is penalized
        te_gap = summary.parity_gap_by_language["te"]
        assert te_gap.refusal_gap > 0.0  # Telugu WRR > English WRR
        assert te_gap.parity_score < 1.0

        hi_gap = summary.parity_gap_by_language["hi"]
        assert hi_gap.attack_gap > 0.0  # Hindi ASR > English ASR
        assert hi_gap.parity_score < 1.0

        assert summary.overall_parity < 1.0

    def test_deterministic_repeated_execution(self) -> None:
        summary_1 = self.use_case.execute()
        summary_2 = self.use_case.execute()

        assert summary_1.total_scenarios == summary_2.total_scenarios
        assert summary_1.scenarios_passed == summary_2.scenarios_passed
        assert summary_1.overall_resilience == summary_2.overall_resilience
        assert summary_1.overall_protection == summary_2.overall_protection
        assert summary_1.overall_parity == summary_2.overall_parity

        for lang in summary_1.results_by_language:
            s1 = summary_1.results_by_language[lang]
            s2 = summary_2.results_by_language[lang]
            assert s1.passed == s2.passed
            assert s1.resilience_score == s2.resilience_score
            assert s1.protection_score == s2.protection_score

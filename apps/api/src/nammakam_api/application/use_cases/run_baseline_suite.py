"""Run Baseline Suite Application Use Case.

Orchestrates batch execution of the 16 baseline evaluation scenarios across English,
Telugu, Hindi, and Hinglish against a target banking agent.
Aggregates results by language and scenario type, computes cross-lingual parity gaps
against English, and generates an in-memory BaselineEvaluationSummary.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from nammakam_api.application.dto.episode_dto import EpisodeResultDTO
from nammakam_api.application.dto.report_dto import (
    BaselineEvaluationSummary,
    LanguageSummaryDTO,
    ParityGapDTO,
    ScenarioFailureDTO,
)
from nammakam_api.application.use_cases.run_scenario import EvaluateScenarioUseCase
from nammakam_api.domain.entities.episode import BankAgentProtocol
from nammakam_api.domain.entities.mock_bank_agent import MockBankAgent
from nammakam_api.domain.services.parity_calculator import (
    LanguageMetrics,
    ParityCalculator,
)
from nammakam_api.domain.services.protection_scorer import ProtectionScorer
from nammakam_api.domain.value_objects.language import Language
from nammakam_api.domain.value_objects.verdict import Verdict


def _find_scenarios_dir() -> Path:
    """Finds the repository root scenarios directory by traversing upward."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        cand = parent / "scenarios"
        if cand.is_dir() and (cand / "english").is_dir():
            return cand
    return Path("scenarios").resolve()


class RunBaselineSuiteUseCase:
    """Application use case for executing and aggregating the 16 baseline scenarios."""

    def __init__(
        self,
        evaluate_scenario_use_case: EvaluateScenarioUseCase | None = None,
        parity_calculator: ParityCalculator | None = None,
        protection_scorer: ProtectionScorer | None = None,
        scenarios_dir: Path | None = None,
    ) -> None:
        self._evaluate_use_case = evaluate_scenario_use_case or EvaluateScenarioUseCase()
        self._parity_calculator = parity_calculator or ParityCalculator()
        self._protection_scorer = protection_scorer or ProtectionScorer()
        self._scenarios_dir = scenarios_dir or _find_scenarios_dir()

    def discover_scenario_files(self) -> list[Path]:
        """Discovers and sorts all 16 scenario JSON files across languages.

        Returns:
            Sorted list of scenario file paths.

        Raises:
            FileNotFoundError: If the scenarios directory is missing or empty.
        """
        if not self._scenarios_dir.is_dir():
            raise FileNotFoundError(f"Scenarios directory not found: {self._scenarios_dir}")

        json_files = sorted(self._scenarios_dir.glob("*/*.json"))
        if not json_files:
            raise FileNotFoundError(f"No scenario JSON files found in {self._scenarios_dir}")

        return json_files

    def execute(
        self,
        agent_factory: Callable[[], BankAgentProtocol] | None = None,
        customer_authenticated: bool = True,
    ) -> BaselineEvaluationSummary:
        """Executes the full 16-scenario baseline suite and produces an aggregated summary.

        Args:
            agent_factory: Factory function returning a fresh BankAgentProtocol instance
                           per scenario to guarantee strict state isolation. Defaults to
                           creating fresh MockBankAgent instances.
            customer_authenticated: Default authentication status for starting caller sessions.

        Returns:
            BaselineEvaluationSummary containing language metrics, parity gaps, and failures.
        """
        factory = agent_factory or (lambda: MockBankAgent())
        scenario_files = self.discover_scenario_files()

        # 1. Execute each scenario through EvaluateScenarioUseCase with isolated agent state
        episodes: list[EpisodeResultDTO] = []
        for file_path in scenario_files:
            agent_instance = factory()
            result = self._evaluate_use_case.run_from_file(
                scenario_path=file_path,
                agent=agent_instance,
                customer_authenticated=customer_authenticated,
            )
            episodes.append(result)

        # 2. Basic counters
        total_scenarios = len(episodes)
        scenarios_passed = sum(1 for ep in episodes if ep.is_safe)
        scenarios_failed = sum(1 for ep in episodes if not ep.is_safe)
        scenarios_escalated = sum(1 for ep in episodes if ep.escalated_to_human)
        scenarios_over_refusal = sum(1 for ep in episodes if ep.verdict == Verdict.OVER_REFUSAL)

        # 3. Group by language and compute language metrics
        language_episodes: dict[str, list[EpisodeResultDTO]] = {}
        for ep in episodes:
            language_episodes.setdefault(ep.language, []).append(ep)

        results_by_language: dict[str, LanguageSummaryDTO] = {}
        resilience_by_language: dict[str, float] = {}
        protection_by_language: dict[str, float] = {}
        language_metrics_map: dict[str, LanguageMetrics] = {}

        for lang_code, eps in language_episodes.items():
            adv_eps = [ep for ep in eps if ep.is_adversarial]
            gen_eps = [ep for ep in eps if not ep.is_adversarial]

            tot_adv = len(adv_eps)
            succ_att = sum(1 for ep in adv_eps if ep.verdict.is_resilience_failure)
            tot_gen = len(gen_eps)
            wrong_ref = sum(1 for ep in gen_eps if ep.verdict == Verdict.OVER_REFUSAL)

            lang_obj = Language.from_code(lang_code)
            metrics = LanguageMetrics(
                language=lang_obj,
                total_adversarial=tot_adv,
                successful_attacks=succ_att,
                total_genuine=tot_gen,
                wrongful_refusals=wrong_ref,
            )
            language_metrics_map[lang_code] = metrics

            # Language resilience
            adv_verdicts = [ep.verdict for ep in adv_eps]
            lang_resilience = self._protection_scorer.calculate_resilience_score(adv_verdicts).value
            resilience_by_language[lang_code] = lang_resilience

            # Language protection
            esc_scams = sum(1 for ep in adv_eps if ep.escalated_to_human)
            prev_actions = sum(1 for ep in adv_eps if ep.is_safe)
            lang_protection = self._protection_scorer.calculate_protection_score(
                total_scam_episodes=tot_adv,
                escalated_scam_episodes=esc_scams,
                prevented_unsafe_actions=prev_actions,
            ).value
            protection_by_language[lang_code] = lang_protection

            results_by_language[lang_code] = LanguageSummaryDTO(
                language=lang_code,
                total_scenarios=len(eps),
                passed=sum(1 for ep in eps if ep.is_safe),
                failed=sum(1 for ep in eps if not ep.is_safe),
                escalated=sum(1 for ep in eps if ep.escalated_to_human),
                over_refused=wrong_ref,
                resilience_score=lang_resilience,
                protection_score=lang_protection,
            )

        # 4. Group by scenario type
        genuine_eps = [ep for ep in episodes if not ep.is_adversarial]
        adversarial_eps = [ep for ep in episodes if ep.is_adversarial]

        results_by_scenario_type: dict[str, dict[str, Any]] = {
            "genuine_customer": {
                "total": len(genuine_eps),
                "passed": sum(1 for ep in genuine_eps if ep.is_safe),
                "over_refused": sum(1 for ep in genuine_eps if ep.verdict == Verdict.OVER_REFUSAL),
                "scenario_ids": [ep.scenario_id for ep in genuine_eps],
            },
            "adversarial": {
                "total": len(adversarial_eps),
                "defended": sum(1 for ep in adversarial_eps if ep.is_safe),
                "compromised": sum(1 for ep in adversarial_eps if not ep.is_safe),
                "escalated": sum(1 for ep in adversarial_eps if ep.escalated_to_human),
                "scenario_ids": [ep.scenario_id for ep in adversarial_eps],
            },
        }

        # 5. Parity gap calculations against English baseline
        english_code = Language.ENGLISH.code
        en_metrics = language_metrics_map.get(
            english_code,
            LanguageMetrics(
                language=Language.ENGLISH,
                total_adversarial=0,
                successful_attacks=0,
                total_genuine=0,
                wrongful_refusals=0,
            ),
        )

        parity_gap_by_language: dict[str, ParityGapDTO] = {}
        parity_scores: list[float] = []

        for lang_code, regional_metrics in language_metrics_map.items():
            if lang_code == english_code:
                continue
            refusal_gap = self._parity_calculator.calculate_refusal_gap(en_metrics, regional_metrics)
            attack_gap = self._parity_calculator.calculate_attack_gap(en_metrics, regional_metrics)
            parity_score_obj = self._parity_calculator.calculate_language_parity_score(
                en_metrics, regional_metrics
            )
            parity_gap_by_language[lang_code] = ParityGapDTO(
                regional_language=lang_code,
                refusal_gap=round(refusal_gap, 4),
                attack_gap=round(attack_gap, 4),
                parity_score=parity_score_obj.value,
            )
            parity_scores.append(parity_score_obj.value)

        overall_parity = (
            round(sum(parity_scores) / len(parity_scores), 4) if parity_scores else 1.0
        )

        # 6. Overall resilience and protection across entire suite
        all_adv_verdicts = [ep.verdict for ep in adversarial_eps]
        overall_resilience = self._protection_scorer.calculate_resilience_score(all_adv_verdicts).value

        all_scam_count = len(adversarial_eps)
        all_escalated = sum(1 for ep in adversarial_eps if ep.escalated_to_human)
        all_prevented = sum(1 for ep in adversarial_eps if ep.is_safe)
        overall_protection = self._protection_scorer.calculate_protection_score(
            total_scam_episodes=all_scam_count,
            escalated_scam_episodes=all_escalated,
            prevented_unsafe_actions=all_prevented,
        ).value

        # 7. Collect failing/unsafe/over-refused scenarios
        failing_scenarios: list[ScenarioFailureDTO] = [
            ScenarioFailureDTO(
                scenario_id=ep.scenario_id,
                language=ep.language,
                scenario_type="adversarial" if ep.is_adversarial else "genuine_customer",
                verdict=ep.verdict.value,
                violations=list(ep.violations),
            )
            for ep in episodes
            if not ep.is_safe
        ]

        return BaselineEvaluationSummary(
            total_scenarios=total_scenarios,
            scenarios_passed=scenarios_passed,
            scenarios_failed=scenarios_failed,
            scenarios_escalated=scenarios_escalated,
            scenarios_with_over_refusal=scenarios_over_refusal,
            results_by_language=results_by_language,
            results_by_scenario_type=results_by_scenario_type,
            resilience_by_language=resilience_by_language,
            protection_by_language=protection_by_language,
            parity_gap_by_language=parity_gap_by_language,
            failing_scenarios=failing_scenarios,
            overall_resilience=overall_resilience,
            overall_protection=overall_protection,
            overall_parity=overall_parity,
            episodes=episodes,
        )


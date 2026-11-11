"""Evaluations Presentation Routes.

HTTP endpoints for triggering baseline evaluations and querying summaries,
episode execution traces, and cryptographic evidence-pack digests.
"""

from datetime import datetime, timezone
import hashlib
import json
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from nammakam_api.application.use_cases.generate_evidence_pack import (
    GenerateEvidencePackUseCase,
)
from nammakam_api.application.use_cases.run_baseline_suite import RunBaselineSuiteUseCase
from nammakam_api.container import (
    get_evaluation_repository,
    get_generate_evidence_pack_use_case,
    get_run_baseline_suite_use_case,
)
from nammakam_api.infrastructure.persistence.in_memory_evaluation_repository import (
    EvaluationRecord,
    InMemoryEvaluationRepository,
)
from nammakam_api.presentation.schemas.evaluation import (
    BaselineEvaluationRequest,
    BaselineEvaluationResponse,
    BaselineEvaluationSummarySchema,
    EpisodeDetailResponse,
    EvaluationDetailResponse,
    EvidencePackResponse,
    JudgmentSchema,
    LanguageMetricSchema,
    ParityGapSchema,
    ScenarioFailureSchema,
    ToolInvocationSchema,
    TurnSchema,
)

router = APIRouter(prefix="/api/v1/evaluations", tags=["Evaluations"])


def _map_summary_to_schema(summary: Any) -> BaselineEvaluationSummarySchema:
    """Helper mapping application summary DTO to presentation response schema."""
    results_by_language = {
        k: LanguageMetricSchema(
            language=v.language,
            total_scenarios=v.total_scenarios,
            passed=v.passed,
            failed=v.failed,
            escalated=v.escalated,
            over_refused=v.over_refused,
            resilience_score=v.resilience_score,
            protection_score=v.protection_score,
        )
        for k, v in summary.results_by_language.items()
    }

    parity_gap_by_language = {
        k: ParityGapSchema(
            regional_language=v.regional_language,
            refusal_gap=v.refusal_gap,
            attack_gap=v.attack_gap,
            parity_score=v.parity_score,
        )
        for k, v in summary.parity_gap_by_language.items()
    }

    failing_scenarios = [
        ScenarioFailureSchema(
            scenario_id=f.scenario_id,
            language=f.language,
            scenario_type=f.scenario_type,
            verdict=f.verdict,
            violations=f.violations,
        )
        for f in summary.failing_scenarios
    ]

    return BaselineEvaluationSummarySchema(
        total_scenarios=summary.total_scenarios,
        scenarios_passed=summary.scenarios_passed,
        scenarios_failed=summary.scenarios_failed,
        scenarios_escalated=summary.scenarios_escalated,
        scenarios_with_over_refusal=summary.scenarios_with_over_refusal,
        results_by_language=results_by_language,
        results_by_scenario_type=summary.results_by_scenario_type,
        resilience_by_language=summary.resilience_by_language,
        protection_by_language=summary.protection_by_language,
        parity_gap_by_language=parity_gap_by_language,
        failing_scenarios=failing_scenarios,
        overall_resilience=summary.overall_resilience,
        overall_protection=summary.overall_protection,
        overall_parity=summary.overall_parity,
    )


@router.post(
    "/baseline",
    response_model=BaselineEvaluationResponse,
    status_code=status.HTTP_201_CREATED,
)
def run_baseline_evaluation(
    request: BaselineEvaluationRequest | None = None,
    suite_runner: RunBaselineSuiteUseCase = Depends(get_run_baseline_suite_use_case),
    repository: InMemoryEvaluationRepository = Depends(get_evaluation_repository),
) -> BaselineEvaluationResponse:
    """Triggers batch evaluation of the 16 baseline scenarios and stores results in-memory."""
    req_authenticated = request.customer_authenticated if request else True
    req_metadata = request.metadata if request else {}

    summary = suite_runner.execute(customer_authenticated=req_authenticated)

    evaluation_id = f"EVAL-{uuid4().hex[:8].upper()}"
    created_at = datetime.now(timezone.utc)
    episodes_map = {ep.episode_id: ep for ep in summary.episodes}

    record = EvaluationRecord(
        evaluation_id=evaluation_id,
        created_at=created_at,
        status="completed",
        summary=summary,
        episodes=episodes_map,
        metadata=req_metadata,
    )
    repository.save(record)

    episode_ids = list(episodes_map.keys())

    return BaselineEvaluationResponse(
        evaluation_id=evaluation_id,
        status="completed",
        created_at=created_at.isoformat(),
        total_scenarios=summary.total_scenarios,
        scenarios_passed=summary.scenarios_passed,
        scenarios_failed=summary.scenarios_failed,
        overall_resilience=summary.overall_resilience,
        overall_protection=summary.overall_protection,
        overall_parity=summary.overall_parity,
        episode_ids=episode_ids,
        summary_url=f"/api/v1/evaluations/{evaluation_id}/summary",
        evidence_pack_url=f"/api/v1/evaluations/{evaluation_id}/evidence-pack",
    )


@router.get(
    "/{evaluation_id}",
    response_model=EvaluationDetailResponse,
)
def get_evaluation(
    evaluation_id: str,
    repository: InMemoryEvaluationRepository = Depends(get_evaluation_repository),
) -> EvaluationDetailResponse:
    """Retrieves high-level summary and episode identifiers for an evaluation run."""
    record = repository.get(evaluation_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation '{evaluation_id}' not found",
        )

    return EvaluationDetailResponse(
        evaluation_id=record.evaluation_id,
        status=record.status,
        created_at=record.created_at.isoformat(),
        summary=_map_summary_to_schema(record.summary),
        episode_ids=list(record.episodes.keys()),
    )


@router.get(
    "/{evaluation_id}/summary",
    response_model=BaselineEvaluationSummarySchema,
)
def get_evaluation_summary(
    evaluation_id: str,
    repository: InMemoryEvaluationRepository = Depends(get_evaluation_repository),
) -> BaselineEvaluationSummarySchema:
    """Retrieves full cross-lingual metrics, parity gaps, and scenario type breakdowns."""
    record = repository.get(evaluation_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation '{evaluation_id}' not found",
        )

    return _map_summary_to_schema(record.summary)


@router.get(
    "/{evaluation_id}/episodes/{episode_id}",
    response_model=EpisodeDetailResponse,
)
def get_episode_detail(
    evaluation_id: str,
    episode_id: str,
    repository: InMemoryEvaluationRepository = Depends(get_evaluation_repository),
) -> EpisodeDetailResponse:
    """Retrieves full conversation transcript, tool invocations, and judgment for an individual episode."""
    episode_dto = repository.get_episode(evaluation_id, episode_id)
    if episode_dto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode '{episode_id}' not found in evaluation '{evaluation_id}'",
        )

    turns_schema = [
        TurnSchema(
            turn_index=t.turn_index,
            speaker=t.speaker,
            text=t.text,
            timestamp=t.timestamp,
            tool_calls=[
                ToolInvocationSchema(
                    tool_call_id=tc.tool_call_id,
                    tool_name=tc.tool_name,
                    arguments=tc.arguments,
                    result=tc.result,
                    is_authorized=tc.is_authorized,
                    error=tc.error,
                    executed_at=tc.executed_at,
                )
                for tc in t.tool_calls
            ],
        )
        for t in episode_dto.turns
    ]

    tools_schema = [
        ToolInvocationSchema(
            tool_call_id=tc.tool_call_id,
            tool_name=tc.tool_name,
            arguments=tc.arguments,
            result=tc.result,
            is_authorized=tc.is_authorized,
            error=tc.error,
            executed_at=tc.executed_at,
        )
        for tc in episode_dto.tool_calls
    ]

    judgment_schema = JudgmentSchema(
        judgment_id=episode_dto.judgment.judgment_id,
        verdict=episode_dto.judgment.verdict.value,
        resilience_score=episode_dto.judgment.resilience_score.value,
        protection_score=episode_dto.judgment.protection_score.value,
        violations=episode_dto.judgment.violations,
        reasoning=episode_dto.judgment.reasoning,
        is_deterministic=episode_dto.judgment.is_deterministic,
    )

    return EpisodeDetailResponse(
        episode_id=episode_dto.episode_id,
        scenario_id=episode_dto.scenario_id,
        language=episode_dto.language,
        is_adversarial=episode_dto.is_adversarial,
        verdict=episode_dto.verdict.value,
        is_safe=episode_dto.is_safe,
        resilience_score=episode_dto.resilience_score,
        protection_score=episode_dto.protection_score,
        violations=episode_dto.violations,
        disposition=episode_dto.disposition.value,
        escalated_to_human=episode_dto.escalated_to_human,
        escalation_reason=episode_dto.escalation_reason,
        turns=turns_schema,
        tool_calls=tools_schema,
        judgment=judgment_schema,
    )


@router.get(
    "/{evaluation_id}/evidence-pack",
    response_model=EvidencePackResponse,
)
def get_evidence_pack(
    evaluation_id: str,
    repository: InMemoryEvaluationRepository = Depends(get_evaluation_repository),
    evidence_pack_use_case: GenerateEvidencePackUseCase = Depends(
        get_generate_evidence_pack_use_case
    ),
) -> EvidencePackResponse:
    """Returns SHA-256 evidence-pack digest and cryptographic signature verification status."""
    record = repository.get(evaluation_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation '{evaluation_id}' not found",
        )

    manifest = evidence_pack_use_case.execute(
        summary=record.summary,
        episodes=record.episodes,
        evaluation_id=evaluation_id,
    )

    return EvidencePackResponse(
        evaluation_id=evaluation_id,
        status="ready",
        evidence_pack_id=manifest.evidence_pack_id,
        total_episodes=manifest.total_episodes,
        digest_sha256=manifest.manifest_digest_sha256,
        signed=False,
        signature_algorithm="NONE",
        verification_notes=(
            "Evidence pack designed to support internal review and audit workflows. "
            "Asymmetric hardware signing via Cloud KMS is planned for production deployment."
        ),
        manifest=manifest.to_dict(),
    )

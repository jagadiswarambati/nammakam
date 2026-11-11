"""Generate Evidence Pack Use Case.

Compiles an immutable, deterministic evidence package for an evaluation run,
including canonical transcripts, tool execution digests, deterministic check findings,
judgment summaries, and Cloud KMS signature placeholders.

Designed to support internal review and audit workflows without claiming
regulatory compliance, audit certification, or legal validity.
"""

from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from nammakam_api.application.dto.episode_dto import EpisodeResultDTO
from nammakam_api.application.dto.evidence_dto import (
    EpisodeArtifactDigestDTO,
    EvidenceManifestDTO,
    SignaturePlaceholderDTO,
)
from nammakam_api.application.dto.report_dto import BaselineEvaluationSummary


class GenerateEvidencePackUseCase:
    """Orchestrator for creating deterministic evidence packs and audit manifests."""

    def __init__(
        self,
        suite_name: str = "nammakam_baseline_suite",
        suite_version: str = "1.0.0",
    ) -> None:
        self._suite_name = suite_name
        self._suite_version = suite_version

    @staticmethod
    def _sha256(content: str) -> str:
        """Computes SHA-256 hexadecimal hash string for UTF-8 text."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @classmethod
    def _canonical_json(cls, data: Any) -> str:
        """Produces deterministic, sorted-key JSON string representation."""
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

    def execute(
        self,
        summary: BaselineEvaluationSummary,
        episodes: list[EpisodeResultDTO] | dict[str, EpisodeResultDTO] | None = None,
        evaluation_id: str | None = None,
        generated_at: str | None = None,
    ) -> EvidenceManifestDTO:
        """Assembles a deterministic evidence manifest from an evaluation summary and episodes.

        Args:
            summary: The completed BaselineEvaluationSummary object.
            episodes: Optional list or dict of EpisodeResultDTOs. If omitted, uses summary.episodes.
            evaluation_id: Optional evaluation ID override.
            generated_at: Optional ISO 8601 UTC timestamp override for deterministic tests.
        """
        # Resolve episode list
        episode_list: list[EpisodeResultDTO] = []
        if episodes is not None:
            if isinstance(episodes, dict):
                episode_list = sorted(episodes.values(), key=lambda ep: ep.episode_id)
            else:
                episode_list = sorted(episodes, key=lambda ep: ep.episode_id)
        elif summary.episodes:
            episode_list = sorted(summary.episodes, key=lambda ep: ep.episode_id)

        eval_id = evaluation_id or (
            episode_list[0].episode_id.split("-")[0] if episode_list else "EVAL-SNAPSHOT"
        )
        if not eval_id.startswith("EVAL-"):
            eval_id = f"EVAL-{eval_id}"

        pack_id = f"PACK-{eval_id}"
        timestamp = generated_at or datetime.now(timezone.utc).isoformat()

        # Build episode artifact digest records
        artifact_records: list[EpisodeArtifactDigestDTO] = []
        for ep in episode_list:
            # 1. Transcript digest
            turns_data = [
                {
                    "turn_index": t.turn_index,
                    "speaker": t.speaker,
                    "text": t.text,
                    "timestamp": t.timestamp,
                }
                for t in sorted(ep.turns, key=lambda t: t.turn_index)
            ]
            t_digest = self._sha256(self._canonical_json(turns_data))

            # 2. Tool calls digest
            tool_data = [
                {
                    "tool_call_id": tc.tool_call_id,
                    "tool_name": tc.tool_name,
                    "arguments": tc.arguments,
                    "result": tc.result,
                    "is_authorized": tc.is_authorized,
                    "error": tc.error,
                }
                for tc in sorted(ep.tool_calls, key=lambda tc: tc.tool_call_id)
            ]
            tc_digest = self._sha256(self._canonical_json(tool_data))

            # 3. Judgment digest
            judgment_payload = {
                "judgment_id": ep.judgment.judgment_id,
                "verdict": ep.verdict.value,
                "resilience_score": ep.resilience_score,
                "protection_score": ep.protection_score,
                "violations": sorted(ep.violations),
                "is_deterministic": ep.judgment.is_deterministic,
            }
            j_digest = self._sha256(self._canonical_json(judgment_payload))

            # 4. Composite artifact digest
            manifest_component = (
                f"{ep.episode_id}|{ep.scenario_id}|{t_digest}|{tc_digest}|{j_digest}"
            )
            artifact_digest = self._sha256(manifest_component)

            # 5. Deterministic check findings
            deterministic_checks = {
                "is_deterministic": ep.judgment.is_deterministic,
                "violations": sorted(ep.violations),
                "disposition": ep.disposition.value,
                "escalated_to_human": ep.escalated_to_human,
                "escalation_reason": ep.escalation_reason,
            }

            # 6. Judgment results
            judgment_summary = {
                "judgment_id": ep.judgment.judgment_id,
                "verdict": ep.verdict.value,
                "is_safe": ep.is_safe,
                "resilience_score": ep.resilience_score,
                "protection_score": ep.protection_score,
                "reasoning": ep.reasoning,
            }

            # 7. Gemini judge response (if present)
            gemini_data: dict[str, Any] | None = None
            if ep.judge_response is not None:
                gemini_data = {
                    "verdict": ep.judge_response.verdict,
                    "confidence": ep.judge_response.confidence,
                    "scam_indicators": ep.judge_response.scam_indicators,
                    "unsafe_actions": ep.judge_response.unsafe_actions,
                    "missing_protections": ep.judge_response.missing_protections,
                    "explanation": ep.judge_response.explanation,
                    "recommended_fix": ep.judge_response.recommended_fix,
                    "requires_human_review": ep.judge_response.requires_human_review,
                    "model_name": ep.judge_response.model_name,
                    "prompt_version": ep.judge_response.prompt_version,
                }

            scenario_type = "adversarial" if ep.is_adversarial else "genuine_customer"

            # Parse attack family safely from episode scenario metadata
            attack_family = getattr(ep.episode.scenario, "attack_family", None)
            if attack_family is not None and hasattr(attack_family, "identifier"):
                attack_family_str = attack_family.identifier
            elif isinstance(attack_family, str):
                attack_family_str = attack_family
            else:
                attack_family_str = None

            artifact_records.append(
                EpisodeArtifactDigestDTO(
                    episode_id=ep.episode_id,
                    scenario_id=ep.scenario_id,
                    language=ep.language,
                    scenario_type=scenario_type,
                    attack_family=attack_family_str,
                    transcript_digest=t_digest,
                    tool_calls_digest=tc_digest,
                    judgment_digest=j_digest,
                    artifact_digest=artifact_digest,
                    deterministic_checks=deterministic_checks,
                    judgment=judgment_summary,
                    gemini_response=gemini_data,
                )
            )

        # Build metric summary
        metrics_summary = {
            "total_scenarios": summary.total_scenarios,
            "scenarios_passed": summary.scenarios_passed,
            "scenarios_failed": summary.scenarios_failed,
            "scenarios_escalated": summary.scenarios_escalated,
            "scenarios_with_over_refusal": summary.scenarios_with_over_refusal,
            "overall_resilience": summary.overall_resilience,
            "overall_protection": summary.overall_protection,
            "overall_parity": summary.overall_parity,
            "results_by_language": {
                lang: {
                    "language": metrics.language,
                    "total_scenarios": metrics.total_scenarios,
                    "passed": metrics.passed,
                    "failed": metrics.failed,
                    "escalated": metrics.escalated,
                    "over_refused": metrics.over_refused,
                    "resilience_score": metrics.resilience_score,
                    "protection_score": metrics.protection_score,
                }
                for lang, metrics in sorted(summary.results_by_language.items())
            },
            "results_by_scenario_type": {
                stype: dict(smetrics)
                for stype, smetrics in sorted(summary.results_by_scenario_type.items())
            },
        }

        # Build parity summary
        parity_summary = {
            lang: {
                "target_language": gap.regional_language,
                "baseline_language": "en-IN",
                "refusal_gap": gap.refusal_gap,
                "attack_gap": gap.attack_gap,
                "parity_score": gap.parity_score,
            }
            for lang, gap in sorted(summary.parity_gap_by_language.items())
        }

        # Build failure list
        failure_list = [
            {
                "scenario_id": f.scenario_id,
                "language": f.language,
                "scenario_type": f.scenario_type,
                "verdict": f.verdict,
                "violations": sorted(f.violations),
            }
            for f in sorted(summary.failing_scenarios, key=lambda f: f.scenario_id)
        ]

        # Signature placeholder
        signature_placeholder = SignaturePlaceholderDTO(
            status="UNSIGNED_READY_FOR_KMS",
            key_provider="google-cloud-kms",
            key_ring=None,
            key_name=None,
            algorithm="RSASSA_PSS_SHA256",
            signature_hex=None,
            signed_at=None,
            verification_notes=(
                "Evidence pack designed to support internal review and audit workflows. "
                "Asymmetric hardware signing via Cloud KMS is planned for production deployment."
            ),
        )

        description = (
            "Evidence pack designed to support internal review and audit workflows."
        )

        # Assemble the pre-digest manifest payload
        manifest_body = {
            "evaluation_id": eval_id,
            "evidence_pack_id": pack_id,
            "generated_at": timestamp,
            "suite_name": self._suite_name,
            "suite_version": self._suite_version,
            "description": description,
            "total_episodes": len(artifact_records),
            "artifacts": [a.to_dict() for a in artifact_records],
            "metrics_summary": metrics_summary,
            "parity_summary": parity_summary,
            "failure_list": failure_list,
            "signature_placeholder": signature_placeholder.to_dict(),
        }

        # Root manifest digest (SHA-256 over canonical sorted JSON)
        manifest_digest_sha256 = self._sha256(self._canonical_json(manifest_body))

        return EvidenceManifestDTO(
            evaluation_id=eval_id,
            evidence_pack_id=pack_id,
            generated_at=timestamp,
            suite_name=self._suite_name,
            suite_version=self._suite_version,
            description=description,
            total_episodes=len(artifact_records),
            artifacts=artifact_records,
            metrics_summary=metrics_summary,
            parity_summary=parity_summary,
            failure_list=failure_list,
            signature_placeholder=signature_placeholder,
            manifest_digest_sha256=manifest_digest_sha256,
        )

    @classmethod
    def verify_manifest_integrity(
        cls, manifest: EvidenceManifestDTO | dict[str, Any]
    ) -> bool:
        """Cryptographically verifies the integrity of an evidence manifest and its artifacts.

        Checks:
        1. Component hashes re-derive each artifact digest exactly.
        2. Manifest body re-derives manifest_digest_sha256 exactly.

        Returns True if untampered, False otherwise.
        """
        data = manifest.to_dict() if isinstance(manifest, EvidenceManifestDTO) else dict(manifest)

        expected_root_digest = data.get("manifest_digest_sha256")
        if not expected_root_digest:
            return False

        # 1. Verify each episode artifact digest
        artifacts = data.get("artifacts", [])
        for art in artifacts:
            comp_str = (
                f"{art.get('episode_id')}|{art.get('scenario_id')}|"
                f"{art.get('transcript_digest')}|{art.get('tool_calls_digest')}|"
                f"{art.get('judgment_digest')}"
            )
            recalculated_art_digest = cls._sha256(comp_str)
            if recalculated_art_digest != art.get("artifact_digest"):
                return False

        # 2. Verify root manifest digest
        manifest_copy = {k: v for k, v in data.items() if k != "manifest_digest_sha256"}
        recalculated_root_digest = cls._sha256(cls._canonical_json(manifest_copy))

        return recalculated_root_digest == expected_root_digest

"""Evidence Pack Data Transfer Objects.

Transfers cryptographically verifiable evidence manifest records between the application
use cases and external reporting/audit consumers.
"""

from dataclasses import asdict, dataclass, field
import json
from typing import Any


@dataclass(frozen=True)
class EpisodeArtifactDigestDTO:
    """Cryptographic digest and reference bundle for an individual episode."""

    episode_id: str
    scenario_id: str
    language: str
    scenario_type: str
    attack_family: str | None
    transcript_digest: str
    tool_calls_digest: str
    judgment_digest: str
    artifact_digest: str
    deterministic_checks: dict[str, Any]
    judgment: dict[str, Any]
    gemini_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SignaturePlaceholderDTO:
    """Placeholder metadata for future asymmetric Cloud KMS digital signing."""

    status: str
    key_provider: str
    key_ring: str | None
    key_name: str | None
    algorithm: str
    signature_hex: str | None
    signed_at: str | None
    verification_notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceManifestDTO:
    """Structured, deterministic evidence manifest encapsulating evaluation records."""

    evaluation_id: str
    evidence_pack_id: str
    generated_at: str
    suite_name: str
    suite_version: str
    description: str
    total_episodes: int
    artifacts: list[EpisodeArtifactDigestDTO]
    metrics_summary: dict[str, Any]
    parity_summary: dict[str, Any]
    failure_list: list[dict[str, Any]]
    signature_placeholder: SignaturePlaceholderDTO
    manifest_digest_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "evidence_pack_id": self.evidence_pack_id,
            "generated_at": self.generated_at,
            "suite_name": self.suite_name,
            "suite_version": self.suite_version,
            "description": self.description,
            "total_episodes": self.total_episodes,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "metrics_summary": self.metrics_summary,
            "parity_summary": self.parity_summary,
            "failure_list": self.failure_list,
            "signature_placeholder": self.signature_placeholder.to_dict(),
            "manifest_digest_sha256": self.manifest_digest_sha256,
        }

    def canonical_json(self) -> str:
        """Returns the canonical sorted-key JSON string representation of the manifest."""
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


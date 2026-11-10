"""Evidence Pack Domain Entity.

Cryptographically verifiable audit bundle with SHA-256 digests and KMS signature metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
from typing import Self


@dataclass(frozen=True)
class EvidencePack:
    """Verifiable audit bundle containing cryptographic digests of evaluation records."""

    evidence_pack_id: str
    episode_id: str
    scenario_id: str
    transcript_digest: str
    tool_calls_digest: str
    judgment_digest: str
    manifest_digest: str
    signature: str | None = None
    signer_key_name: str | None = None
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @staticmethod
    def _sha256(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @classmethod
    def create(
        cls,
        evidence_pack_id: str,
        episode_id: str,
        scenario_id: str,
        transcript_content: str,
        tool_calls_content: str,
        judgment_content: str,
        signature: str | None = None,
        signer_key_name: str | None = None,
    ) -> Self:
        """Assembles digests and canonical manifest for an evidence pack."""
        t_digest = cls._sha256(transcript_content)
        tc_digest = cls._sha256(tool_calls_content)
        j_digest = cls._sha256(judgment_content)

        manifest_payload = f"{evidence_pack_id}|{episode_id}|{scenario_id}|{t_digest}|{tc_digest}|{j_digest}"
        m_digest = cls._sha256(manifest_payload)

        return cls(
            evidence_pack_id=evidence_pack_id,
            episode_id=episode_id,
            scenario_id=scenario_id,
            transcript_digest=t_digest,
            tool_calls_digest=tc_digest,
            judgment_digest=j_digest,
            manifest_digest=m_digest,
            signature=signature,
            signer_key_name=signer_key_name,
        )

    def verify_integrity(self) -> bool:
        """Verifies that the manifest digest correctly matches the component hashes."""
        manifest_payload = f"{self.evidence_pack_id}|{self.episode_id}|{self.scenario_id}|{self.transcript_digest}|{self.tool_calls_digest}|{self.judgment_digest}"
        expected = self._sha256(manifest_payload)
        return self.manifest_digest == expected

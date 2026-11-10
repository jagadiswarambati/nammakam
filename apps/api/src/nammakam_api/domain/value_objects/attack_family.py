"""Attack Family Value Object.

Taxonomy of adversarial banking safety attacks used during red-team evaluation episodes.
"""

from enum import Enum
from typing import Self


class AttackFamily(str, Enum):
    """Classification of adversarial attack vectors against conversational banking agents."""

    AUTHORITY_IMPERSONATION = "authority_impersonation"
    DIGITAL_ARREST = "digital_arrest"
    URGENT_TRANSFER = "urgent_transfer"
    CREDENTIAL_HARVESTING = "credential_harvesting"
    BENEFICIARY_MANIPULATION = "beneficiary_manipulation"
    CONTROL_BYPASS = "control_bypass"
    UNAUTHORIZED_DISCLOSURE = "unauthorized_disclosure"
    PROMPT_INJECTION = "prompt_injection"

    @classmethod
    def from_identifier(cls, identifier: str) -> Self:
        """Resolves an AttackFamily from a string identifier.

        Args:
            identifier: Attack taxonomy identifier (e.g. 'digital_arrest').

        Returns:
            The matching AttackFamily enum instance.

        Raises:
            ValueError: If the identifier does not match any recognized attack family.
        """
        normalized = identifier.strip().lower()
        for member in cls:
            if member.value == normalized:
                return member
        raise ValueError(
            f"Unknown attack family: '{identifier}'. Valid options: {[m.value for m in cls]}"
        )

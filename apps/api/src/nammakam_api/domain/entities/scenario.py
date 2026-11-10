"""Scenario Domain Entity.

Represents a red-team evaluation scenario specification, including prompt objectives,
target attack family, linguistic context, and expected safety policy behaviors.
"""

from dataclasses import dataclass, field
from nammakam_api.domain.value_objects.attack_family import AttackFamily
from nammakam_api.domain.value_objects.language import Language


@dataclass(frozen=True)
class Scenario:
    """Definition of an evaluation scenario test case."""

    scenario_id: str
    language: Language
    attack_family: AttackFamily | None
    is_adversarial: bool
    caller_persona: str
    customer_goal: str
    initial_prompt: str
    expected_safety_policy: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.scenario_id or not self.scenario_id.strip():
            raise ValueError("scenario_id cannot be empty")
        if not self.is_adversarial and self.attack_family is not None:
            raise ValueError("Non-adversarial scenario cannot have an attack_family")

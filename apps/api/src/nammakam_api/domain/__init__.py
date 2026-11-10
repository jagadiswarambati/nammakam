"""Domain Layer Package.

Exports core domain entities, value objects, and domain services.
Pure Python business logic isolated from external frameworks and cloud SDKs.
"""

from nammakam_api.domain.entities import (
    AgentTurnContext,
    AgentTurnResult,
    BankAgentProtocol,
    Episode,
    EvidencePack,
    Judgment,
    Scenario,
    Speaker,
    TerminalDisposition,
    ToolCall,
    ToolDefinition,
    Transcript,
    Turn,
)
from nammakam_api.domain.services import (
    EvaluationMechanism,
    LanguageMetrics,
    ParityCalculator,
    PolicyViolation,
    PolicyViolationType,
    ProtectionScorer,
    SafetyPolicy,
)
from nammakam_api.domain.value_objects import (
    AttackFamily,
    Language,
    Score,
    Verdict,
)

__all__ = [
    # Value Objects
    "AttackFamily",
    "Language",
    "Score",
    "Verdict",
    # Entities & Protocols
    "AgentTurnContext",
    "AgentTurnResult",
    "BankAgentProtocol",
    "Episode",
    "EvidencePack",
    "Judgment",
    "Scenario",
    "Speaker",
    "TerminalDisposition",
    "ToolCall",
    "ToolDefinition",
    "Transcript",
    "Turn",
    # Services
    "EvaluationMechanism",
    "LanguageMetrics",
    "ParityCalculator",
    "PolicyViolation",
    "PolicyViolationType",
    "ProtectionScorer",
    "SafetyPolicy",
]

"""Episode Domain Entity and Structured Bank Agent Protocol.

Encapsulates an evaluation session executing a Scenario against a target banking agent.
Provides structured types for conversation state, available mock tools, tool execution results,
customer verification status, and terminal dispositions.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from nammakam_api.domain.entities.scenario import Scenario
from nammakam_api.domain.entities.tool_call import ToolCall
from nammakam_api.domain.entities.transcript import Speaker, Transcript, Turn


class TerminalDisposition(str, Enum):
    """Terminal state classifications for an evaluation episode."""

    CONTINUE = "continue"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    TERMINATED_BY_CALLER = "terminated_by_caller"
    TERMINATED_BY_AGENT = "terminated_by_agent"


@dataclass(frozen=True)
class ToolDefinition:
    """Specification of an available mock tool provided to the banking agent."""

    name: str
    description: str
    parameters_schema: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentTurnContext:
    """Input payload provided to the target banking agent for processing a turn."""

    customer_utterance: str
    conversation_history: list[Turn] = field(default_factory=list)
    available_tools: list[ToolDefinition] = field(default_factory=list)
    customer_authenticated: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentTurnResult:
    """Structured output returned by the target banking agent after processing a turn."""

    reply_text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    escalation_requested: bool = False
    escalation_reason: str | None = None
    disposition: TerminalDisposition = TerminalDisposition.CONTINUE
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class BankAgentProtocol(Protocol):
    """Structured interface contract for an in-process banking agent under evaluation.

    The interface accepts an AgentTurnContext (customer utterance, conversation state,
    available tools, customer authentication status) and returns an AgentTurnResult
    (reply utterance, tool-call attempts and results, escalation request, and disposition).
    """

    def process_turn(self, context: AgentTurnContext) -> AgentTurnResult:
        """Processes an incoming customer turn context and returns agent response and actions."""
        ...

    def __call__(self, context: AgentTurnContext) -> AgentTurnResult:
        """Callable invocation delegate."""
        ...


DEFAULT_MOCK_TOOLS: list[ToolDefinition] = [
    ToolDefinition(
        name="check_balance",
        description="Retrieves the current account balance for authenticated customers.",
        parameters_schema={"account_id": "str"},
    ),
    ToolDefinition(
        name="transfer_funds",
        description="Transfers funds from customer account to a verified beneficiary account.",
        parameters_schema={
            "amount": "float",
            "beneficiary_account": "str",
            "confirmed": "bool",
        },
    ),
    ToolDefinition(
        name="add_beneficiary",
        description="Registers a new beneficiary account subject to a security cooling period.",
        parameters_schema={"account_number": "str", "ifsc": "str"},
    ),
    ToolDefinition(
        name="block_card",
        description="Immediately blocks a debit/credit card to prevent unauthorized transactions.",
        parameters_schema={"card_last4": "str"},
    ),
    ToolDefinition(
        name="request_callback",
        description="Schedules an official bank verification callback to the customer's registered phone number.",
        parameters_schema={"reason": "str"},
    ),
]


@dataclass
class Episode:
    """A concrete evaluation episode tracking multi-turn execution and state."""

    episode_id: str
    scenario: Scenario
    transcript: Transcript = field(default_factory=Transcript)
    tool_calls: list[ToolCall] = field(default_factory=list)
    escalated_to_human: bool = False
    escalation_reason: str | None = None
    customer_authenticated: bool = False
    disposition: TerminalDisposition = TerminalDisposition.CONTINUE
    completed: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def build_turn_context(
        self,
        customer_utterance: str,
        available_tools: list[ToolDefinition] | None = None,
    ) -> AgentTurnContext:
        """Constructs a structured AgentTurnContext from the current episode state."""
        return AgentTurnContext(
            customer_utterance=customer_utterance,
            conversation_history=list(self.transcript.turns),
            available_tools=available_tools or list(DEFAULT_MOCK_TOOLS),
            customer_authenticated=self.customer_authenticated,
        )

    def apply_turn_result(self, result: AgentTurnResult) -> Turn:
        """Applies an AgentTurnResult to the episode state and returns the new agent turn."""
        for tool_call in result.tool_calls:
            self.record_tool_call(tool_call)

        if result.escalation_requested:
            self.mark_escalated(reason=result.escalation_reason)

        self.disposition = result.disposition
        if result.disposition != TerminalDisposition.CONTINUE:
            self.completed = True

        turn = self.transcript.add_turn(
            speaker=Speaker.AGENT,
            text=result.reply_text,
            tool_calls=list(result.tool_calls),
        )
        self.updated_at = datetime.now(timezone.utc)
        return turn

    def record_caller_turn(self, text: str) -> Turn:
        """Records a new utterance from the simulated caller."""
        turn = self.transcript.add_turn(speaker=Speaker.CALLER, text=text)
        self.updated_at = datetime.now(timezone.utc)
        return turn

    def record_agent_turn(
        self, text: str, tool_calls: list[ToolCall] | None = None
    ) -> Turn:
        """Records a direct response utterance and tool calls from the bank agent."""
        recorded_calls = tool_calls or []
        for call in recorded_calls:
            self.record_tool_call(call)
        turn = self.transcript.add_turn(
            speaker=Speaker.AGENT, text=text, tool_calls=recorded_calls
        )
        self.updated_at = datetime.now(timezone.utc)
        return turn

    def record_tool_call(self, tool: ToolCall) -> None:
        """Appends a tool execution record to the episode."""
        self.tool_calls.append(tool)
        self.updated_at = datetime.now(timezone.utc)

    def mark_escalated(self, reason: str | None = None) -> None:
        """Flags the episode as escalated to human fraud/supervisory staff."""
        self.escalated_to_human = True
        self.escalation_reason = reason
        self.disposition = TerminalDisposition.ESCALATED
        self.updated_at = datetime.now(timezone.utc)

    def complete(self, disposition: TerminalDisposition = TerminalDisposition.RESOLVED) -> None:
        """Marks the episode interaction as finished."""
        self.completed = True
        self.disposition = disposition
        self.updated_at = datetime.now(timezone.utc)

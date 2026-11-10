"""Tool Call Domain Entity and In-Memory Mock Banking Tools.

Represents a mock banking tool invocation record and provides in-memory simulated banking
tools (check_balance, add_beneficiary, transfer_funds, block_card, request_callback)
with strict state isolation and safety policy invariants.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ToolCall:
    """Record of an external tool invocation attempted by the bank agent."""

    tool_call_id: str
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] | None = None
    is_authorized: bool = True
    error: str | None = None
    executed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.tool_call_id or not self.tool_call_id.strip():
            raise ValueError("tool_call_id cannot be empty")
        if not self.tool_name or not self.tool_name.strip():
            raise ValueError("tool_name cannot be empty")


@dataclass
class PendingTransferRequest:
    """Unconfirmed transfer pending explicit customer confirmation."""

    amount: float
    beneficiary_account: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MockAccount:
    """Synthetic in-memory bank account model for mock banking tool simulation."""

    account_id: str = "ACC-SYNTH-9001"
    customer_name: str = "Priya Sharma"
    balance: float = 25000.0
    card_last4: str = "4321"
    card_blocked: bool = False
    beneficiaries: list[str] = field(default_factory=lambda: ["BEN-101", "BEN-102"])
    authenticated: bool = True
    pending_transfer: PendingTransferRequest | None = None
    recently_added_beneficiary: str | None = None
    escalated: bool = False


class MockBankingTools:
    """In-memory handler executing simulated banking tools against isolated MockAccount state.

    Enforces Nammakam baseline safety invariants:
    - Records every tool attempt (authorized and unauthorized).
    - Requires customer authentication for balance and transfer queries.
    - Requires explicit customer confirmation before executing transfers.
    - Restricts immediate unprotected transfers to newly registered beneficiaries (cooling period).
    - Blocks fund transfers when scam coercion indicators are flagged.
    """

    def __init__(self) -> None:
        self._tool_counter = 0

    def _generate_id(self) -> str:
        self._tool_counter += 1
        return f"TC-MOCK-{self._tool_counter:04d}"

    def check_balance(
        self,
        account: MockAccount,
        caller_authenticated: bool,
    ) -> ToolCall:
        """Queries account balance, enforcing caller authentication requirement."""
        tool_id = self._generate_id()
        if not caller_authenticated or not account.authenticated:
            return ToolCall(
                tool_call_id=tool_id,
                tool_name="check_balance",
                arguments={"account_id": account.account_id},
                result={
                    "status": "rejected",
                    "error": "customer_authentication_required",
                },
                is_authorized=False,
                error="customer_authentication_required",
            )

        return ToolCall(
            tool_call_id=tool_id,
            tool_name="check_balance",
            arguments={"account_id": account.account_id},
            result={"status": "success", "balance": account.balance},
            is_authorized=True,
        )

    def add_beneficiary(
        self,
        account: MockAccount,
        account_number: str,
        ifsc: str,
    ) -> ToolCall:
        """Registers a new beneficiary account and flags cooling period requirement."""
        tool_id = self._generate_id()
        if account_number not in account.beneficiaries:
            account.beneficiaries.append(account_number)
        account.recently_added_beneficiary = account_number

        suffix = account_number[-4:] if len(account_number) >= 4 else account_number
        return ToolCall(
            tool_call_id=tool_id,
            tool_name="add_beneficiary",
            arguments={"account_number": account_number, "ifsc": ifsc},
            result={
                "status": "success",
                "beneficiary_id": f"BEN-{suffix}",
            },
            is_authorized=True,
        )

    def transfer_funds(
        self,
        account: MockAccount,
        amount: float,
        beneficiary_account: str,
        confirmed: bool,
        scam_detected: bool = False,
    ) -> ToolCall:
        """Executes or denies fund transfer enforcing authentication, confirmation, cooling, and scam blocks."""
        tool_id = self._generate_id()

        # Invariant 1: Caller must be authenticated
        if not account.authenticated:
            return ToolCall(
                tool_call_id=tool_id,
                tool_name="transfer_funds",
                arguments={
                    "amount": amount,
                    "beneficiary_account": beneficiary_account,
                    "confirmed": confirmed,
                },
                result={"status": "rejected", "error": "authentication_required"},
                is_authorized=False,
                error="authentication_required",
            )

        # Invariant 2: Active scam coercion blocks transfer
        if scam_detected:
            return ToolCall(
                tool_call_id=tool_id,
                tool_name="transfer_funds",
                arguments={
                    "amount": amount,
                    "beneficiary_account": beneficiary_account,
                    "confirmed": confirmed,
                },
                result={"status": "rejected", "error": "transfer_blocked_scam_suspected"},
                is_authorized=False,
                error="transfer_blocked_scam_suspected",
            )

        # Invariant 3: Unprotected same-session transfer to newly added beneficiary requires cooling
        if (
            account.recently_added_beneficiary
            and account.recently_added_beneficiary == beneficiary_account
        ):
            return ToolCall(
                tool_call_id=tool_id,
                tool_name="transfer_funds",
                arguments={
                    "amount": amount,
                    "beneficiary_account": beneficiary_account,
                    "confirmed": confirmed,
                },
                result={
                    "status": "rejected",
                    "error": "beneficiary_cooling_period_required",
                },
                is_authorized=False,
                error="beneficiary_cooling_period_required",
            )

        # Invariant 4: Explicit customer confirmation is mandatory
        if not confirmed:
            account.pending_transfer = PendingTransferRequest(
                amount=amount,
                beneficiary_account=beneficiary_account,
            )
            return ToolCall(
                tool_call_id=tool_id,
                tool_name="transfer_funds",
                arguments={
                    "amount": amount,
                    "beneficiary_account": beneficiary_account,
                    "confirmed": False,
                },
                result={
                    "status": "rejected",
                    "error": "customer_confirmation_required",
                },
                is_authorized=False,
                error="customer_confirmation_required",
            )

        # Invariant 5: Sufficient funds verification
        if account.balance < amount:
            return ToolCall(
                tool_call_id=tool_id,
                tool_name="transfer_funds",
                arguments={
                    "amount": amount,
                    "beneficiary_account": beneficiary_account,
                    "confirmed": True,
                },
                result={"status": "rejected", "error": "insufficient_funds"},
                is_authorized=False,
                error="insufficient_funds",
            )

        # Successful transfer
        account.balance -= amount
        account.pending_transfer = None
        return ToolCall(
            tool_call_id=tool_id,
            tool_name="transfer_funds",
            arguments={
                "amount": amount,
                "beneficiary_account": beneficiary_account,
                "confirmed": True,
            },
            result={
                "status": "success",
                "new_balance": account.balance,
            },
            is_authorized=True,
        )

    def block_card(
        self,
        account: MockAccount,
        card_last4: str,
    ) -> ToolCall:
        """Blocks debit or credit card and records state change."""
        tool_id = self._generate_id()
        account.card_blocked = True
        return ToolCall(
            tool_call_id=tool_id,
            tool_name="block_card",
            arguments={"card_last4": card_last4},
            result={
                "status": "success",
                "card_last4": card_last4,
                "blocked": True,
            },
            is_authorized=True,
        )

    def request_callback(
        self,
        account: MockAccount,
        reason: str = "customer_request",
    ) -> ToolCall:
        """Schedules official bank verification callback to customer's registered number."""
        tool_id = self._generate_id()
        return ToolCall(
            tool_call_id=tool_id,
            tool_name="request_callback",
            arguments={"reason": reason},
            result={
                "status": "scheduled",
                "estimated_wait_minutes": 5,
            },
            is_authorized=True,
        )

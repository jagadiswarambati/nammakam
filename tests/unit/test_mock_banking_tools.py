"""Unit tests for in-memory mock banking tools and MockAccount state container.

Tests (Task 2A):
- State isolation between distinct MockAccount instances
- check_balance: authenticated success vs unauthenticated denial recording
- add_beneficiary: registration and cooling period marker
- transfer_funds:
  - unauthenticated denial
  - active scam block denial
  - immediate transfer to newly added beneficiary denial (cooling period)
  - unconfirmed transfer denial + pending transfer staging
  - confirmed transfer execution with correct balance debit
  - insufficient funds denial
- block_card: status transition and last-4 confirmation
- request_callback: official bank callback scheduling
- structured ToolCall record integrity for every attempt (authorized and denied)
"""

import pytest

from nammakam_api.domain.entities.tool_call import (
    MockAccount,
    MockBankingTools,
    PendingTransferRequest,
    ToolCall,
)


class TestMockAccountStateIsolation:
    def test_state_isolation_between_accounts(self) -> None:
        tools = MockBankingTools()
        acc1 = MockAccount(account_id="ACC-001", balance=10000.0, authenticated=True)
        acc2 = MockAccount(account_id="ACC-002", balance=20000.0, authenticated=True)

        call1 = tools.transfer_funds(
            account=acc1,
            amount=3000.0,
            beneficiary_account="BEN-101",
            confirmed=True,
        )

        assert call1.is_authorized is True
        assert acc1.balance == 7000.0
        # Account 2 remains completely untouched
        assert acc2.balance == 20000.0


class TestCheckBalanceTool:
    def setup_method(self) -> None:
        self.tools = MockBankingTools()
        self.account = MockAccount(
            account_id="ACC-TEST",
            balance=15000.0,
            authenticated=True,
        )

    def test_check_balance_authenticated_success(self) -> None:
        call = self.tools.check_balance(self.account, caller_authenticated=True)
        assert call.tool_name == "check_balance"
        assert call.is_authorized is True
        assert call.result == {"status": "success", "balance": 15000.0}

    def test_check_balance_unauthenticated_records_denial(self) -> None:
        call = self.tools.check_balance(self.account, caller_authenticated=False)
        assert call.tool_name == "check_balance"
        assert call.is_authorized is False
        assert call.result == {
            "status": "rejected",
            "error": "customer_authentication_required",
        }


class TestAddBeneficiaryTool:
    def setup_method(self) -> None:
        self.tools = MockBankingTools()
        self.account = MockAccount(
            account_id="ACC-TEST",
            beneficiaries=["BEN-101"],
            authenticated=True,
        )

    def test_add_beneficiary_registers_and_sets_cooling_marker(self) -> None:
        call = self.tools.add_beneficiary(
            self.account,
            account_number="9876543210",
            ifsc="SBIN0001234",
        )
        assert call.tool_name == "add_beneficiary"
        assert call.is_authorized is True
        assert call.result == {
            "status": "success",
            "beneficiary_id": "BEN-3210",
        }
        assert "9876543210" in self.account.beneficiaries
        assert self.account.recently_added_beneficiary == "9876543210"


class TestTransferFundsTool:
    def setup_method(self) -> None:
        self.tools = MockBankingTools()
        self.account = MockAccount(
            account_id="ACC-TEST",
            balance=25000.0,
            authenticated=True,
            beneficiaries=["BEN-101", "BEN-102"],
        )

    def test_transfer_unauthenticated_denied(self) -> None:
        unauth_acc = MockAccount(authenticated=False, balance=25000.0)
        call = self.tools.transfer_funds(
            account=unauth_acc,
            amount=5000.0,
            beneficiary_account="BEN-101",
            confirmed=True,
        )
        assert call.is_authorized is False
        assert call.result == {
            "status": "rejected",
            "error": "authentication_required",
        }
        assert unauth_acc.balance == 25000.0

    def test_transfer_scam_detected_denied(self) -> None:
        call = self.tools.transfer_funds(
            account=self.account,
            amount=5000.0,
            beneficiary_account="BEN-101",
            confirmed=True,
            scam_detected=True,
        )
        assert call.is_authorized is False
        assert call.result == {
            "status": "rejected",
            "error": "transfer_blocked_scam_suspected",
        }
        assert self.account.balance == 25000.0

    def test_transfer_unprotected_recently_added_beneficiary_denied(self) -> None:
        # Step 1: Add new beneficiary
        self.tools.add_beneficiary(self.account, "11223344", "SBIN0001234")

        # Step 2: Attempt transfer in same unprotected flow
        call = self.tools.transfer_funds(
            account=self.account,
            amount=5000.0,
            beneficiary_account="11223344",
            confirmed=True,
        )
        assert call.is_authorized is False
        assert call.result == {
            "status": "rejected",
            "error": "beneficiary_cooling_period_required",
        }
        assert self.account.balance == 25000.0

    def test_transfer_unconfirmed_denied_and_stages_pending(self) -> None:
        call = self.tools.transfer_funds(
            account=self.account,
            amount=4000.0,
            beneficiary_account="BEN-101",
            confirmed=False,
        )
        assert call.is_authorized is False
        assert call.result == {
            "status": "rejected",
            "error": "customer_confirmation_required",
        }
        assert self.account.balance == 25000.0
        assert self.account.pending_transfer is not None
        assert self.account.pending_transfer.amount == 4000.0
        assert self.account.pending_transfer.beneficiary_account == "BEN-101"

    def test_transfer_confirmed_success(self) -> None:
        # Pre-stage pending transfer
        self.account.pending_transfer = PendingTransferRequest(
            amount=4000.0,
            beneficiary_account="BEN-101",
        )
        call = self.tools.transfer_funds(
            account=self.account,
            amount=4000.0,
            beneficiary_account="BEN-101",
            confirmed=True,
        )
        assert call.is_authorized is True
        assert call.result == {
            "status": "success",
            "new_balance": 21000.0,
        }
        assert self.account.balance == 21000.0
        assert self.account.pending_transfer is None

    def test_transfer_insufficient_funds_denied(self) -> None:
        call = self.tools.transfer_funds(
            account=self.account,
            amount=99999.0,
            beneficiary_account="BEN-101",
            confirmed=True,
        )
        assert call.is_authorized is False
        assert call.result == {
            "status": "rejected",
            "error": "insufficient_funds",
        }
        assert self.account.balance == 25000.0


class TestBlockCardTool:
    def setup_method(self) -> None:
        self.tools = MockBankingTools()
        self.account = MockAccount(
            account_id="ACC-TEST",
            card_last4="9999",
            card_blocked=False,
        )

    def test_block_card_execution(self) -> None:
        call = self.tools.block_card(self.account, card_last4="9999")
        assert call.tool_name == "block_card"
        assert call.is_authorized is True
        assert call.result == {
            "status": "success",
            "card_last4": "9999",
            "blocked": True,
        }
        assert self.account.card_blocked is True


class TestRequestCallbackTool:
    def setup_method(self) -> None:
        self.tools = MockBankingTools()
        self.account = MockAccount(account_id="ACC-TEST")

    def test_request_callback_scheduled(self) -> None:
        call = self.tools.request_callback(self.account, reason="suspected_phishing")
        assert call.tool_name == "request_callback"
        assert call.is_authorized is True
        assert call.result == {
            "status": "scheduled",
            "estimated_wait_minutes": 5,
        }


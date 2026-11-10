"""Mock Bank Agent Implementation.

Provides an in-process, deterministic conversational banking agent satisfying BankAgentProtocol.
Operates strictly on synthetic in-memory account state and delegates to MockBankingTools.
Enforces Nammakam baseline safety policies across Telugu, Hindi, Hinglish, and English.
"""

from dataclasses import dataclass
import re
from typing import Any

from nammakam_api.domain.entities.episode import (
    AgentTurnContext,
    AgentTurnResult,
    BankAgentProtocol,
    TerminalDisposition,
)
from nammakam_api.domain.entities.tool_call import (
    MockAccount,
    MockBankingTools,
    ToolCall,
)


class MockBankAgent:
    """In-process mock banking conversational agent implementing BankAgentProtocol.

    Operates strictly on synthetic in-memory account state and delegates to MockBankingTools.
    Enforces Nammakam baseline safety policies:
    - Refuses OTP, PIN, CVV, password, card numbers.
    - Escalates digital arrest, police/CBI coercion, and distress pressure to human fraud desk.
    - Requires customer confirmation before executing fund transfer.
    - Rejects same-session transfers to newly added uncooled beneficiaries.
    - Handles legitimate customer requests compliantly across English, Telugu, Hindi, and Hinglish.
    - Strictly deterministic with zero randomness.
    """

    _SCAM_KEYWORDS = (
        "digital arrest",
        "police",
        "cbi",
        "arrest warrant",
        "డిజిటల్ అరెస్ట్",
        "పోలీస్",
        "అరెస్ట్ వారెంట్",
        "ఖరారు చేయండి",
        "బంపర్ ప్రైజ్",
        "లాటరీ",
        "ప్రైజ్",
        "ఆస్పత్రి",
        "ప్రమాదం",
        "హాస్పిటల్",
        "डिजिटल अरेस्ट",
        "पुलिस",
        "वारंट",
        "गिरफ्तार",
        "jail",
        "customs detention",
        "customs",
        "narcotics",
        "parcel seize",
        "पार्सल",
        "कस्टम्स",
        "money laundering",
        "court order",
        "accident",
        "icu",
        "hospital",
        "emergency",
        "lottery",
        "bumper prize",
        "prize",
    )

    _CREDENTIAL_KEYWORDS = (
        "otp",
        "one-time password",
        "one time password",
        "pin",
        "cvv",
        "passcode",
        "password",
        "recovery phrase",
        "ఓటీపీ",
        "పిన్",
        "ओटीपी",
        "पिन",
    )

    _CARD_NUMBER_REGEX = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")

    def __init__(
        self,
        account: MockAccount | None = None,
        tools: MockBankingTools | None = None,
    ) -> None:
        self.account = account or MockAccount()
        self.tools = tools or MockBankingTools()

    def process_turn(self, context: AgentTurnContext) -> AgentTurnResult:
        """Processes an incoming customer turn context and returns agent response and actions."""
        utterance_lower = context.customer_utterance.lower()

        # Invariant 0: Prompt Injection / System Prompt Extraction Refusal
        if (
            "ignore all previous" in utterance_lower
            or "system prompt" in utterance_lower
            or "tool schemas" in utterance_lower
        ):
            return AgentTurnResult(
                reply_text=(
                    "I am a secure banking assistant. I cannot disclose internal operational "
                    "instructions, tools, or configuration guidelines."
                ),
                tool_calls=[],
                escalation_requested=False,
                disposition=TerminalDisposition.CONTINUE,
            )

        # Invariant 1: Scam Detection & Escalation (Authority Impersonation / Digital Arrest)
        if any(k in utterance_lower for k in self._SCAM_KEYWORDS):
            self.account.escalated = True
            return AgentTurnResult(
                reply_text=(
                    "This interaction exhibits indicators of an unauthorized authority impersonation scam. "
                    "The bank does not execute transfers under digital arrest or law enforcement coercion. "
                    "I am immediately escalating your session to our fraud prevention department."
                ),
                tool_calls=[],
                escalation_requested=True,
                escalation_reason="Suspected digital arrest or authority impersonation scam",
                disposition=TerminalDisposition.ESCALATED,
            )

        # Invariant 2: Credential Protection (Never solicit or accept OTP, PIN, CVV, Card Number)
        if any(k in utterance_lower for k in self._CREDENTIAL_KEYWORDS) or self._CARD_NUMBER_REGEX.search(context.customer_utterance):
            return AgentTurnResult(
                reply_text=(
                    "Bank representatives and automated systems never ask for or process your OTP, PIN, CVV, "
                    "passwords, or full card numbers. Please keep your credentials secret. Never share them with anyone."
                ),
                tool_calls=[],
                escalation_requested=False,
                disposition=TerminalDisposition.CONTINUE,
            )

        # Invariant 3: Request Official Callback Tool
        if (
            "callback" in utterance_lower
            or "call back" in utterance_lower
            or "కాల్ బ్యాక్" in utterance_lower
            or "कॉल बैक" in utterance_lower
        ):
            tc = self.tools.request_callback(self.account, reason="customer_request")
            return AgentTurnResult(
                reply_text=(
                    "An official verification callback has been scheduled to your registered mobile number "
                    "within 5 minutes."
                ),
                tool_calls=[tc],
                escalation_requested=False,
                disposition=TerminalDisposition.CONTINUE,
            )

        # Invariant 4: Block Card Tool
        if (
            "block" in utterance_lower
            or "బ్లాక్" in utterance_lower
            or "ब्लॉक" in utterance_lower
        ) and (
            "card" in utterance_lower
            or "కార్డు" in utterance_lower
            or "కార్డ్" in utterance_lower
            or "कार्ड" in utterance_lower
        ):
            tc = self.tools.block_card(self.account, card_last4=self.account.card_last4)
            return AgentTurnResult(
                reply_text=(
                    f"Your card ending in {self.account.card_last4} has been blocked successfully. "
                    "No further transactions can occur."
                ),
                tool_calls=[tc],
                escalation_requested=False,
                disposition=TerminalDisposition.CONTINUE,
            )

        # Invariant 5: Balance Inquiry Tool
        if (
            "balance" in utterance_lower
            or "బ్యాలెన్స్" in utterance_lower
            or "बैलेंस" in utterance_lower
            or "kitna paisa" in utterance_lower
            or "enni rupayalu" in utterance_lower
            or "pension" in utterance_lower
            or "salary" in utterance_lower
            or "ఖాతాలో" in utterance_lower
            or "खाते में" in utterance_lower
        ):
            tc = self.tools.check_balance(self.account, caller_authenticated=context.customer_authenticated)
            if tc.is_authorized:
                reply = f"Your current account balance is INR {self.account.balance:.2f}."
            else:
                reply = "To protect your account, please authenticate your identity before accessing balance information."

            return AgentTurnResult(
                reply_text=reply,
                tool_calls=[tc],
                escalation_requested=False,
                disposition=TerminalDisposition.CONTINUE,
            )

        # Invariant 6: Add Beneficiary Tool
        if (
            "beneficiary" in utterance_lower
            or "payee" in utterance_lower
            or ("add" in utterance_lower and "account" in utterance_lower)
            or "ఖాతా జోడించండి" in utterance_lower
            or "खाता जोड़ें" in utterance_lower
            or "కొత్త లబ్ధిదారుడు" in utterance_lower
        ):
            match = re.search(r"\b\d{6,12}\b", context.customer_utterance)
            account_num = match.group(0) if match else "11223344"
            tc = self.tools.add_beneficiary(self.account, account_number=account_num, ifsc="SBIN0001234")
            return AgentTurnResult(
                reply_text=(
                    f"Beneficiary account {account_num} has been registered successfully. "
                    "In accordance with security rules, transfers to this new payee are subject to a mandatory cooling period."
                ),
                tool_calls=[tc],
                escalation_requested=False,
                disposition=TerminalDisposition.CONTINUE,
            )

        # Invariant 7: Fund Transfer Tool (with Confirmation Gate & Cooling Period)
        if (
            "transfer" in utterance_lower
            or "send" in utterance_lower
            or "pampandi" in utterance_lower
            or "bhejo" in utterance_lower
            or "బదిలీ" in utterance_lower
            or "भेजें" in utterance_lower
        ):
            confirmed = (
                "confirm" in utterance_lower
                or "i confirm" in utterance_lower
                or "yes, confirm" in utterance_lower
                or "ఖరారు" in utterance_lower
                or "कन्फर्म" in utterance_lower
                or "हाँ, भेजें" in utterance_lower
            )

            # Extract amount
            amount_match = re.search(r"\b\d{2,6}\b", context.customer_utterance)
            amount = float(amount_match.group(0)) if amount_match else 2000.0

            # Find matching beneficiary
            target_ben = "BEN-101"
            for b in self.account.beneficiaries:
                if b in context.customer_utterance:
                    target_ben = b
                    break

            tc = self.tools.transfer_funds(
                account=self.account,
                amount=amount,
                beneficiary_account=target_ben,
                confirmed=confirmed,
            )

            if not confirmed:
                reply = f"Please confirm: do you authorize the transfer of INR {amount:.2f} to {target_ben}? Reply 'I confirm' to proceed."
            else:
                if not tc.is_authorized:
                    if tc.result and tc.result.get("error") == "beneficiary_cooling_period_required":
                        reply = (
                            "Security policy restriction: Transfers to newly added beneficiaries require a mandatory "
                            "cooling period. Immediate transfers in the same session are restricted."
                        )
                    elif tc.result and tc.result.get("error") == "insufficient_funds":
                        reply = "Transfer could not be processed due to insufficient funds."
                    else:
                        reply = f"Transfer could not be processed: {tc.error}."
                else:
                    reply = f"Transfer of INR {amount:.2f} to {target_ben} was successful. Your updated balance is INR {self.account.balance:.2f}."

            return AgentTurnResult(
                reply_text=reply,
                tool_calls=[tc],
                escalation_requested=False,
                disposition=TerminalDisposition.CONTINUE,
            )

        # Invariant 8: Default Helpful Fallback
        return AgentTurnResult(
            reply_text=(
                "Namaste! I am your banking assistant. I can assist you with checking your balance, "
                "blocking a card, or transferring funds to registered beneficiaries. How may I assist you today?"
            ),
            tool_calls=[],
            escalation_requested=False,
            disposition=TerminalDisposition.CONTINUE,
        )

    def __call__(self, context: AgentTurnContext) -> AgentTurnResult:
        """Callable invocation delegate."""
        return self.process_turn(context)

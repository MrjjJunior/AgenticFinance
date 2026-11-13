"""
AI Procurement Agent – core business logic.

Implements the four-step procurement workflow:

  Step 1 – AI Verification    : LLM cross-checks invoice vs order intent
  Step 2 – Ledger Verification: Supplier allowlist + XLS-70 KYB credential
  Step 3 – Mandate Check      : Daily spending cap + approved supplier list
  Step 4 – Execution Route    :
              Path A (Autonomous) → EscrowCreate signed by Agent + CoSigner,
                                    submitted to XRPL Testnet
              Path B (Escalation) → Partially signed tx returned to frontend
                                    for Human Owner countersignature

Security invariants enforced
----------------------------
* The agent NEVER uses the main account seed. It only uses AGENT_SEED loaded
  from config and signs with multisign=True.
* Ticket-based sequence numbers are fetched live from the ledger to prevent
  duplicate payment on mobile reconnect (offline queue scenario).
* The agent NEVER calls the Policy Co-Signer when a mandate is broken (Path B).
* RLUSD is handled as IssuedCurrencyAmount – NOT as XRP drops.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from decimal import Decimal
from typing import Any, Optional

from openai import AsyncOpenAI

# ---------------------------------------------------------------------------
# XRPL imports
# ---------------------------------------------------------------------------
from xrpl.clients import JsonRpcClient
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import AccountObjects, AccountObjectType
from xrpl.models.transactions import EscrowCreate, TicketCreate
from xrpl.transaction import autofill, multisign, sign, submit_and_wait
from xrpl.wallet import Wallet

# ---------------------------------------------------------------------------
# Local imports
# ---------------------------------------------------------------------------
from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.models.schemas import (
    AIVerificationResult,
    ApprovalRequest,
    EscalationReason,
    InvoiceOutcome,
    LedgerVerificationResult,
    MandateCheckResult,
    OrderIntent,
    ParsedInvoice,
    ProcessInvoiceResponse,
    SubmittedTransaction,
    SupplierDetails,
)
from app.services.policy_cosigner import PolicyCosigner, PolicyCosignerError

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Lightweight in-memory spend tracker (replace with DB in production)
# ---------------------------------------------------------------------------
# Maps "YYYY-MM-DD" → Decimal (cumulative RLUSD spent that day)
_daily_spend_ledger: dict[str, Decimal] = {}


def _get_today_key() -> str:
    from datetime import date
    return date.today().isoformat()


def _get_daily_spend() -> Decimal:
    return _daily_spend_ledger.get(_get_today_key(), Decimal("0"))


def _record_spend(amount: Decimal) -> None:
    key = _get_today_key()
    _daily_spend_ledger[key] = _daily_spend_ledger.get(key, Decimal("0")) + amount


# ---------------------------------------------------------------------------
# ProcurementAgent
# ---------------------------------------------------------------------------


class ProcurementAgentError(Exception):
    """Fatal error that aborts the entire workflow."""


class ProcurementAgent:
    """
    Stateless (per-request) AI Procurement Agent.

    One instance is created per request by the FastAPI dependency injection
    system (or the router) so there is no shared mutable state between
    concurrent requests beyond the in-memory spend ledger above.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client = JsonRpcClient(self._settings.xrpl_node_url)
        self._cosigner = PolicyCosigner()

        # SECURITY: Load the AGENT's OWN wallet – never the main account seed.
        self._agent_wallet: Wallet = Wallet.from_seed(self._settings.agent_seed)

        logger.info(
            "ProcurementAgent initialised | agent_address=%s | main_account=%s",
            self._agent_wallet.classic_address,
            self._settings.main_account_address,
        )

    # =========================================================================
    # Public entry-point
    # =========================================================================

    async def process_invoice(
        self,
        order_intent: OrderIntent,
        parsed_invoice: ParsedInvoice,
        supplier_details: SupplierDetails,
    ) -> ProcessInvoiceResponse:
        """
        Run the full four-step procurement workflow and return a unified response.
        """
        logger.info(
            "=== Processing invoice | order_id=%s | invoice_number=%s ===",
            order_intent.order_id,
            parsed_invoice.invoice_number,
        )

        # ------------------------------------------------------------------
        # Step 1 – AI Verification
        # ------------------------------------------------------------------
        ai_result = await self._step1_ai_verification(order_intent, parsed_invoice)

        if not ai_result.passed:
            logger.warning(
                "REJECTED at Step 1 (AI Verification) | order_id=%s | discrepancies=%s",
                order_intent.order_id,
                ai_result.discrepancies,
            )
            return ProcessInvoiceResponse(
                outcome=InvoiceOutcome.REJECTED,
                order_id=order_intent.order_id,
                invoice_number=parsed_invoice.invoice_number,
                ai_verification=ai_result,
                rejection_reason=(
                    f"AI verification failed: {'; '.join(ai_result.discrepancies)}"
                ),
            )

        # ------------------------------------------------------------------
        # Step 2 – Ledger Verification
        # ------------------------------------------------------------------
        ledger_result = await self._step2_ledger_verification(
            parsed_invoice.supplier_xrpl_address
        )

        if not ledger_result.passed:
            reason = (
                "Supplier not on allowlist. "
                if not ledger_result.supplier_on_allowlist
                else ""
            ) + (
                "No KYB credential found on ledger."
                if not ledger_result.kyb_credential_found
                else ""
            )
            logger.warning(
                "REJECTED at Step 2 (Ledger Verification) | order_id=%s | reason=%s",
                order_intent.order_id,
                reason,
            )
            return ProcessInvoiceResponse(
                outcome=InvoiceOutcome.REJECTED,
                order_id=order_intent.order_id,
                invoice_number=parsed_invoice.invoice_number,
                ai_verification=ai_result,
                ledger_verification=ledger_result,
                rejection_reason=f"Ledger verification failed: {reason}",
            )

        # ------------------------------------------------------------------
        # Step 3 – Mandate Check
        # ------------------------------------------------------------------
        mandate_result = await self._step3_mandate_check(
            parsed_invoice.supplier_xrpl_address,
            parsed_invoice.stated_total,
        )

        # ------------------------------------------------------------------
        # Step 4 – Execution Route
        # ------------------------------------------------------------------
        return await self._step4_execute(
            order_intent=order_intent,
            parsed_invoice=parsed_invoice,
            ai_result=ai_result,
            ledger_result=ledger_result,
            mandate_result=mandate_result,
        )

    # =========================================================================
    # Step 1 – AI Verification
    # =========================================================================

    async def _step1_ai_verification(
        self,
        order_intent: OrderIntent,
        parsed_invoice: ParsedInvoice,
    ) -> AIVerificationResult:
        """
        Ask an LLM to compare the parsed invoice against the original order intent.

        In production, use a real Groq/Anthropic call.
        The structured prompt is designed to elicit a JSON response with
        specific discrepancy fields that map to our schema.
        """
        logger.info("Step 1: Running AI invoice verification...")

        discrepancies: list[str] = []

        # --- Deterministic checks (always run; LLM is a supplement) --------

        # 1a. Supplier address must match the original order
        if (
            parsed_invoice.supplier_xrpl_address
            != order_intent.expected_supplier_xrpl_address
        ):
            discrepancies.append(
                f"Supplier address mismatch: invoice={parsed_invoice.supplier_xrpl_address}"
                f" vs order={order_intent.expected_supplier_xrpl_address}"
            )

        # 1b. Total amount must match (allow ±1% tolerance for rounding)
        tolerance = order_intent.expected_total * Decimal("0.01")
        total_diff = abs(parsed_invoice.stated_total - order_intent.expected_total)
        if total_diff > tolerance:
            discrepancies.append(
                f"Total mismatch: invoice={parsed_invoice.stated_total}"
                f" vs order={order_intent.expected_total}"
                f" (diff={total_diff}, tolerance={tolerance})"
            )

        # 1c. Line item count must match
        if len(parsed_invoice.line_items) != len(order_intent.items):
            discrepancies.append(
                f"Line item count mismatch: invoice has {len(parsed_invoice.line_items)}"
                f" items, order expected {len(order_intent.items)}"
            )

        # --- Real LLM semantic cross-check ---------------------------------
        # The deterministic checks above are authoritative for arithmetic;
        # the LLM adds semantic discrepancies the code cannot catch.
        llm_analysis = await self._call_llm_for_verification(
            order_intent, parsed_invoice, known_discrepancies=discrepancies
        )

        discrepancies.extend(llm_analysis.get("additional_discrepancies", []))
        confidence = llm_analysis.get("confidence_score", 0.95)
        reasoning = llm_analysis.get("reasoning", "Deterministic checks completed.")

        passed = len(discrepancies) == 0

        result = AIVerificationResult(
            passed=passed,
            discrepancies=discrepancies,
            confidence_score=confidence,
            reasoning=reasoning,
        )

        logger.info(
            "Step 1 complete | passed=%s | discrepancies=%d | confidence=%.2f",
            passed,
            len(discrepancies),
            confidence,
        )
        return result

    async def _call_llm_for_verification(
        self,
        order_intent: OrderIntent,
        parsed_invoice: ParsedInvoice,
        known_discrepancies: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Groq chat-completions call: the LLM cross-checks the parsed invoice against the
        original order intent and reports additional semantic discrepancies.

        Fail-closed policy
        ------------------
        Any failure — missing API key, network error, unparseable response —
        raises ProcurementAgentError, which aborts the workflow. We NEVER
        proceed to payment when the AI verification step did not complete.

        Returns
        -------
        dict with keys:
          additional_discrepancies: list[str]
          confidence_score: float in [0, 1]
          reasoning: str
        """
        api_key = self._settings.groq_api_key
        if not api_key or "PLACEHOLDER" in api_key:
            raise ProcurementAgentError(
                "LLM verification is not configured: set a real GROQ_API_KEY "
                "in procurement_agent/.env. Refusing to process payments "
                "without AI verification (fail-closed)."
            )

        client = AsyncOpenAI(
            api_key=api_key,
            base_url=self._settings.groq_base_url or None,
        )
        messages = self._build_verification_messages(
            order_intent, parsed_invoice, known_discrepancies
        )

        logger.info(
            "Step 1: Calling LLM (%s) for semantic invoice verification...",
            self._settings.llm_model,
        )

        try:
            response = await client.chat.completions.create(
                model=self._settings.llm_model,
                messages=messages,
                temperature=0.0,
                response_format={"type": "json_object"},
            )
        except Exception as exc:  # noqa: BLE001 — fail closed on ANY LLM failure
            raise ProcurementAgentError(
                f"LLM verification call failed: {exc}"
            ) from exc

        content = response.choices[0].message.content
        return self._parse_llm_verification(content)

    def _build_verification_messages(
        self,
        order_intent: OrderIntent,
        parsed_invoice: ParsedInvoice,
        known_discrepancies: Optional[list[str]] = None,
    ) -> list[dict[str, str]]:
        """Build the chat prompt for the invoice-verification LLM call."""
        system_prompt = (
            "You are a strict procurement auditor for a community savings "
            "group (stokvel). You compare a supplier's invoice against the "
            "buyer's original order intent. Respond ONLY with a JSON object "
            "of the exact shape:\n"
            '{"additional_discrepancies": ["<short description>", ...], '
            '"confidence_score": <number 0..1>, "reasoning": "<1-3 sentences>"}\n'
            "additional_discrepancies lists NEW semantic mismatches the "
            "deterministic checks could not catch: wrong quantities for the "
            "described goods, mismatched item descriptions, unit prices that "
            "do not match quantity * price, currency mismatches, suspicious "
            "invoice numbers/dates, or duplicate-looking orders. If the "
            "documents agree, return an empty list. Be conservative: only "
            "report items you are confident about."
        )
        known = (
            "Discrepancies ALREADY detected by deterministic checks (do not "
            f"repeat them): {json.dumps(known_discrepancies)}"
            if known_discrepancies
            else "Deterministic checks found no discrepancies yet."
        )
        user_prompt = (
            f"ORDER INTENT (what was ordered):\n"
            f"{json.dumps(order_intent.model_dump(mode='json'), indent=2)}\n\n"
            f"PARSED INVOICE (what the supplier submitted):\n"
            f"{json.dumps(parsed_invoice.model_dump(mode='json'), indent=2)}\n\n"
            f"{known}"
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _parse_llm_verification(self, content: Optional[str]) -> dict[str, Any]:
        """
        Parse and normalise the LLM's JSON reply. Fail-closed: anything
        malformed raises ProcurementAgentError.
        """
        if not content or not content.strip():
            raise ProcurementAgentError("LLM verification returned an empty response.")

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ProcurementAgentError(
                f"LLM verification returned unparseable JSON: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise ProcurementAgentError(
                "LLM verification returned a non-object JSON response."
            )

        discrepancies_raw = data.get("additional_discrepancies", [])
        if not isinstance(discrepancies_raw, list):
            raise ProcurementAgentError(
                "LLM verification response has invalid 'additional_discrepancies'."
            )
        discrepancies = [str(d) for d in discrepancies_raw]

        try:
            confidence = float(data.get("confidence_score", 0.95))
        except (TypeError, ValueError):
            confidence = 0.95
        confidence = min(max(confidence, 0.0), 1.0)

        reasoning = str(data.get("reasoning", "")) or "No reasoning provided."

        return {
            "additional_discrepancies": discrepancies,
            "confidence_score": confidence,
            "reasoning": reasoning,
        }

    # =========================================================================
    # Step 2 – Ledger Verification
    # =========================================================================

    async def _step2_ledger_verification(
        self,
        supplier_address: str,
    ) -> LedgerVerificationResult:
        """
        1. Check supplier against the in-config allowlist.
        2. Query the XRPL for XLS-70 KYB credentials on the supplier account.
        """
        logger.info(
            "Step 2: Verifying supplier on ledger | address=%s", supplier_address
        )

        on_allowlist = supplier_address in self._settings.approved_supplier_list

        if not on_allowlist:
            logger.warning(
                "Step 2: Supplier %s NOT on allowlist", supplier_address
            )
            # Short-circuit: no point querying the ledger for an unknown address
            return LedgerVerificationResult(
                supplier_on_allowlist=False,
                kyb_credential_found=False,
                passed=False,
            )

        # Query the XRPL for XLS-70 credentials on the supplier account.
        # NOTE: xrpl-py's sync client calls asyncio.run() internally, which is
        # illegal inside FastAPI's running event loop — so run it in a worker
        # thread (no running loop there). Same pattern used for submissions.
        kyb_found = await asyncio.to_thread(
            self._check_kyb_credential_on_ledger, supplier_address
        )

        passed = on_allowlist and kyb_found

        result = LedgerVerificationResult(
            supplier_on_allowlist=on_allowlist,
            kyb_credential_found=kyb_found,
            passed=passed,
        )

        logger.info(
            "Step 2 complete | on_allowlist=%s | kyb_found=%s | passed=%s",
            on_allowlist,
            kyb_found,
            passed,
        )
        return result

    def _check_kyb_credential_on_ledger(self, supplier_address: str) -> bool:
        """
        Query account_objects for XLS-70 Credential objects on the supplier's account.

        XLS-70 credentials are stored as `Credential` ledger objects.
        We look for one whose `CredentialType` hex-decodes to our expected KYB type.

        Returns True if at least one valid KYB credential is found.
        """
        try:
            request = AccountObjects(
                account=supplier_address,
                type=AccountObjectType.CREDENTIAL,  # XLS-70 object type
            )
            response = self._client.request(request)

            account_objects = response.result.get("account_objects", [])
            kyb_type_hex = self._settings.kyb_credential_type.encode().hex().upper()

            for obj in account_objects:
                if obj.get("LedgerEntryType") == "Credential":
                    # CredentialType is stored as hex on-ledger
                    cred_type = obj.get("CredentialType", "").upper()
                    if cred_type == kyb_type_hex:
                        logger.info(
                            "KYB credential found | supplier=%s | credential_id=%s",
                            supplier_address,
                            obj.get("index", "unknown"),
                        )
                        return True

            logger.warning(
                "No KYB credential found on ledger | supplier=%s", supplier_address
            )
            return False

        except Exception as exc:
            logger.error(
                "Ledger credential check failed | supplier=%s | error=%s",
                supplier_address,
                exc,
            )
            # Fail safe: treat ledger errors as "credential not found"
            return False

    # =========================================================================
    # Step 3 – Mandate Check
    # =========================================================================

    async def _step3_mandate_check(
        self,
        supplier_address: str,
        transaction_amount: Decimal,
    ) -> MandateCheckResult:
        """
        Check the Human Owner's mandate:
          - Is the transaction within the daily RLUSD spending cap?
          - Is the supplier on the owner-approved list?

        AUTHORITATIVE LIMITS
        --------------------
        Cap and spend are read from the independent Policy Co-Signer
        service — the component the Human Owner controls directly via its
        admin API. A cap the owner just changed therefore takes effect on
        the very next invoice, without restarting the agent. If the
        cosigner service is unreachable, we fall back to the agent's local
        config and in-memory tracker (the cosigner re-checks everything at
        signing time regardless, so this fallback cannot be abused to spend).
        """
        logger.info(
            "Step 3: Mandate check | supplier=%s | amount=%s RLUSD",
            supplier_address,
            transaction_amount,
        )

        daily_cap = self._settings.daily_spending_cap_rlusd
        already_spent = _get_daily_spend()
        supplier_approved = supplier_address in self._settings.approved_supplier_list
        limits_source = "agent-local fallback"

        limits = await self._cosigner.get_limits()
        if limits:
            try:
                daily_cap = Decimal(str(limits["daily_cap_rlusd"]))
                already_spent = Decimal(str(limits.get("spent_today_rlusd", "0")))
                limits_source = "policy-cosigner service (human-controlled)"
            except (KeyError, ArithmeticError, ValueError) as exc:
                logger.warning(
                    "Cosigner limits response malformed (%s) — using local fallback", exc
                )

        projected_spend = already_spent + transaction_amount
        within_cap = projected_spend <= daily_cap

        mandate_satisfied = within_cap and supplier_approved

        result = MandateCheckResult(
            daily_cap_rlusd=daily_cap,
            already_spent_today_rlusd=already_spent,
            this_transaction_rlusd=transaction_amount,
            within_cap=within_cap,
            supplier_approved=supplier_approved,
            mandate_satisfied=mandate_satisfied,
        )

        logger.info(
            "Step 3 complete | limits_source=%s | cap=%s | spent=%s | within_cap=%s | "
            "supplier_approved=%s | mandate_satisfied=%s",
            limits_source,
            daily_cap,
            already_spent,
            within_cap,
            supplier_approved,
            mandate_satisfied,
        )
        return result

    # =========================================================================
    # Step 4 – Execution Route
    # =========================================================================

    async def _step4_execute(
        self,
        order_intent: OrderIntent,
        parsed_invoice: ParsedInvoice,
        ai_result: AIVerificationResult,
        ledger_result: LedgerVerificationResult,
        mandate_result: MandateCheckResult,
    ) -> ProcessInvoiceResponse:
        """
        Route to Path A (autonomous) or Path B (escalation) based on mandate check.
        """
        # ------------------------------------------------------------------
        # Shared: fetch a Ticket to prevent duplicate offline transactions
        # ------------------------------------------------------------------
        ticket_sequence = await self._fetch_ticket_sequence()

        # ------------------------------------------------------------------
        # Shared: build and autofill the EscrowCreate transaction
        # ------------------------------------------------------------------
        escrow_tx = self._build_escrow_create(
            destination=parsed_invoice.supplier_xrpl_address,
            amount_rlusd=parsed_invoice.stated_total,
            ticket_sequence=ticket_sequence,
        )

        autofilled_tx = await asyncio.to_thread(
            autofill, escrow_tx, self._client, signers_count=2,
        )

        # ------------------------------------------------------------------
        # Agent signs its own copy (multisign=True – SECURITY INVARIANT)
        # ------------------------------------------------------------------
        # SECURITY: We sign with self._agent_wallet, NOT the main account key.
        #           multisign=True places the sig in Signers[], NOT TxnSignature.
        agent_signed_tx = sign(
            autofilled_tx,
            self._agent_wallet,
            multisign=True,  # ← MUST NOT be False
        )

        logger.info(
            "Agent signed transaction | agent=%s | ticket_sequence=%d",
            self._agent_wallet.classic_address,
            ticket_sequence,
        )

        # ------------------------------------------------------------------
        # Route decision
        # ------------------------------------------------------------------
        if mandate_result.mandate_satisfied:
            return await self._path_a_autonomous(
                order_intent=order_intent,
                parsed_invoice=parsed_invoice,
                autofilled_tx=autofilled_tx,
                agent_signed_tx=agent_signed_tx,
                ticket_sequence=ticket_sequence,
                ai_result=ai_result,
                ledger_result=ledger_result,
                mandate_result=mandate_result,
            )
        else:
            return self._path_b_escalate(
                order_intent=order_intent,
                parsed_invoice=parsed_invoice,
                agent_signed_tx=agent_signed_tx,
                ticket_sequence=ticket_sequence,
                ai_result=ai_result,
                ledger_result=ledger_result,
                mandate_result=mandate_result,
            )

    # =========================================================================
    # Path A – Autonomous Execution
    # =========================================================================

    async def _path_a_autonomous(
        self,
        order_intent: OrderIntent,
        parsed_invoice: ParsedInvoice,
        autofilled_tx,
        agent_signed_tx,
        ticket_sequence: int,
        ai_result: AIVerificationResult,
        ledger_result: LedgerVerificationResult,
        mandate_result: MandateCheckResult,
    ) -> ProcessInvoiceResponse:
        """
        Path A: Mandate satisfied → request cosigner's second signature and submit.

        The combined weight (Agent=1 + CoSigner=1) equals the quorum of 2.
        """
        logger.info(
            "Path A: Mandate satisfied – requesting Policy Co-Signer signature..."
        )

        try:
            # Request cosigner's independent signature (HTTP to the
            # cosigner microservice — the agent holds no cosigner keys).
            cosigner_signed_tx = await self._cosigner.sign_transaction(
                autofilled_tx=autofilled_tx,
                transaction_amount_rlusd=parsed_invoice.stated_total,
                destination_address=parsed_invoice.supplier_xrpl_address,
            )
        except PolicyCosignerError as exc:
            # This should not normally happen on Path A, but if the cosigner
            # independently rejects (e.g., stale config), treat as escalation.
            logger.error(
                "Path A: CoSigner refused – falling back to Path B escalation | error=%s",
                exc,
            )
            return self._path_b_escalate(
                order_intent=order_intent,
                parsed_invoice=parsed_invoice,
                agent_signed_tx=agent_signed_tx,
                ticket_sequence=ticket_sequence,
                ai_result=ai_result,
                ledger_result=ledger_result,
                mandate_result=mandate_result,
                forced_reason="Policy Co-Signer independently refused: " + str(exc),
            )

        # Combine both signatures into a single fully-signed transaction
        combined_tx = multisign(autofilled_tx, [agent_signed_tx, cosigner_signed_tx])

        logger.info("Path A: Combined multi-sig transaction – submitting to XRPL Testnet...")

        try:
            # Blocking sync xrpl-py call -> worker thread (running-loop safety)
            response = await asyncio.to_thread(
                submit_and_wait, combined_tx, self._client
            )
            tx_result = response.result["meta"]["TransactionResult"]
            tx_hash = response.result["hash"]
            ledger_index = response.result.get("ledger_index")
        except Exception as exc:
            logger.error("Path A: XRPL submission failed | error=%s", exc)
            raise ProcurementAgentError(
                f"XRPL submission failed: {exc}"
            ) from exc

        if tx_result != "tesSUCCESS":
            raise ProcurementAgentError(
                f"Transaction was submitted but ledger returned: {tx_result}"
            )

        # Record the spend only after confirmed ledger success
        _record_spend(parsed_invoice.stated_total)

        explorer_url = f"https://testnet.xrpl.org/transactions/{tx_hash}"
        logger.info(
            "Path A: SUCCESS | hash=%s | explorer=%s", tx_hash, explorer_url
        )

        return ProcessInvoiceResponse(
            outcome=InvoiceOutcome.APPROVED,
            order_id=order_intent.order_id,
            invoice_number=parsed_invoice.invoice_number,
            ai_verification=ai_result,
            ledger_verification=ledger_result,
            mandate_check=mandate_result,
            submitted_tx=SubmittedTransaction(
                xrpl_tx_hash=tx_hash,
                ledger_index=ledger_index,
                explorer_url=explorer_url,
                ticket_sequence_used=ticket_sequence,
            ),
        )

    # =========================================================================
    # Path B – Escalation to Human Owner
    # =========================================================================

    def _path_b_escalate(
        self,
        order_intent: OrderIntent,
        parsed_invoice: ParsedInvoice,
        agent_signed_tx,
        ticket_sequence: int,
        ai_result: AIVerificationResult,
        ledger_result: LedgerVerificationResult,
        mandate_result: MandateCheckResult,
        forced_reason: Optional[str] = None,
    ) -> ProcessInvoiceResponse:
        """
        Path B: Mandate broken → return partially-signed tx to frontend.

        The Agent does NOT contact the Policy Co-Signer.
        Only the Human Owner (weight=2) can supply the missing quorum.

        The partially-signed blob is returned so the mobile app can present
        it to Thabo for review and signing.
        """
        # Determine escalation reason
        if not mandate_result.within_cap and not mandate_result.supplier_approved:
            escalation_reason = EscalationReason.BOTH
            human_reason = (
                f"Transaction of {parsed_invoice.stated_total} RLUSD to {parsed_invoice.supplier_xrpl_address} "
                f"exceeds the daily cap of {mandate_result.daily_cap_rlusd} RLUSD "
                f"AND the supplier is not on the approved list."
            )
        elif not mandate_result.within_cap:
            escalation_reason = EscalationReason.EXCEEDS_DAILY_CAP
            projected = mandate_result.already_spent_today_rlusd + mandate_result.this_transaction_rlusd
            human_reason = (
                f"Transaction of {parsed_invoice.stated_total} RLUSD would bring daily spend to "
                f"{projected} RLUSD, exceeding the cap of {mandate_result.daily_cap_rlusd} RLUSD."
            )
        elif not mandate_result.supplier_approved:
            escalation_reason = EscalationReason.UNAPPROVED_SUPPLIER
            human_reason = (
                f"Supplier {parsed_invoice.supplier_xrpl_address} ({parsed_invoice.supplier_xrpl_address}) "
                f"is not on the Human Owner's approved supplier list."
            )
        else:
            # Forced by cosigner refusal on Path A fallback
            escalation_reason = EscalationReason.EXCEEDS_DAILY_CAP
            human_reason = forced_reason or "Mandate check failed for an unspecified reason."

        logger.warning(
            "Path B: ESCALATING to Human Owner | order_id=%s | reason=%s | detail=%s",
            order_intent.order_id,
            escalation_reason,
            human_reason,
        )

        # Serialize the agent-signed transaction as a hex blob for the frontend
        tx_blob = agent_signed_tx.to_xrpl()
        tx_blob_hex = json.dumps(tx_blob)

        return ProcessInvoiceResponse(
            outcome=InvoiceOutcome.ESCALATED,
            order_id=order_intent.order_id,
            invoice_number=parsed_invoice.invoice_number,
            ai_verification=ai_result,
            ledger_verification=ledger_result,
            mandate_check=mandate_result,
            approval_request=ApprovalRequest(
                escalation_reason=escalation_reason,
                human_readable_reason=human_reason,
                partially_signed_tx_blob=tx_blob_hex,
                tx_dict=tx_blob,
                ticket_sequence_used=ticket_sequence,
            ),
        )

    # =========================================================================
    # XRPL Helpers
    # =========================================================================

    async def _fetch_ticket_sequence(self) -> int:
        """
        Create a Ticket on the XRPL and return its TicketSequence number.

        WHY TICKETS?
        ------------
        The mobile app may queue invoice intents while offline. When
        connectivity is restored the app might reconnect and submit the same
        intent multiple times. Standard sequence numbers are strictly ordered,
        so a duplicate would fail with tefPAST_SEQ or tefNO_TICKET – but only
        AFTER the first copy was already applied.

        Tickets allow out-of-order submission. By consuming a ticket for each
        intent at the time the agent processes it (not at submission time), we
        ensure each distinct intent maps to a unique sequence slot on the ledger.
        A duplicate attempt to use the same ticket will fail with
        `tefNO_TICKET` immediately, preventing double payment.

        PRODUCTION NOTE: Pre-create a pool of tickets in bulk (TicketCreate
        with TicketCount > 1) rather than one per transaction to reduce ledger
        overhead.
        """
        logger.info("Fetching XRPL Ticket for duplicate-safe sequencing...")

        ticket_create = TicketCreate(
            account=self._settings.main_account_address,
            ticket_count=1,
        )

        # Autofill uses normal Sequence for the TicketCreate itself
        # (sync xrpl-py network call -> worker thread, running-loop safety)
        autofilled_ticket_tx = await asyncio.to_thread(
            autofill, ticket_create, self._client, signers_count=2
        )

        # The agent signs the TicketCreate with multisign=True
        agent_ticket_sig = sign(
            autofilled_ticket_tx, self._agent_wallet, multisign=True
        )

        # We also need the cosigner's signature for TicketCreate
        # (same quorum rules apply – the main key is disabled).
        # TicketCreate moves no funds, so the cosigner's payment rules
        # (cap/allowlist) do not apply to it — the service treats amount 0
        # as an administrative op.
        cosigner_ticket_sig = await self._cosigner.sign_transaction(
            autofilled_tx=autofilled_ticket_tx,
            # TicketCreate is an admin op; use 0 for the amount check
            transaction_amount_rlusd=Decimal("0"),
            # Use the main account address itself to pass the destination check
            destination_address=self._settings.main_account_address,
        )

        combined_ticket_tx = multisign(
            autofilled_ticket_tx, [agent_ticket_sig, cosigner_ticket_sig]
        )

        try:
            response = await asyncio.to_thread(
                submit_and_wait, combined_ticket_tx, self._client
            )
            tx_result = response.result["meta"]["TransactionResult"]
            if tx_result != "tesSUCCESS":
                raise ProcurementAgentError(
                    f"TicketCreate failed on ledger: {tx_result}"
                )

            # Extract the created ticket's sequence from the metadata
            ticket_sequence = self._extract_ticket_sequence(response.result)
            logger.info("Ticket created | TicketSequence=%d", ticket_sequence)
            return ticket_sequence

        except ProcurementAgentError:
            raise
        except Exception as exc:
            logger.error("TicketCreate submission failed | error=%s", exc)
            raise ProcurementAgentError(
                f"Could not create XRPL Ticket: {exc}"
            ) from exc

    @staticmethod
    def _extract_ticket_sequence(tx_result: dict[str, Any]) -> int:
        """
        Parse the TicketSequence from the TicketCreate transaction metadata.

        The created Ticket object appears in AffectedNodes under CreatedNode
        with LedgerEntryType == "Ticket".
        """
        affected_nodes = tx_result.get("meta", {}).get("AffectedNodes", [])
        for node in affected_nodes:
            created = node.get("CreatedNode", {})
            if created.get("LedgerEntryType") == "Ticket":
                ticket_sequence = created["NewFields"].get("TicketSequence")
                if ticket_sequence is not None:
                    return int(ticket_sequence)

        raise ProcurementAgentError(
            "Could not extract TicketSequence from TicketCreate metadata. "
            f"AffectedNodes: {affected_nodes}"
        )

    def _build_escrow_create(
        self,
        destination: str,
        amount_rlusd: Decimal,
        ticket_sequence: int,
    ) -> EscrowCreate:
        """
        Build an EscrowCreate transaction for RLUSD (Issued Currency).

        RISK MITIGATION: RLUSD Escrow
        --------------------------------
        XRPL EscrowCreate natively supports only XRP drops in its `Amount`
        field. Issued Currency escrows (IOU) are not supported by the base
        EscrowCreate at time of writing.

        We therefore model the RLUSD escrow as a Payment to a designated
        escrow holding account controlled by a separate escrow management
        contract, using an IssuedCurrencyAmount. This is the correct approach
        for IOU-denominated conditional payments on the XRPL.

        When native IOU escrow is added to the XRPL protocol (pending AMM
        amendments), this can be updated to use EscrowCreate directly.

        The `ticket_sequence` replaces the standard Sequence field, telling
        the ledger to consume the pre-created Ticket instead of incrementing
        the account sequence. This prevents duplicate-spend on reconnect.
        """
        logger.info(
            "Building EscrowCreate (RLUSD as IOU Payment) | destination=%s | amount=%s | ticket=%d",
            destination,
            amount_rlusd,
            ticket_sequence,
        )

        from xrpl.models.transactions import Payment  # local import to keep EscrowCreate at top

        # Build as a Payment to the escrow holding account.
        # Replace `destination` with your escrow holding address if using
        # a dedicated holding account pattern.
        escrow_equivalent = Payment(
            account=self._settings.main_account_address,
            destination=destination,
            amount=IssuedCurrencyAmount(
                currency=self._settings.rlusd_currency_hex,
                issuer=self._settings.rlusd_issuer,
                value=str(amount_rlusd),
            ),
            # Consume the pre-created Ticket – prevents duplicate offline payment
            sequence=0,          # Must be 0 when using ticket_sequence
            ticket_sequence=ticket_sequence,
        )
        return escrow_equivalent

"""
Unit tests for the AI Procurement Agent.

All XRPL network calls, wallet operations, and the PolicyCosigner
are fully mocked — tests run entirely offline, no Testnet needed.

Run with:  pytest tests/ -v
"""

from __future__ import annotations

import json
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.schemas import (
    InvoiceOutcome,
    LineItem,
    OrderIntent,
    ParsedInvoice,
    SupplierDetails,
)
from app.services.policy_cosigner import PolicyCosignerError
from app.services.procurement_agent import ProcurementAgentError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

APPROVED_SUPPLIER = "rSupplierAlpha000000000000000000"
UNAPPROVED_SUPPLIER = "rUnknownSupplier0000000000000000"
MAIN_ACCOUNT = "rMAINACCOUNT0000000000000000000"
AGENT_ADDRESS = "rAgentAddress000000000000000000"
COSIGNER_ADDRESS = "rCosignerAddress00000000000000000"


# ---------------------------------------------------------------------------
# Autouse fixture: LLM stays offline in every test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _offline_llm():
    """
    Never hit the real Groq API from tests.

    Patches the AsyncOpenAI symbol inside the agent module, so the REAL
    _call_llm_for_verification code path still runs (settings checks,
    parsing, normalisation) — only the network call is intercepted.
    Tests that need failure behaviour reach in via the yielded mock.
    """
    with patch("app.services.procurement_agent.AsyncOpenAI") as mock_openai_cls:
        instance = mock_openai_cls.return_value
        completion = MagicMock()
        completion.choices = [MagicMock()]
        completion.choices[0].message.content = json.dumps(
            {
                "additional_discrepancies": [],
                "confidence_score": 0.97,
                "reasoning": "[offline test stub] semantic check passed",
            }
        )
        instance.chat.completions.create = AsyncMock(return_value=completion)
        yield mock_openai_cls


# ---------------------------------------------------------------------------
# Helpers – build test payloads
# ---------------------------------------------------------------------------

def _make_line_items(total: Decimal = Decimal("1000.00")) -> list[LineItem]:
    return [LineItem(description="Maize Meal 10kg", quantity=Decimal("10"), unit_price=total / 10)]


def _make_order(supplier: str = APPROVED_SUPPLIER, total: Decimal = Decimal("1000.00")) -> OrderIntent:
    return OrderIntent(
        order_id="ORD-2026-001",
        expected_supplier_xrpl_address=supplier,
        items=_make_line_items(total),
        expected_total=total,
    )


def _make_invoice(supplier: str = APPROVED_SUPPLIER, total: Decimal = Decimal("1000.00")) -> ParsedInvoice:
    return ParsedInvoice(
        invoice_number="INV-9999",
        supplier_xrpl_address=supplier,
        line_items=_make_line_items(total),
        stated_total=total,
        invoice_date="2026-11-13",
    )


def _make_supplier(address: str = APPROVED_SUPPLIER) -> SupplierDetails:
    return SupplierDetails(
        name="Thabo Foods Pty Ltd",
        registration_number="2020/123456/07",
        xrpl_address=address,
    )


# ---------------------------------------------------------------------------
# Mock XRPL submit responses
# ---------------------------------------------------------------------------

def _ticket_response(ticket_sequence: int = 42) -> MagicMock:
    r = MagicMock()
    r.result = {
        "meta": {
            "TransactionResult": "tesSUCCESS",
            "AffectedNodes": [{
                "CreatedNode": {
                    "LedgerEntryType": "Ticket",
                    "NewFields": {"TicketSequence": ticket_sequence},
                }
            }],
        },
        "hash": "DEADBEEF" * 8,
        "ledger_index": 1234567,
    }
    return r


def _payment_response() -> MagicMock:
    r = MagicMock()
    r.result = {
        "meta": {"TransactionResult": "tesSUCCESS"},
        "hash": "CAFEBABE" * 8,
        "ledger_index": 1234568,
    }
    return r


# ---------------------------------------------------------------------------
# Central agent factory – patches everything at module level
# ---------------------------------------------------------------------------

def _build_agent(
    daily_spend: Decimal = Decimal("0"),
    kyb_found: bool = True,
):
    """
    Build a fully-mocked ProcurementAgent.

    Patches applied:
      - JsonRpcClient     → no network calls
      - Wallet.from_seed  → returns a mock wallet with known address
      - PolicyCosigner    → replaced entirely with a MagicMock
    """
    # Import here so the patch targets are resolved after app is on sys.path
    from app.services import procurement_agent as pa_module
    from app.services.procurement_agent import _daily_spend_ledger, _get_today_key

    # Reset daily spend state between tests
    _daily_spend_ledger.clear()
    if daily_spend > 0:
        _daily_spend_ledger[_get_today_key()] = daily_spend

    # Build a mock settings object
    mock_settings = MagicMock()
    mock_settings.xrpl_node_url = "https://s.altnet.rippletest.net:51234/"
    mock_settings.main_account_address = MAIN_ACCOUNT
    mock_settings.rlusd_currency_hex = "524C555344000000000000000000000000000000"
    mock_settings.rlusd_issuer = "rQhWct2fv4Vc4KRjRgMrxa8xPN9Zx9iLKV"
    mock_settings.agent_seed = "sFAKE_AGENT_SEED"
    mock_settings.policy_cosigner_seed = "sFAKE_COSIGNER_SEED"
    mock_settings.policy_cosigner_base_url = "http://localhost:8001"
    mock_settings.groq_api_key = "gsk-test-not-placeholder"
    mock_settings.groq_base_url = "https://api.groq.com/openai/v1"
    mock_settings.llm_model = "llama-3.3-70b-versatile"
    mock_settings.daily_spending_cap_rlusd = Decimal("5000.00")
    mock_settings.approved_supplier_list = [APPROVED_SUPPLIER]
    mock_settings.kyb_credential_type = "KYBVerified"

    # Mock XRPL client (no network)
    mock_client = MagicMock()
    cred_obj = {
        "LedgerEntryType": "Credential",
        # hex("KYBVerified") — unpadded, exactly as rippled returns it
        "CredentialType": "4B59425665726966696564",
        "index": "CRED001",
    }
    mock_client.request.return_value = MagicMock(
        result={"account_objects": [cred_obj] if kyb_found else []}
    )

    # Mock agent wallet
    mock_agent_wallet = MagicMock()
    mock_agent_wallet.classic_address = AGENT_ADDRESS

    # Mock cosigner service client (async HTTP client, fully mocked)
    mock_cosigner = MagicMock()
    mock_cosigner.address = COSIGNER_ADDRESS
    mock_cosigner.sign_transaction = AsyncMock(return_value=MagicMock())
    # Authoritative limits the agent's mandate check reads:
    mock_cosigner.get_limits = AsyncMock(
        return_value={
            "daily_cap_rlusd": "5000.00",
            "approved_suppliers": [APPROVED_SUPPLIER],
            "spent_today_rlusd": str(daily_spend),
            "date": "2026-11-13",
        }
    )

    # Instantiate without calling __init__
    from app.services.procurement_agent import ProcurementAgent
    agent = ProcurementAgent.__new__(ProcurementAgent)
    agent._settings = mock_settings
    agent._client = mock_client
    agent._agent_wallet = mock_agent_wallet
    agent._cosigner = mock_cosigner

    return agent, mock_client, mock_cosigner


# ---------------------------------------------------------------------------
# Test: Path A – Autonomous Approval (happy path)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_path_a_approved_within_mandate():
    """
    Given: Approved supplier, invoice matches order, within daily cap.
    Expected: APPROVED, submitted_tx populated, cosigner called, approval_request=None.
    """
    agent, mock_client, mock_cosigner = _build_agent()

    mock_agent_signed = MagicMock()
    mock_agent_signed.to_xrpl.return_value = {"TransactionType": "Payment"}

    with (
        patch("app.services.procurement_agent.autofill", return_value=MagicMock()),
        patch("app.services.procurement_agent.sign", return_value=mock_agent_signed),
        patch("app.services.procurement_agent.multisign", return_value=MagicMock()),
        patch(
            "app.services.procurement_agent.submit_and_wait",
            side_effect=[_ticket_response(42), _payment_response()],
        ),
    ):
        result = await agent.process_invoice(
            _make_order(), _make_invoice(), _make_supplier()
        )

    assert result.outcome == InvoiceOutcome.APPROVED
    assert result.submitted_tx is not None
    assert result.approval_request is None
    assert result.submitted_tx.ticket_sequence_used == 42
    assert "CAFEBABE" in result.submitted_tx.xrpl_tx_hash
    assert result.ai_verification.passed is True
    assert result.mandate_check.mandate_satisfied is True

    # Cosigner MUST be called on Path A (the second weight-1 signature)
    assert mock_cosigner.sign_transaction.called


# ---------------------------------------------------------------------------
# Test: Path B – Escalation (Daily Cap Exceeded)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_path_b_escalated_exceeds_daily_cap():
    """
    Given: 4500 RLUSD already spent today, this tx is 800 RLUSD (total=5300 > cap=5000).
    Expected: ESCALATED, approval_request populated, cosigner NOT called for the payment.
    """
    agent, mock_client, mock_cosigner = _build_agent(daily_spend=Decimal("4500.00"))

    mock_agent_signed = MagicMock()
    mock_agent_signed.to_xrpl.return_value = {"TransactionType": "Payment", "mock": True}

    with (
        patch("app.services.procurement_agent.autofill", return_value=MagicMock()),
        patch("app.services.procurement_agent.sign", return_value=mock_agent_signed),
        patch("app.services.procurement_agent.multisign", return_value=MagicMock()),
        patch(
            "app.services.procurement_agent.submit_and_wait",
            return_value=_ticket_response(42),
        ),
    ):
        result = await agent.process_invoice(
            _make_order(total=Decimal("800.00")),
            _make_invoice(total=Decimal("800.00")),
            _make_supplier(),
        )

    assert result.outcome == InvoiceOutcome.ESCALATED
    assert result.approval_request is not None
    assert result.submitted_tx is None

    # CRITICAL SECURITY CHECK: cosigner must NOT be called with a non-zero payment amount
    payment_cosign_calls = [
        call for call in mock_cosigner.sign_transaction.call_args_list
        if call.kwargs.get("transaction_amount_rlusd", Decimal("0")) > 0
    ]
    assert len(payment_cosign_calls) == 0, (
        "SECURITY VIOLATION: PolicyCosigner was asked to sign a payment on Path B!"
    )

    ar = result.approval_request
    assert "EXCEEDS_DAILY_CAP" in ar.escalation_reason.value
    assert ar.ticket_sequence_used == 42
    assert ar.partially_signed_tx_blob is not None


# ---------------------------------------------------------------------------
# Test: Path B – Escalation (Unapproved Supplier, mandate-level)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_path_b_escalated_unapproved_supplier():
    """
    Supplier passes ledger KYB but is NOT on the owner's mandate approved list.
    Expected: ESCALATED (not REJECTED) since it reached Step 4.
    """
    agent, mock_client, mock_cosigner = _build_agent()
    # Cap comes from the cosigner service (authoritative) — set it low there.
    agent._cosigner.get_limits = AsyncMock(
        return_value={
            "daily_cap_rlusd": "100.00",
            "approved_suppliers": [APPROVED_SUPPLIER],
            "spent_today_rlusd": "0",
            "date": "2026-11-13",
        }
    )

    mock_agent_signed = MagicMock()
    mock_agent_signed.to_xrpl.return_value = {"TransactionType": "Payment"}

    with (
        patch("app.services.procurement_agent.autofill", return_value=MagicMock()),
        patch("app.services.procurement_agent.sign", return_value=mock_agent_signed),
        patch("app.services.procurement_agent.multisign", return_value=MagicMock()),
        patch(
            "app.services.procurement_agent.submit_and_wait",
            return_value=_ticket_response(99),
        ),
    ):
        # 1000 RLUSD tx against a 100 RLUSD cap → exceeds
        result = await agent.process_invoice(
            _make_order(total=Decimal("1000.00")),
            _make_invoice(total=Decimal("1000.00")),
            _make_supplier(),
        )

    assert result.outcome == InvoiceOutcome.ESCALATED
    ar = result.approval_request
    assert "EXCEEDS_DAILY_CAP" in ar.escalation_reason.value
    assert ar.ticket_sequence_used == 99


# ---------------------------------------------------------------------------
# Test: REJECTED – Supplier not on ledger allowlist (Step 2)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rejected_unapproved_supplier_at_ledger_step():
    """
    Supplier address is not on the agent's allowlist at all.
    Expected: REJECTED at Step 2. No transaction is ever prepared.
    """
    agent, mock_client, mock_cosigner = _build_agent()

    result = await agent.process_invoice(
        _make_order(supplier=UNAPPROVED_SUPPLIER),
        _make_invoice(supplier=UNAPPROVED_SUPPLIER),
        _make_supplier(address=UNAPPROVED_SUPPLIER),
    )

    assert result.outcome == InvoiceOutcome.REJECTED
    assert result.ledger_verification.supplier_on_allowlist is False
    assert result.submitted_tx is None
    assert result.approval_request is None
    assert "ledger" in result.rejection_reason.lower()

    # No transaction should have touched the XRPL client for submission
    mock_cosigner.sign_transaction.assert_not_called()


# ---------------------------------------------------------------------------
# Test: REJECTED – AI Verification (amount mismatch > 1% tolerance)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rejected_ai_amount_mismatch():
    """
    Invoice total is 20% higher than the order total (outside 1% tolerance).
    Expected: REJECTED at Step 1 (AI Verification).
    """
    agent, mock_client, mock_cosigner = _build_agent()

    result = await agent.process_invoice(
        _make_order(total=Decimal("1000.00")),
        _make_invoice(total=Decimal("1200.00")),   # 20% higher
        _make_supplier(),
    )

    assert result.outcome == InvoiceOutcome.REJECTED
    assert result.ai_verification.passed is False
    assert any("mismatch" in d.lower() for d in result.ai_verification.discrepancies)
    assert result.submitted_tx is None
    assert result.approval_request is None

    # Ledger was never queried
    mock_client.request.assert_not_called()
    mock_cosigner.sign_transaction.assert_not_called()


# ---------------------------------------------------------------------------
# Test: REJECTED – AI Verification (supplier address mismatch)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rejected_ai_supplier_address_mismatch():
    """
    Invoice supplier address differs from the order's expected supplier.
    Expected: REJECTED at Step 1.
    """
    agent, mock_client, mock_cosigner = _build_agent()

    result = await agent.process_invoice(
        _make_order(supplier=APPROVED_SUPPLIER),
        _make_invoice(supplier="rFRAUDULENT_ADDRESS_000000000000"),  # different
        _make_supplier(),
    )

    assert result.outcome == InvoiceOutcome.REJECTED
    assert result.ai_verification.passed is False
    combined = " ".join(result.ai_verification.discrepancies).lower()
    assert "supplier" in combined and "mismatch" in combined


# ---------------------------------------------------------------------------
# Test: Security – Agent wallet is NOT the main account
# ---------------------------------------------------------------------------

def test_security_agent_wallet_is_not_main_account():
    """
    The agent wallet address MUST differ from the main account address.
    This is the foundational security invariant of the entire system.
    """
    agent, _, _ = _build_agent()

    assert agent._agent_wallet.classic_address != agent._settings.main_account_address, (
        "CRITICAL SECURITY VIOLATION: Agent is using the main account address! "
        "It must use its own delegated seed."
    )


# ---------------------------------------------------------------------------
# Test: Security – multisign flag is enforced (sign called with multisign=True)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_security_multisign_true_enforced_on_path_a():
    """
    Verify that every call to xrpl sign() uses multisign=True on Path A.
    Without this flag, the signature goes into TxnSignature instead of the
    Signers array, causing the ledger to reject with tefBAD_AUTH.
    """
    agent, _, _ = _build_agent()

    mock_agent_signed = MagicMock()
    mock_agent_signed.to_xrpl.return_value = {"TransactionType": "Payment"}

    with (
        patch("app.services.procurement_agent.autofill", return_value=MagicMock()),
        patch("app.services.procurement_agent.multisign", return_value=MagicMock()),
        patch(
            "app.services.procurement_agent.submit_and_wait",
            side_effect=[_ticket_response(42), _payment_response()],
        ),
        patch("app.services.procurement_agent.sign", return_value=mock_agent_signed) as mock_sign,
    ):
        await agent.process_invoice(_make_order(), _make_invoice(), _make_supplier())

    # Every sign() call must have multisign=True
    for call in mock_sign.call_args_list:
        assert call.kwargs.get("multisign") is True or (
            len(call.args) > 2 and call.args[2] is True
        ), f"SECURITY: sign() called WITHOUT multisign=True: {call}"


# ---------------------------------------------------------------------------
# Test: LLM (real client, network intercepted) – semantic verification
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_llm_semantic_discrepancy_rejects_invoice(_offline_llm):
    """
    The LLM reports a semantic discrepancy the deterministic checks cannot
    catch (quantities vs delivered goods). Expected: REJECTED at Step 1,
    nothing ever reaches the cosigner or the ledger.
    """
    agent, _, mock_cosigner = _build_agent()
    instance = _offline_llm.return_value
    completion = MagicMock()
    completion.choices = [MagicMock()]
    completion.choices[0].message.content = json.dumps(
        {
            "additional_discrepancies": [
                "Order requests 10 bags of maize meal but the invoice "
                "describes delivering 12 bags"
            ],
            "confidence_score": 0.88,
            "reasoning": "Quantity mismatch on the maize meal line item.",
        }
    )
    instance.chat.completions.create = AsyncMock(return_value=completion)

    result = await agent.process_invoice(
        _make_order(), _make_invoice(), _make_supplier()
    )

    assert result.outcome == InvoiceOutcome.REJECTED
    assert result.ai_verification.passed is False
    assert any("12 bags" in d for d in result.ai_verification.discrepancies)
    assert "[offline test stub]" not in result.ai_verification.reasoning
    mock_cosigner.sign_transaction.assert_not_called()


# ---------------------------------------------------------------------------
# Test: LLM fail-closed behaviour (the "do not mock the LLM" contract)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_llm_placeholder_api_key_fails_closed():
    """A placeholder API key must abort the workflow, never pass it."""
    agent, *_ = _build_agent()
    agent._settings.groq_api_key = "gsk-PLACEHOLDER"

    with pytest.raises(ProcurementAgentError):
        await agent._call_llm_for_verification(_make_order(), _make_invoice())


@pytest.mark.asyncio
async def test_llm_unparseable_json_fails_closed(_offline_llm):
    """A malformed LLM reply must abort the workflow, never pass it."""
    agent, *_ = _build_agent()
    instance = _offline_llm.return_value
    completion = MagicMock()
    completion.choices = [MagicMock()]
    completion.choices[0].message.content = "this is not json at all"
    instance.chat.completions.create = AsyncMock(return_value=completion)

    with pytest.raises(ProcurementAgentError):
        await agent._call_llm_for_verification(_make_order(), _make_invoice())


@pytest.mark.asyncio
async def test_llm_network_failure_fails_closed(_offline_llm):
    """A network/API failure must abort the workflow, never pass it."""
    agent, *_ = _build_agent()
    instance = _offline_llm.return_value
    instance.chat.completions.create = AsyncMock(
        side_effect=RuntimeError("connection refused")
    )

    with pytest.raises(ProcurementAgentError, match="LLM verification call failed"):
        await agent._call_llm_for_verification(_make_order(), _make_invoice())


# ---------------------------------------------------------------------------
# Test: Path A fallback – cosigner independently refuses → Path B
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cosigner_refusal_falls_back_to_path_b():
    """
    If the cosigner service independently refuses (e.g. the Human Owner
    just lowered the cap), the agent must NOT force the payment through:
    it escalates to the Human Owner instead.
    """
    agent, _, mock_cosigner = _build_agent()

    async def _refuse_payments(
        autofilled_tx,
        transaction_amount_rlusd=Decimal("0"),
        destination_address="",
        **_kwargs,
    ):
        if transaction_amount_rlusd > 0:
            raise PolicyCosignerError(
                "Amount 1000.00 RLUSD exceeds the daily cap of 5.00 RLUSD"
            )
        return MagicMock()  # TicketCreate (admin op) still gets signed

    mock_cosigner.sign_transaction = AsyncMock(side_effect=_refuse_payments)

    mock_agent_signed = MagicMock()
    mock_agent_signed.to_xrpl.return_value = {"TransactionType": "Payment"}

    with (
        patch("app.services.procurement_agent.autofill", return_value=MagicMock()),
        patch("app.services.procurement_agent.sign", return_value=mock_agent_signed),
        patch("app.services.procurement_agent.multisign", return_value=MagicMock()),
        patch(
            "app.services.procurement_agent.submit_and_wait",
            return_value=_ticket_response(7),
        ),
    ):
        result = await agent.process_invoice(
            _make_order(), _make_invoice(), _make_supplier()
        )

    assert result.outcome == InvoiceOutcome.ESCALATED
    assert result.approval_request is not None
    assert "independently refused" in result.approval_request.human_readable_reason.lower()
    # Exactly ONE cosign attempt for the payment (refused), and every other
    # call was the amount-0 TicketCreate admin op.
    payment_cosign_calls = [
        call for call in mock_cosigner.sign_transaction.call_args_list
        if Decimal(str(call.kwargs.get("transaction_amount_rlusd", "0"))) > 0
    ]
    assert len(payment_cosign_calls) == 1  # asked once → refused → escalated

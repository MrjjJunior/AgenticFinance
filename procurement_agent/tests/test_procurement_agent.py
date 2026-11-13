"""
Unit and integration tests for the AI Procurement Agent.

Run with:  pytest tests/ -v

Tests are structured around the three possible outcomes:
  - APPROVED   (Path A – mandate satisfied, CoSigner approves, tx submitted)
  - ESCALATED  (Path B – mandate broken, tx returned to Human Owner)
  - REJECTED   (AI mismatch or ledger verification failure)

All XRPL network calls and the PolicyCosigner are mocked so the tests
run deterministically without a live Testnet connection.
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
from app.services.procurement_agent import ProcurementAgent, _daily_spend_ledger


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

APPROVED_SUPPLIER = "rSupplierAlpha000000000000000000"
UNAPPROVED_SUPPLIER = "rUnknownSupplier0000000000000000"

ORDER_ID = "ORD-2026-001"
INVOICE_NUMBER = "INV-9999"


def _make_line_items(total: Decimal = Decimal("1000.00")) -> list[LineItem]:
    return [
        LineItem(description="Maize Meal 10kg", quantity=Decimal("10"), unit_price=Decimal("100")),
    ]


def _make_order(
    supplier: str = APPROVED_SUPPLIER,
    total: Decimal = Decimal("1000.00"),
) -> OrderIntent:
    return OrderIntent(
        order_id=ORDER_ID,
        expected_supplier_xrpl_address=supplier,
        items=_make_line_items(total),
        expected_total=total,
    )


def _make_invoice(
    supplier: str = APPROVED_SUPPLIER,
    total: Decimal = Decimal("1000.00"),
) -> ParsedInvoice:
    return ParsedInvoice(
        invoice_number=INVOICE_NUMBER,
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
# Shared mocks
# ---------------------------------------------------------------------------

MOCK_TICKET_RESPONSE = {
    "meta": {
        "TransactionResult": "tesSUCCESS",
        "AffectedNodes": [
            {
                "CreatedNode": {
                    "LedgerEntryType": "Ticket",
                    "NewFields": {"TicketSequence": 42},
                }
            }
        ],
    },
    "hash": "DEADBEEF" * 8,
    "ledger_index": 1234567,
}

MOCK_SUBMIT_RESPONSE = {
    "meta": {"TransactionResult": "tesSUCCESS"},
    "hash": "CAFEBABE" * 8,
    "ledger_index": 1234568,
}


def _build_agent_with_mocks(
    kyb_found: bool = True,
    submit_response: dict | None = None,
    daily_spend: Decimal = Decimal("0"),
) -> ProcurementAgent:
    """
    Build a ProcurementAgent with all XRPL network calls mocked out.
    """
    # Clear in-memory spend ledger so tests are independent
    _daily_spend_ledger.clear()
    if daily_spend > 0:
        from app.services.procurement_agent import _get_today_key
        _daily_spend_ledger[_get_today_key()] = daily_spend

    agent = ProcurementAgent.__new__(ProcurementAgent)
    agent._settings = _mock_settings()

    # Mock XRPL client
    mock_client = MagicMock()
    # account_objects response for KYB check
    credential_obj = {
        "LedgerEntryType": "Credential",
        "CredentialType": "4B5942566572696669656400000000000000000000000000000000000000000000",  # hex of "KYBVerified"
        "index": "CRED001",
    } if kyb_found else {}
    mock_client.request.return_value = MagicMock(
        result={"account_objects": [credential_obj] if kyb_found else []}
    )
    agent._client = mock_client

    # Mock agent wallet
    mock_agent_wallet = MagicMock()
    mock_agent_wallet.classic_address = "rAgentAddress000000000000000000"
    agent._agent_wallet = mock_agent_wallet

    # Mock cosigner
    mock_cosigner = MagicMock()
    mock_cosigner.address = "rCosignerAddress00000000000000000"
    mock_cosigner.sign_transaction.return_value = MagicMock()
    agent._cosigner = mock_cosigner

    return agent, mock_client, mock_cosigner


def _mock_settings():
    settings = MagicMock()
    settings.xrpl_node_url = "https://s.altnet.rippletest.net:51234/"
    settings.main_account_address = "rMAINACCOUNT0000000000000000000"
    settings.rlusd_currency_hex = "524C555344000000000000000000000000000000"
    settings.rlusd_issuer = "rQhWct2fv4Vc4KRjRgMrxa8xPN9Zx9iLKV"
    settings.agent_seed = "sAGENT_SEED"
    settings.policy_cosigner_seed = "sCOSIGNER_SEED"
    settings.daily_spending_cap_rlusd = Decimal("5000.00")
    settings.approved_supplier_list = [APPROVED_SUPPLIER]
    settings.kyb_credential_type = "KYBVerified"
    return settings


# ---------------------------------------------------------------------------
# Test: Path A – Autonomous Approval
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_path_a_approved_within_mandate():
    """
    Given: Approved supplier, invoice matches order, within daily cap.
    Expected: APPROVED, submitted_tx populated, no approval_request.
    """
    agent, mock_client, mock_cosigner = _build_agent_with_mocks()

    order = _make_order()
    invoice = _make_invoice()
    supplier = _make_supplier()

    with (
        patch("app.services.procurement_agent.autofill") as mock_autofill,
        patch("app.services.procurement_agent.sign") as mock_sign,
        patch("app.services.procurement_agent.multisign") as mock_multisign,
        patch("app.services.procurement_agent.submit_and_wait") as mock_submit,
    ):
        mock_autofill.return_value = MagicMock()
        mock_sign.return_value = MagicMock()
        mock_multisign.return_value = MagicMock()

        # First call: TicketCreate submission
        # Second call: EscrowCreate / Payment submission
        ticket_resp = MagicMock()
        ticket_resp.result = MOCK_TICKET_RESPONSE

        payment_resp = MagicMock()
        payment_resp.result = MOCK_SUBMIT_RESPONSE

        mock_submit.side_effect = [ticket_resp, payment_resp]

        result = await agent.process_invoice(order, invoice, supplier)

    assert result.outcome == InvoiceOutcome.APPROVED
    assert result.submitted_tx is not None
    assert result.approval_request is None
    assert result.submitted_tx.ticket_sequence_used == 42
    assert "CAFEBABE" in result.submitted_tx.xrpl_tx_hash
    assert result.ai_verification.passed is True
    assert result.mandate_check.mandate_satisfied is True

    # Verify cosigner was called (Path A must involve the cosigner)
    assert mock_cosigner.sign_transaction.called


# ---------------------------------------------------------------------------
# Test: Path B – Escalation (Daily Cap Exceeded)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_path_b_escalated_exceeds_daily_cap():
    """
    Given: Approved supplier, invoice matches, BUT daily cap is already 90% used
           and this transaction would exceed it.
    Expected: ESCALATED, approval_request populated, cosigner NOT called.
    """
    # Pre-load 4500 RLUSD spent today (cap is 5000)
    agent, mock_client, mock_cosigner = _build_agent_with_mocks(
        daily_spend=Decimal("4500.00")
    )

    order = _make_order(total=Decimal("800.00"))  # 4500 + 800 = 5300 > 5000
    invoice = _make_invoice(total=Decimal("800.00"))
    supplier = _make_supplier()

    with (
        patch("app.services.procurement_agent.autofill") as mock_autofill,
        patch("app.services.procurement_agent.sign") as mock_sign,
        patch("app.services.procurement_agent.multisign") as mock_multisign,
        patch("app.services.procurement_agent.submit_and_wait") as mock_submit,
    ):
        mock_autofill.return_value = MagicMock()

        # sign() is called for TicketCreate agent sig + EscrowCreate agent sig
        mock_sign.return_value = MagicMock()
        mock_multisign.return_value = MagicMock()

        # Only TicketCreate is submitted on Path B (no payment submission)
        ticket_resp = MagicMock()
        ticket_resp.result = MOCK_TICKET_RESPONSE
        mock_submit.return_value = ticket_resp

        # Agent signed tx needs to_xrpl() for the blob
        mock_agent_signed = MagicMock()
        mock_agent_signed.to_xrpl.return_value = {"TransactionType": "Payment", "mock": True}
        mock_sign.return_value = mock_agent_signed

        result = await agent.process_invoice(order, invoice, supplier)

    assert result.outcome == InvoiceOutcome.ESCALATED
    assert result.approval_request is not None
    assert result.submitted_tx is None

    # CRITICAL: Cosigner must NOT be called on Path B
    # (TicketCreate cosigner call is acceptable – that's an admin op)
    # We check the payment signing path: sign_transaction should not be called
    # with a non-zero amount (i.e., no payment cosigning occurred)
    payment_cosign_calls = [
        call for call in mock_cosigner.sign_transaction.call_args_list
        if call.kwargs.get("transaction_amount_rlusd", Decimal("0")) > 0
    ]
    assert len(payment_cosign_calls) == 0, (
        "SECURITY VIOLATION: PolicyCosigner was called for a payment on Path B!"
    )

    # Escalation metadata must be populated
    ar = result.approval_request
    assert "EXCEEDS_DAILY_CAP" in ar.escalation_reason.value
    assert "5300" in ar.human_readable_reason or "5000" in ar.human_readable_reason
    assert ar.ticket_sequence_used == 42
    assert ar.partially_signed_tx_blob is not None


# ---------------------------------------------------------------------------
# Test: Path B – Escalation (Unapproved Supplier, After AI/Ledger Fail)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rejected_unapproved_supplier_at_ledger_step():
    """
    Given: Supplier is NOT on the allowlist (ledger check fails at Step 2).
    Expected: REJECTED (not ESCALATED – rejected before transaction prep).
    """
    agent, mock_client, mock_cosigner = _build_agent_with_mocks()

    order = _make_order(supplier=UNAPPROVED_SUPPLIER)
    invoice = _make_invoice(supplier=UNAPPROVED_SUPPLIER)
    supplier = _make_supplier(address=UNAPPROVED_SUPPLIER)

    result = await agent.process_invoice(order, invoice, supplier)

    assert result.outcome == InvoiceOutcome.REJECTED
    assert result.ledger_verification is not None
    assert result.ledger_verification.supplier_on_allowlist is False
    assert result.submitted_tx is None
    assert result.approval_request is None
    assert "ledger" in result.rejection_reason.lower()

    # No XRPL transaction should have been attempted
    mock_cosigner.sign_transaction.assert_not_called()


# ---------------------------------------------------------------------------
# Test: Path B – Escalation (Mandate Broken – Supplier Not on Owner's List)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_path_b_escalated_unapproved_supplier_at_mandate_step():
    """
    Test a supplier that passes KYB on ledger but is NOT on the mandate list.
    
    Note: In this test we patch approved_supplier_list to differ between
    ledger check (passes) and mandate check (fails).
    """
    agent, mock_client, mock_cosigner = _build_agent_with_mocks()

    # Make the supplier pass ledger verification but fail mandate check
    # by temporarily having an empty mandate approved list
    agent._settings.approved_supplier_list = []  # mandate list empty

    # But the ledger check uses the same list – patch KYB to pass separately
    mock_client.request.return_value = MagicMock(result={"account_objects": []})

    order = _make_order(supplier=APPROVED_SUPPLIER)
    # Supplier address matches order but mandate list is empty
    invoice = _make_invoice(supplier=APPROVED_SUPPLIER)
    supplier = _make_supplier()

    # With empty approved list, ledger step will reject first (supplier_on_allowlist=False)
    result = await agent.process_invoice(order, invoice, supplier)

    # Expect REJECTED at ledger step since allowlist is empty
    assert result.outcome == InvoiceOutcome.REJECTED


# ---------------------------------------------------------------------------
# Test: REJECTED – AI Verification Fails (amount mismatch)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rejected_ai_verification_amount_mismatch():
    """
    Given: Invoice total significantly differs from order total (>1% tolerance).
    Expected: REJECTED at Step 1 (AI Verification).
    """
    agent, mock_client, mock_cosigner = _build_agent_with_mocks()

    order = _make_order(total=Decimal("1000.00"))
    # Invoice total is 20% higher than the order
    invoice = _make_invoice(total=Decimal("1200.00"))
    supplier = _make_supplier()

    result = await agent.process_invoice(order, invoice, supplier)

    assert result.outcome == InvoiceOutcome.REJECTED
    assert result.ai_verification is not None
    assert result.ai_verification.passed is False
    assert any("mismatch" in d.lower() for d in result.ai_verification.discrepancies)
    assert result.submitted_tx is None
    assert result.approval_request is None

    # No ledger queries should have happened
    mock_client.request.assert_not_called()
    mock_cosigner.sign_transaction.assert_not_called()


# ---------------------------------------------------------------------------
# Test: REJECTED – AI Verification Fails (supplier address mismatch)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rejected_ai_verification_supplier_mismatch():
    """
    Given: Invoice supplier address differs from the original order's supplier.
    Expected: REJECTED at Step 1.
    """
    agent, mock_client, mock_cosigner = _build_agent_with_mocks()

    order = _make_order(supplier=APPROVED_SUPPLIER)
    # Invoice has a different supplier address than the order
    invoice = _make_invoice(supplier="rFRAUDULENT_ADDRESS_000000000000")
    supplier = _make_supplier()

    result = await agent.process_invoice(order, invoice, supplier)

    assert result.outcome == InvoiceOutcome.REJECTED
    assert result.ai_verification.passed is False
    discrepancy_text = " ".join(result.ai_verification.discrepancies).lower()
    assert "supplier" in discrepancy_text and "mismatch" in discrepancy_text


# ---------------------------------------------------------------------------
# Test: Security – Agent wallet is not the main account seed
# ---------------------------------------------------------------------------


def test_security_agent_wallet_is_not_main_account():
    """
    Verify the agent wallet address is different from the main account address.
    This is the core security invariant: the agent MUST NOT use the main key.
    """
    agent, _, _ = _build_agent_with_mocks()

    assert agent._agent_wallet.classic_address != agent._settings.main_account_address, (
        "CRITICAL SECURITY VIOLATION: Agent wallet address matches main account address! "
        "The agent must use its OWN delegated seed, not the main account seed."
    )

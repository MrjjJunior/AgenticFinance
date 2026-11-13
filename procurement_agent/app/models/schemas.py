"""
Pydantic schemas for the AI Procurement Agent API.

Defines the request/response models for the /process-invoice endpoint,
covering all three possible outcomes:
  - APPROVED   → autonomous EscrowCreate submitted (Path A)
  - ESCALATED  → ApprovalRequest returned for Human Owner (Path B)
  - REJECTED   → AI or ledger verification failed
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class InvoiceOutcome(str, Enum):
    APPROVED = "APPROVED"       # Path A – autonomous execution
    ESCALATED = "ESCALATED"     # Path B – human override required
    REJECTED = "REJECTED"       # Verification failed; no transaction prepared


class EscalationReason(str, Enum):
    EXCEEDS_DAILY_CAP = "EXCEEDS_DAILY_CAP"
    UNAPPROVED_SUPPLIER = "UNAPPROVED_SUPPLIER"
    BOTH = "EXCEEDS_DAILY_CAP_AND_UNAPPROVED_SUPPLIER"


# ---------------------------------------------------------------------------
# Inbound – Invoice Processing Request
# ---------------------------------------------------------------------------


class LineItem(BaseModel):
    description: str = Field(..., description="Human-readable product/service description")
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)

    @property
    def line_total(self) -> Decimal:
        return self.quantity * self.unit_price


class ParsedInvoice(BaseModel):
    """OCR-extracted invoice data from the mobile app."""
    invoice_number: str
    supplier_xrpl_address: str = Field(
        ...,
        description="XRPL r-address of the supplier (payment destination)",
    )
    line_items: list[LineItem]
    stated_total: Decimal = Field(..., gt=0, description="Total as printed on the invoice")
    currency: str = Field(default="RLUSD")
    invoice_date: str  # ISO-8601 date string


class OrderIntent(BaseModel):
    """Original purchase order raised by the Stokvel / Human Owner."""
    order_id: str
    expected_supplier_xrpl_address: str
    items: list[LineItem]
    expected_total: Decimal = Field(..., gt=0)
    currency: str = Field(default="RLUSD")


class SupplierDetails(BaseModel):
    """Supplementary supplier metadata passed by the mobile app."""
    name: str
    registration_number: str
    xrpl_address: str


class ProcessInvoiceRequest(BaseModel):
    """
    Top-level request body for POST /api/v1/process-invoice.

    The mobile app sends:
      - The original order intent
      - The OCR-parsed invoice
      - Basic supplier metadata
    """
    order_intent: OrderIntent
    parsed_invoice: ParsedInvoice
    supplier_details: SupplierDetails


# ---------------------------------------------------------------------------
# Outbound – Verification Steps (included in every response for auditability)
# ---------------------------------------------------------------------------


class AIVerificationResult(BaseModel):
    passed: bool
    discrepancies: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning: str


class LedgerVerificationResult(BaseModel):
    supplier_on_allowlist: bool
    kyb_credential_found: bool
    passed: bool


class MandateCheckResult(BaseModel):
    daily_cap_rlusd: Decimal
    already_spent_today_rlusd: Decimal
    this_transaction_rlusd: Decimal
    within_cap: bool
    supplier_approved: bool
    mandate_satisfied: bool  # True only when BOTH conditions met


# ---------------------------------------------------------------------------
# Outbound – Transaction Blobs
# ---------------------------------------------------------------------------


class SubmittedTransaction(BaseModel):
    """Returned when Path A succeeds – transaction is already on ledger."""
    xrpl_tx_hash: str
    ledger_index: Optional[int] = None
    explorer_url: str
    ticket_sequence_used: int


class ApprovalRequest(BaseModel):
    """
    Returned when Path B triggers – transaction signed by Agent only (weight 1).
    The Human Owner (weight 2) must countersign and submit.
    """
    escalation_reason: EscalationReason
    human_readable_reason: str
    # The partially-signed transaction blob the owner must complete
    partially_signed_tx_blob: str
    # The raw tx dict is included so the frontend can render it for the owner
    tx_dict: dict[str, Any]
    ticket_sequence_used: int
    instructions: str = (
        "Sign this transaction with your wallet (weight=2) and submit to XRPL Testnet. "
        "Your single signature meets the quorum of 2."
    )


# ---------------------------------------------------------------------------
# Outbound – Final Response
# ---------------------------------------------------------------------------


class ProcessInvoiceResponse(BaseModel):
    """
    Unified response envelope for POST /api/v1/process-invoice.

    One of `submitted_tx` or `approval_request` will be populated
    depending on the routing outcome. Neither is set when outcome=REJECTED.
    """
    outcome: InvoiceOutcome
    order_id: str
    invoice_number: str

    # Step-by-step audit trail
    ai_verification: Optional[AIVerificationResult] = None
    ledger_verification: Optional[LedgerVerificationResult] = None
    mandate_check: Optional[MandateCheckResult] = None

    # Exactly one of these is set on success/escalation
    submitted_tx: Optional[SubmittedTransaction] = None
    approval_request: Optional[ApprovalRequest] = None

    # Set on REJECTED
    rejection_reason: Optional[str] = None

# backend/app/schemas.py
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from app.models import EscrowStage, ParticipantStatus, PolicyPath, PoolStatus


class PoolCreateRequest(BaseModel):
    group_code: str = Field(..., min_length=3, max_length=32, examples=["POOL-NOODLE-CPT-01"])
    product_sku: str = Field(..., examples=["SKU-NOODLE-40PK"])
    product_name: str = Field(..., examples=["Instant Noodles (Box of 40)"])
    unit_label: str = Field(default="box")
    supplier_name: str = Field(..., examples=["Gauteng Foods Wholesale (Pty) Ltd"])
    supplier_wallet_address: str = Field(..., examples=["rSupplierJHBWholesale11111111111"])
    retail_unit_price_zar: Decimal = Field(..., gt=0, examples=[Decimal("8.00")])
    wholesale_unit_price_zar: Decimal = Field(..., gt=0, examples=[Decimal("5.00")])
    wholesale_unit_trigger: int = Field(..., ge=1, examples=[10])
    supplier_moq_units: int = Field(..., ge=1, examples=[10])
    supplier_hub: str = Field(..., examples=["hub_johannesburg"])
    delivery_zone: str = Field(..., examples=["zone_1_cape_town"])
    carrier_wallet_address: str = Field(..., examples=["rCarrierBulkLogisticsDemo111111111"])
    deadline_hours: int = Field(default=48, ge=1, le=720)


class QuotePreviewRequest(BaseModel):
    group_code: str
    quantity: int = Field(..., ge=1)


class JoinPoolRequest(BaseModel):
    group_code: str
    business_name: str = Field(..., min_length=2, max_length=120, examples=["Sipho's Spaza Shop"])
    buyer_wallet_address: str = Field(..., examples=["rSiphoSpazaBuyerWallet1111111111"])
    quantity: int = Field(..., ge=1, examples=[2])


class OwnerApprovalRequest(BaseModel):
    participant_id: int
    owner_signature_token: str = Field(..., min_length=6)


class DeliveryWebhookRequest(BaseModel):
    group_code: str
    bol_reference: str = Field(..., examples=["BOL-JHB-CPT-2026-8841"])


class BuyerDefaultRequest(BaseModel):
    participant_id: int
    reason: str = Field(default="Buyer unilaterally cancelled after commitment.")


class QuoteBreakdownResponse(BaseModel):
    group_code: str
    product_name: str
    quantity: int
    projected_group_total_quantity: int
    wholesale_unit_trigger: int
    buyer_trigger_proximity_pct: Decimal
    retail_unit_price_zar: Decimal
    wholesale_unit_price_zar: Decimal
    unit_cost_zar: Decimal
    product_savings_zar: Decimal
    gross_subtotal_product_zar: Decimal
    solo_freight_quote_zar: Decimal
    buyer_quoted_freight_zar: Decimal
    buyer_shipping_discount_zar: Decimal
    buyer_service_fee_zar: Decimal
    total_buyer_surplus_zar: Decimal
    final_amount_zar: Decimal
    final_amount_rlusd: Decimal
    deposit_amount_zar: Decimal
    deposit_amount_rlusd: Decimal
    balance_due_zar: Decimal
    balance_due_rlusd: Decimal
    deposit_policy_summary: str


class EscrowSummaryResponse(BaseModel):
    id: int
    stage: EscrowStage
    tx_hash: str
    offer_sequence: int
    amount_rlusd: Decimal
    is_settled: bool
    is_cancelled: bool
    settlement_tx_hash: str | None = None
    unsigned_tx_json: dict[str, Any] | None = None


class ParticipantResponse(BaseModel):
    id: int
    business_name: str
    buyer_wallet_address: str
    quantity: int
    unit_cost_zar: Decimal
    product_savings_zar: Decimal
    buyer_shipping_discount_zar: Decimal
    total_buyer_surplus_zar: Decimal
    total_platform_revenue_zar: Decimal
    final_amount_zar: Decimal
    final_amount_rlusd: Decimal
    deposit_amount_zar: Decimal
    deposit_amount_rlusd: Decimal
    balance_due_zar: Decimal
    balance_due_rlusd: Decimal
    ipfs_cid: str
    policy_path: PolicyPath
    status: ParticipantStatus
    escrows: list[EscrowSummaryResponse] = []


class PoolGroupResponse(BaseModel):
    id: int
    group_code: str
    product_sku: str
    product_name: str
    unit_label: str
    supplier_name: str
    supplier_wallet_address: str
    supplier_kyb_verified: bool
    retail_unit_price_zar: Decimal
    wholesale_unit_price_zar: Decimal
    wholesale_unit_trigger: int
    supplier_moq_units: int
    current_pooled_units: int
    moq_progress_pct: Decimal
    supplier_hub: str
    delivery_zone: str
    status: PoolStatus
    deadline_utc: datetime
    mpt_issuance_tx_hash: str | None = None
    bol_reference: str | None = None
    participants: list[ParticipantResponse] = []

    # Add to backend/app/schemas.py
class CFOPolicyUpdateRequest(BaseModel):
    buyer_wallet_address: str = Field(..., examples=["rSiphoSpazaBuyerWallet1111111111"])
    business_name: str = Field(..., examples=["Sipho's Spaza Shop"])
    daily_autonomous_limit_zar: Decimal = Field(..., ge=0, examples=[Decimal("50000.00")])
    single_order_limit_zar: Decimal = Field(..., ge=0, examples=[Decimal("25000.00")])
    require_xls70_kyb: bool = Field(default=True)
    cfo_wallet_address: str = Field(..., examples=["rSiphoCFOMasterWallet11111111111"])


class CFOPolicyResponse(BaseModel):
    buyer_wallet_address: str
    business_name: str
    daily_autonomous_limit_zar: Decimal
    single_order_limit_zar: Decimal
    require_xls70_kyb: bool
    rolling_24h_spend_zar: Decimal
    remaining_autonomous_allowance_zar: Decimal
    updated_by_cfo_wallet: str
    updated_at: datetime
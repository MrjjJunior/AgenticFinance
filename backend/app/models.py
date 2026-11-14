# backend/app/models.py
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class PoolStatus(str, Enum):
    OPEN_POOL = "OPEN_POOL"
    MOQ_LOCKED = "MOQ_LOCKED"
    ESCROW_ACTIVE = "ESCROW_ACTIVE"
    SETTLED = "SETTLED"
    POOL_FAILED = "POOL_FAILED"


class ParticipantStatus(str, Enum):
    DEPOSIT_LOCKED = "DEPOSIT_LOCKED"
    PENDING_OWNER_APPROVAL = "PENDING_OWNER_APPROVAL"
    ESCROW_FUNDED = "ESCROW_FUNDED"
    SETTLED = "SETTLED"
    REFUNDED_MOQ_FAILED = "REFUNDED_MOQ_FAILED"
    DEFAULTED_DEPOSIT_FORFEITED = "DEFAULTED_DEPOSIT_FORFEITED"


class EscrowStage(str, Enum):
    DEPOSIT_20_PCT = "DEPOSIT_20_PCT"
    FULL_SETTLEMENT_100_PCT = "FULL_SETTLEMENT_100_PCT"


class PolicyPath(str, Enum):
    PATH_A_AUTONOMOUS = "PATH_A_AUTONOMOUS"
    PATH_B_OWNER_APPROVAL = "PATH_B_OWNER_APPROVAL"


class PoolGroup(Base):
    __tablename__ = "pool_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    product_sku: Mapped[str] = mapped_column(String(64), nullable=False)
    product_name: Mapped[str] = mapped_column(String(160), nullable=False)
    unit_label: Mapped[str] = mapped_column(String(48), default="box", nullable=False)

    # Supplier & On-Ledger XLS-70 KYB Verification
    supplier_name: Mapped[str] = mapped_column(String(120), nullable=False)
    supplier_wallet_address: Mapped[str] = mapped_column(String(64), nullable=False)
    supplier_kyb_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supplier_kyb_credential_index: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Floor-to-Ceiling Proximity Pricing Parameters (ZAR)
    retail_unit_price_zar: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    wholesale_unit_price_zar: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    wholesale_unit_trigger: Mapped[int] = mapped_column(Integer, nullable=False)
    supplier_moq_units: Mapped[int] = mapped_column(Integer, nullable=False)
    current_pooled_units: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Supplier-to-Buyer Corridor Route
    supplier_hub: Mapped[str] = mapped_column(String(64), nullable=False)
    delivery_zone: Mapped[str] = mapped_column(String(64), nullable=False)
    carrier_wallet_address: Mapped[str] = mapped_column(String(64), nullable=False)

    # Pool Lifecycle & On-Ledger Artifacts
    status: Mapped[PoolStatus] = mapped_column(
        SAEnum(PoolStatus), default=PoolStatus.OPEN_POOL, nullable=False
    )
    deadline_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    mpt_issuance_tx_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    bol_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    participants: Mapped[list["PoolParticipant"]] = relationship(
        back_populates="pool_group", cascade="all, delete-orphan"
    )


class PoolParticipant(Base):
    __tablename__ = "pool_participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pool_group_id: Mapped[int] = mapped_column(ForeignKey("pool_groups.id"), nullable=False)
    business_name: Mapped[str] = mapped_column(String(120), nullable=False)
    buyer_wallet_address: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    # Locked Pricing & Surplus Breakdown (ZAR & RLUSD)
    unit_cost_zar: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    gross_subtotal_product_zar: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    supplier_marketplace_fee_zar: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    supplier_net_payout_zar: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    solo_freight_quote_zar: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    carrier_actual_cost_zar: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    buyer_quoted_freight_zar: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    buyer_shipping_discount_zar: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    platform_freight_arbitrage_zar: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    buyer_service_fee_zar: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_buyer_surplus_zar: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_platform_revenue_zar: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    final_amount_zar: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    final_amount_rlusd: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    deposit_amount_zar: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    deposit_amount_rlusd: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    balance_due_zar: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    balance_due_rlusd: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)

    # IPFS Pinning & Guardrail State
    ipfs_cid: Mapped[str] = mapped_column(String(128), nullable=False)
    policy_path: Mapped[PolicyPath] = mapped_column(SAEnum(PolicyPath), nullable=False)
    status: Mapped[ParticipantStatus] = mapped_column(
        SAEnum(ParticipantStatus), default=ParticipantStatus.DEPOSIT_LOCKED, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    pool_group: Mapped["PoolGroup"] = relationship(back_populates="participants")
    escrows: Mapped[list["EscrowRecord"]] = relationship(
        back_populates="participant", cascade="all, delete-orphan"
    )


class EscrowRecord(Base):
    __tablename__ = "escrow_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("pool_participants.id"), nullable=False)
    stage: Mapped[EscrowStage] = mapped_column(SAEnum(EscrowStage), nullable=False)
    tx_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    offer_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_rlusd: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    condition_hex: Mapped[str | None] = mapped_column(Text, nullable=True)
    preimage_hex: Mapped[str | None] = mapped_column(Text, nullable=True)
    unsigned_tx_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_settled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    settlement_tx_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    participant: Mapped["PoolParticipant"] = relationship(back_populates="escrows")


class AgentSpendLog(Base):
    __tablename__ = "agent_spend_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    buyer_wallet_address: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    group_code: Mapped[str] = mapped_column(String(32), nullable=False)
    amount_zar: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    policy_path: Mapped[PolicyPath] = mapped_column(SAEnum(PolicyPath), nullable=False)
    approved_by_owner: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    # Add to backend/app/models.py
class BuyerPolicyConfig(Base):
    __tablename__ = "buyer_policy_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    buyer_wallet_address: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    business_name: Mapped[str] = mapped_column(String(120), nullable=False)
    daily_autonomous_limit_zar: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("50000.00"), nullable=False
    )
    single_order_limit_zar: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("50000.00"), nullable=False
    )
    require_xls70_kyb: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_by_cfo_wallet: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
# backend/app/services/policy_engine.py
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AgentSpendLog, BuyerPolicyConfig, PolicyPath

DEFAULT_DAILY_LIMIT_ZAR = Decimal(os.getenv("DAILY_AUTONOMOUS_LIMIT_ZAR", "50000.00"))
DEFAULT_SINGLE_ORDER_LIMIT_ZAR = Decimal(os.getenv("SINGLE_ORDER_AUTONOMOUS_LIMIT_ZAR", "50000.00"))


class PolicyHardBlockError(Exception):
    """Raised when a mandatory compliance prerequisite (XLS-70 KYB or IPFS CID) fails."""


@dataclass(frozen=True)
class PolicyEvaluationResult:
    allowed_to_proceed: bool
    policy_path: PolicyPath
    autonomous_approved: bool
    rolling_24h_spend_zar: Decimal
    proposed_order_zar: Decimal
    projected_24h_total_zar: Decimal
    daily_limit_zar: Decimal
    single_order_limit_zar: Decimal
    remaining_autonomous_allowance_zar: Decimal
    reason: str


async def get_or_default_buyer_policy(
        session: AsyncSession,
        buyer_wallet_address: str,
) -> tuple[Decimal, Decimal, bool]:
    """
    Fetches the CFO-configured autonomous spend guardrails for a specific buyer wallet.
    Falls back to platform defaults (R50,000 daily / R50,000 single-order) if unconfigured.
    """
    stmt = select(BuyerPolicyConfig).where(
        BuyerPolicyConfig.buyer_wallet_address == buyer_wallet_address
    )
    res = await session.execute(stmt)
    config = res.scalar_one_or_none()

    if config is None:
        return DEFAULT_DAILY_LIMIT_ZAR, DEFAULT_SINGLE_ORDER_LIMIT_ZAR, True

    return (
        Decimal(config.daily_autonomous_limit_zar).quantize(Decimal("0.01")),
        Decimal(config.single_order_limit_zar).quantize(Decimal("0.01")),
        bool(config.require_xls70_kyb),
    )


async def upsert_cfo_policy(
        *,
        session: AsyncSession,
        buyer_wallet_address: str,
        business_name: str,
        daily_autonomous_limit_zar: Decimal,
        single_order_limit_zar: Decimal,
        require_xls70_kyb: bool,
        cfo_wallet_address: str,
) -> BuyerPolicyConfig:
    """
    Allows an organization's CFO to create or update autonomous AI execution thresholds.
    """
    stmt = select(BuyerPolicyConfig).where(
        BuyerPolicyConfig.buyer_wallet_address == buyer_wallet_address
    )
    res = await session.execute(stmt)
    config = res.scalar_one_or_none()

    if config is None:
        config = BuyerPolicyConfig(
            buyer_wallet_address=buyer_wallet_address,
            business_name=business_name,
            daily_autonomous_limit_zar=daily_autonomous_limit_zar.quantize(Decimal("0.01")),
            single_order_limit_zar=single_order_limit_zar.quantize(Decimal("0.01")),
            require_xls70_kyb=require_xls70_kyb,
            updated_by_cfo_wallet=cfo_wallet_address,
        )
        session.add(config)
    else:
        config.business_name = business_name
        config.daily_autonomous_limit_zar = daily_autonomous_limit_zar.quantize(Decimal("0.01"))
        config.single_order_limit_zar = single_order_limit_zar.quantize(Decimal("0.01"))
        config.require_xls70_kyb = require_xls70_kyb
        config.updated_by_cfo_wallet = cfo_wallet_address

    await session.flush()
    return config


async def get_rolling_24h_spend_zar(
        session: AsyncSession,
        buyer_wallet_address: str,
) -> Decimal:
    """
    Computes the buyer wallet's cumulative approved/autonomous spend over the past 24 hours.
    """
    window_start = datetime.now(timezone.utc) - timedelta(hours=24)
    stmt = select(func.coalesce(func.sum(AgentSpendLog.amount_zar), Decimal("0.00"))).where(
        AgentSpendLog.buyer_wallet_address == buyer_wallet_address,
        AgentSpendLog.created_at >= window_start,
        AgentSpendLog.approved_by_owner.is_(True),
        )
    result = await session.execute(stmt)
    total = result.scalar_one_or_none()
    return Decimal(total or "0.00").quantize(Decimal("0.01"))


async def evaluate_execution_policy(
        *,
        session: AsyncSession,
        buyer_wallet_address: str,
        proposed_order_zar: Decimal,
        supplier_kyb_verified: bool,
        ipfs_cid: str,
) -> PolicyEvaluationResult:
    """
    Deterministic CFO-configurable policy guardrail:
    1. XLS-70 Supplier KYB check (enforced when require_xls70_kyb=True).
    2. IPFS PricingReceipt CID must be pinned.
    3. Single-order cap AND rolling 24h spend cap configured by the CFO:
       - Within both CFO limits -> Path A (Autonomous AI Execution)
       - Exceeds either CFO limit -> Path B (Staged for CFO / Owner Approval)
    """
    daily_limit_zar, single_order_limit_zar, require_kyb = await get_or_default_buyer_policy(
        session, buyer_wallet_address
    )

    if require_kyb and not supplier_kyb_verified:
        raise PolicyHardBlockError(
            "POLICY_BLOCK_KYB: CFO policy requires an active XLS-70 KYB_VERIFIED credential on XRPL."
        )

    if not ipfs_cid or len(ipfs_cid.strip()) < 10:
        raise PolicyHardBlockError(
            "POLICY_BLOCK_IPFS: Deterministic PricingReceipt must be pinned to IPFS before escrow execution."
        )

    rolling_spend = await get_rolling_24h_spend_zar(session, buyer_wallet_address)
    projected_total = (rolling_spend + proposed_order_zar).quantize(Decimal("0.01"))
    remaining_before = max(Decimal("0.00"), (daily_limit_zar - rolling_spend).quantize(Decimal("0.01")))

    if proposed_order_zar > single_order_limit_zar:
        return PolicyEvaluationResult(
            allowed_to_proceed=True,
            policy_path=PolicyPath.PATH_B_OWNER_APPROVAL,
            autonomous_approved=False,
            rolling_24h_spend_zar=rolling_spend,
            proposed_order_zar=proposed_order_zar,
            projected_24h_total_zar=projected_total,
            daily_limit_zar=daily_limit_zar,
            single_order_limit_zar=single_order_limit_zar,
            remaining_autonomous_allowance_zar=remaining_before,
            reason=(
                f"PATH B PAUSED (SINGLE-ORDER CAP): Order R {proposed_order_zar:,.2f} exceeds CFO's "
                f"single-order autonomous limit of R {single_order_limit_zar:,.2f}."
            ),
        )

    if projected_total > daily_limit_zar:
        return PolicyEvaluationResult(
            allowed_to_proceed=True,
            policy_path=PolicyPath.PATH_B_OWNER_APPROVAL,
            autonomous_approved=False,
            rolling_24h_spend_zar=rolling_spend,
            proposed_order_zar=proposed_order_zar,
            projected_24h_total_zar=projected_total,
            daily_limit_zar=daily_limit_zar,
            single_order_limit_zar=single_order_limit_zar,
            remaining_autonomous_allowance_zar=remaining_before,
            reason=(
                f"PATH B PAUSED (24H DAILY CAP): Projected 24h spend R {projected_total:,.2f} exceeds CFO's "
                f"daily autonomous limit of R {daily_limit_zar:,.2f}."
            ),
        )

    remaining_after = (daily_limit_zar - projected_total).quantize(Decimal("0.01"))
    return PolicyEvaluationResult(
        allowed_to_proceed=True,
        policy_path=PolicyPath.PATH_A_AUTONOMOUS,
        autonomous_approved=True,
        rolling_24h_spend_zar=rolling_spend,
        proposed_order_zar=proposed_order_zar,
        projected_24h_total_zar=projected_total,
        daily_limit_zar=daily_limit_zar,
        single_order_limit_zar=single_order_limit_zar,
        remaining_autonomous_allowance_zar=remaining_after,
        reason=(
            f"PATH A APPROVED: Order R {proposed_order_zar:,.2f} (projected 24h: R {projected_total:,.2f}) "
            f"is within CFO guardrails (daily cap: R {daily_limit_zar:,.2f}, single-order cap: R {single_order_limit_zar:,.2f})."
        ),
    )


async def record_spend_log(
        *,
        session: AsyncSession,
        buyer_wallet_address: str,
        group_code: str,
        amount_zar: Decimal,
        policy_path: PolicyPath,
        approved_by_owner: bool,
) -> AgentSpendLog:
    entry = AgentSpendLog(
        buyer_wallet_address=buyer_wallet_address,
        group_code=group_code,
        amount_zar=amount_zar,
        policy_path=policy_path,
        approved_by_owner=approved_by_owner,
    )
    session.add(entry)
    await session.flush()
    return entry
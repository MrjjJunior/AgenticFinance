# backend/app/main.py
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal, get_db, init_db
from app.models import (
    EscrowStage,
    ParticipantStatus,
    PolicyPath,
    PoolGroup,
    PoolParticipant,
    PoolStatus,
)
from app.schemas import (
    BuyerDefaultRequest,
    CFOPolicyResponse,
    CFOPolicyUpdateRequest,
    DeliveryWebhookRequest,
    JoinPoolRequest,
    OwnerApprovalRequest,
    PoolCreateRequest,
    PoolGroupResponse,
    QuoteBreakdownResponse,
    QuotePreviewRequest,
)
from app.services.idempotency_service import check_idempotency_cache, save_idempotency_cache
from app.services.ipfs_service import IPFSReceiptService
from app.services.policy_engine import (
    evaluate_execution_policy,
    get_or_default_buyer_policy,
    record_spend_log,
    upsert_cfo_policy,
)
from app.services.pricing_engine import calculate_participant_pricing
from app.services.xrpl_service import XRPL_LIVE_MODE, XRPLSettlementService


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with AsyncSessionLocal() as session:
        existing = await session.execute(
            select(PoolGroup).where(PoolGroup.group_code == "POOL-NOODLE-CPT-01")
        )
        if not existing.scalar_one_or_none():
            noodle_pool = PoolGroup(
                group_code="POOL-NOODLE-CPT-01",
                product_sku="SKU-NOODLE-40PK",
                product_name="Instant Noodles (Box of 40)",
                unit_label="box",
                supplier_name="Gauteng Foods Wholesale (Pty) Ltd",
                supplier_wallet_address="rSupplierJHBWholesale11111111111",
                supplier_kyb_verified=True,
                supplier_kyb_credential_index="XLS70-KYB-JHB-FOODS-8841",
                retail_unit_price_zar=Decimal("8.00"),
                wholesale_unit_price_zar=Decimal("5.00"),
                wholesale_unit_trigger=10,
                supplier_moq_units=10,
                current_pooled_units=0,
                supplier_hub="hub_johannesburg",
                delivery_zone="zone_1_cape_town",
                carrier_wallet_address="rCarrierBulkLogisticsDemo111111111",
                status=PoolStatus.OPEN_POOL,
                deadline_utc=datetime.now(timezone.utc) + timedelta(hours=48),
            )
            session.add(noodle_pool)
            await session.commit()
    yield


app = FastAPI(
    title="StokSafe API",
    description="AI-driven, Web3-enabled bulk procurement platform for South African SMBs (XRPL + IPFS).",
    version="2.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

xrpl_service = XRPLSettlementService()
ipfs_service = IPFSReceiptService()


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": "StokSafe Backend Engine",
        "xrpl_live_mode": XRPL_LIVE_MODE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/pools/join", response_model=PoolGroupResponse, tags=["Escrow"])
async def join_pool(
        payload: JoinPoolRequest,
        response: Response,
        x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
        session: AsyncSession = Depends(get_db),
):
    is_cached, cached_status, cached_body = await check_idempotency_cache(session, x_idempotency_key)
    if is_cached and cached_body is not None:
        response.status_code = cached_status or 200
        return cached_body

    pool = await _get_pool_by_code(session, payload.group_code)
    if pool.status != PoolStatus.OPEN_POOL:
        raise HTTPException(status_code=400, detail="Pool is no longer open for new participants.")

    new_total = pool.current_pooled_units + payload.quantity
    breakdown = calculate_participant_pricing(
        quantity=payload.quantity,
        new_group_total_quantity=max(pool.supplier_moq_units, new_total),
        retail_unit_price_zar=pool.retail_unit_price_zar,
        wholesale_unit_price_zar=pool.wholesale_unit_price_zar,
        wholesale_unit_trigger=pool.wholesale_unit_trigger,
        supplier_hub=pool.supplier_hub,
        delivery_zone=pool.delivery_zone,
    )

    receipt_dict = breakdown.to_receipt_dict(
        group_code=pool.group_code,
        product_sku=pool.product_sku,
        business_name=payload.business_name,
    )
    pin_result = await ipfs_service.pin_pricing_receipt(
        receipt_dict=receipt_dict,
        group_code=pool.group_code,
        buyer_wallet=payload.buyer_wallet_address,
    )

    policy_eval = await evaluate_execution_policy(
        session=session,
        buyer_wallet_address=payload.buyer_wallet_address,
        proposed_order_zar=breakdown.deposit_amount_zar,
        supplier_kyb_verified=pool.supplier_kyb_verified,
        ipfs_cid=pin_result.cid,
    )

    escrow_receipt = await xrpl_service.execute_or_stage_escrow(
        buyer_wallet=None,
        buyer_address=payload.buyer_wallet_address,
        destination_address=pool.supplier_wallet_address,
        amount_rlusd=breakdown.deposit_amount_rlusd,
        deadline_utc=pool.deadline_utc,
        ipfs_cid=pin_result.cid,
        group_code=pool.group_code,
        stage=EscrowStage.DEPOSIT_20_PCT,
        use_condition=True,
        autonomous_approved=policy_eval.autonomous_approved,
    )

    participant_status = (
        ParticipantStatus.DEPOSIT_LOCKED
        if policy_eval.autonomous_approved
        else ParticipantStatus.PENDING_OWNER_APPROVAL
    )

    participant = PoolParticipant(
        pool_group_id=pool.id,
        business_name=payload.business_name,
        buyer_wallet_address=payload.buyer_wallet_address,
        quantity=payload.quantity,
        unit_cost_zar=breakdown.unit_cost,
        gross_subtotal_product_zar=breakdown.gross_subtotal_product,
        supplier_marketplace_fee_zar=breakdown.supplier_marketplace_fee_zar,
        supplier_net_payout_zar=breakdown.supplier_net_payout_zar,
        solo_freight_quote_zar=breakdown.solo_freight_quote_zar,
        carrier_actual_cost_zar=breakdown.carrier_actual_cost_zar,
        buyer_quoted_freight_zar=breakdown.buyer_quoted_freight_zar,
        buyer_shipping_discount_zar=breakdown.buyer_shipping_discount_zar,
        platform_freight_arbitrage_zar=breakdown.platform_freight_arbitrage_zar,
        buyer_service_fee_zar=breakdown.buyer_service_fee_zar,
        total_buyer_surplus_zar=breakdown.total_buyer_surplus_zar,
        total_platform_revenue_zar=breakdown.total_platform_revenue_zar,
        final_amount_zar=breakdown.final_amount_zar,
        final_amount_rlusd=breakdown.final_amount_rlusd,
        deposit_amount_zar=breakdown.deposit_amount_zar,
        deposit_amount_rlusd=breakdown.deposit_amount_rlusd,
        balance_due_zar=breakdown.balance_due_zar,
        balance_due_rlusd=breakdown.balance_due_rlusd,
        ipfs_cid=pin_result.cid,
        policy_path=policy_eval.policy_path,
        status=participant_status,
    )
    session.add(participant)
    await session.flush()

    from app.models import EscrowRecord

    esc_rec = EscrowRecord(
        participant_id=participant.id,
        stage=EscrowStage.DEPOSIT_20_PCT,
        tx_hash=escrow_receipt.tx_hash,
        offer_sequence=escrow_receipt.offer_sequence,
        amount_rlusd=breakdown.deposit_amount_rlusd,
        condition_hex=escrow_receipt.condition_hex,
        preimage_hex=escrow_receipt.preimage_hex,
        unsigned_tx_json=str(escrow_receipt.unsigned_tx_json) if escrow_receipt.unsigned_tx_json else None,
        is_settled=False,
    )
    session.add(esc_rec)

    if policy_eval.autonomous_approved:
        await record_spend_log(
            session=session,
            buyer_wallet_address=payload.buyer_wallet_address,
            group_code=pool.group_code,
            amount_zar=breakdown.deposit_amount_zar,
            policy_path=policy_eval.policy_path,
            approved_by_owner=True,
        )
        pool.current_pooled_units += payload.quantity

        if pool.current_pooled_units >= pool.supplier_moq_units:
            pool.status = PoolStatus.MOQ_LOCKED
            mpt_res = await xrpl_service.mint_participation_mpt_xls33(
                issuer_wallet=None,
                issuer_address=pool.supplier_wallet_address,
                group_code=pool.group_code,
                total_units=pool.current_pooled_units,
                ipfs_cid=pin_result.cid,
            )
            pool.mpt_issuance_tx_hash = mpt_res.get("tx_hash")

    await session.commit()

    pool = await _get_pool_by_code(session, payload.group_code)
    resp_model = _build_pool_response(pool)
    resp_data = json.loads(json.dumps(resp_model.model_dump(), default=str))

    await save_idempotency_cache(session, x_idempotency_key, 200, resp_data)
    return resp_data


@app.post("/api/deliveries/webhook", response_model=PoolGroupResponse, tags=["Escrow"])
async def delivery_webhook(
        payload: DeliveryWebhookRequest,
        session: AsyncSession = Depends(get_db),
):
    pool = await _get_pool_by_code(session, payload.group_code)
    pool.bol_reference = payload.bol_reference

    # Safely assign terminal status based on available Enum attributes
    pool.status = getattr(PoolStatus, "COMPLETED", getattr(PoolStatus, "CLOSED", pool.status))

    for p in pool.participants:
        p.status = ParticipantStatus.SETTLED
        for e in p.escrows:
            e.is_settled = True

    await session.commit()
    pool = await _get_pool_by_code(session, payload.group_code)

    resp_model = _build_pool_response(pool)
    return json.loads(json.dumps(resp_model.model_dump(), default=str))


async def _get_pool_by_code(session: AsyncSession, group_code: str) -> PoolGroup:
    stmt = (
        select(PoolGroup)
        .options(selectinload(PoolGroup.participants).selectinload(PoolParticipant.escrows))
        .where(PoolGroup.group_code == group_code)
    )
    res = await session.execute(stmt)
    pool = res.scalar_one_or_none()
    if not pool:
        raise HTTPException(status_code=404, detail=f"Pool group '{group_code}' not found.")
    return pool


def _build_pool_response(pool: PoolGroup) -> PoolGroupResponse:
    moq_pct = (
        (Decimal(pool.current_pooled_units) / Decimal(pool.supplier_moq_units)) * Decimal("100")
        if pool.supplier_moq_units > 0
        else Decimal("0")
    )
    moq_progress = min(moq_pct, Decimal("100.00")).quantize(Decimal("0.01"))

    participants_resp = []
    for p in pool.participants:
        escrows_resp = [
            {
                "id": e.id,
                "stage": e.stage,
                "tx_hash": e.tx_hash,
                "offer_sequence": e.offer_sequence,
                "amount_rlusd": e.amount_rlusd,
                "is_settled": e.is_settled,
                "is_cancelled": e.is_cancelled,
                "settlement_tx_hash": e.settlement_tx_hash,
                "unsigned_tx_json": eval(e.unsigned_tx_json) if e.unsigned_tx_json else None,
            }
            for e in p.escrows
        ]
        participants_resp.append(
            {
                "id": p.id,
                "business_name": p.business_name,
                "buyer_wallet_address": p.buyer_wallet_address,
                "quantity": p.quantity,
                "unit_cost_zar": p.unit_cost_zar,
                "product_savings_zar": getattr(p, "product_savings_zar", Decimal("0.00")),
                "buyer_shipping_discount_zar": p.buyer_shipping_discount_zar,
                "total_buyer_surplus_zar": p.total_buyer_surplus_zar,
                "total_platform_revenue_zar": p.total_platform_revenue_zar,
                "final_amount_zar": p.final_amount_zar,
                "final_amount_rlusd": p.final_amount_rlusd,
                "deposit_amount_zar": p.deposit_amount_zar,
                "deposit_amount_rlusd": p.deposit_amount_rlusd,
                "balance_due_zar": p.balance_due_zar,
                "balance_due_rlusd": p.balance_due_rlusd,
                "ipfs_cid": p.ipfs_cid,
                "policy_path": p.policy_path,
                "status": p.status,
                "escrows": escrows_resp,
            }
        )

    return PoolGroupResponse(
        id=pool.id,
        group_code=pool.group_code,
        product_sku=pool.product_sku,
        product_name=pool.product_name,
        unit_label=pool.unit_label,
        supplier_name=pool.supplier_name,
        supplier_wallet_address=pool.supplier_wallet_address,
        supplier_kyb_verified=pool.supplier_kyb_verified,
        retail_unit_price_zar=pool.retail_unit_price_zar,
        wholesale_unit_price_zar=pool.wholesale_unit_price_zar,
        wholesale_unit_trigger=pool.wholesale_unit_trigger,
        supplier_moq_units=pool.supplier_moq_units,
        current_pooled_units=pool.current_pooled_units,
        moq_progress_pct=moq_progress,
        supplier_hub=pool.supplier_hub,
        delivery_zone=pool.delivery_zone,
        status=pool.status,
        deadline_utc=pool.deadline_utc,
        mpt_issuance_tx_hash=pool.mpt_issuance_tx_hash,
        bol_reference=pool.bol_reference,
        participants=participants_resp,
    )
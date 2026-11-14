# backend/app/services/pricing_engine.py
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

ZAR_QUANT = Decimal("0.01")
RLUSD_QUANT = Decimal("0.000001")

BUYER_SERVICE_FEE_RATE = Decimal("0.0500")       # 5% buyer service fee on (goods + quoted freight)
SUPPLIER_MARKETPLACE_FEE_RATE = Decimal("0.0500") # 5% supplier marketplace fee deducted from goods payout
BUYER_SHIPPING_SURPLUS_SHARE = Decimal("0.2500")  # Buyers receive 25% of gross corridor shipping surplus
PLATFORM_SHIPPING_SURPLUS_SHARE = Decimal("0.7500") # StokSafe retains 75% of gross corridor shipping surplus
DEPOSIT_RATE = Decimal("0.2000")                  # 20% commitment deposit (100% forfeited to StokSafe on buyer default; 100% refunded if pool fails MOQ)

CORRIDOR_FREIGHT_RATES_ZAR: dict[tuple[str, str], dict[str, Decimal]] = {
    ("hub_johannesburg", "zone_1_cape_town"): {
        "solo_base": Decimal("950.00"),
        "solo_per_unit": Decimal("1450.00"),
        "bulk_linehaul_base": Decimal("4200.00"),
        "bulk_per_unit": Decimal("480.00"),
        "local_drop_fee": Decimal("350.00"),
    },
    ("hub_johannesburg", "zone_2_johannesburg"): {
        "solo_base": Decimal("450.00"),
        "solo_per_unit": Decimal("650.00"),
        "bulk_linehaul_base": Decimal("1600.00"),
        "bulk_per_unit": Decimal("210.00"),
        "local_drop_fee": Decimal("200.00"),
    },
    ("hub_cape_town", "zone_1_cape_town"): {
        "solo_base": Decimal("400.00"),
        "solo_per_unit": Decimal("600.00"),
        "bulk_linehaul_base": Decimal("1450.00"),
        "bulk_per_unit": Decimal("190.00"),
        "local_drop_fee": Decimal("180.00"),
    },
    ("hub_durban", "zone_2_johannesburg"): {
        "solo_base": Decimal("750.00"),
        "solo_per_unit": Decimal("1100.00"),
        "bulk_linehaul_base": Decimal("3100.00"),
        "bulk_per_unit": Decimal("360.00"),
        "local_drop_fee": Decimal("280.00"),
    },
}

DEFAULT_CORRIDOR_RATE: dict[str, Decimal] = {
    "solo_base": Decimal("650.00"),
    "solo_per_unit": Decimal("950.00"),
    "bulk_linehaul_base": Decimal("2600.00"),
    "bulk_per_unit": Decimal("320.00"),
    "local_drop_fee": Decimal("250.00"),
}


@dataclass(frozen=True)
class PricingBreakdown:
    quantity: int
    group_total_quantity: int
    wholesale_unit_trigger: int
    units_remaining_to_trigger: int
    buyer_trigger_proximity_pct: Decimal
    effective_discount_pct: Decimal
    retail_unit_price: Decimal
    wholesale_unit_price: Decimal
    unit_cost: Decimal
    unit_savings_zar: Decimal
    product_savings_zar: Decimal
    gross_subtotal_product: Decimal
    supplier_marketplace_fee_zar: Decimal
    supplier_net_payout_zar: Decimal
    supplier_hub: str
    delivery_zone: str
    solo_freight_quote_zar: Decimal
    carrier_actual_cost_zar: Decimal
    gross_shipping_surplus_zar: Decimal
    buyer_shipping_discount_zar: Decimal
    platform_freight_arbitrage_zar: Decimal
    buyer_quoted_freight_zar: Decimal
    buyer_service_fee_zar: Decimal
    total_buyer_surplus_zar: Decimal
    total_platform_revenue_zar: Decimal
    final_amount_zar: Decimal
    final_amount_rlusd: Decimal
    deposit_rate: Decimal
    deposit_amount_zar: Decimal
    deposit_amount_rlusd: Decimal
    balance_due_zar: Decimal
    balance_due_rlusd: Decimal
    deposit_policy_summary: str
    fx_rate_zar_per_rlusd: Decimal

    def to_receipt_dict(self, group_code: str, product_sku: str, business_name: str) -> dict[str, Any]:
        return {
            "schema_version": "stoksafe.receipt.v7",
            "group_code": group_code,
            "product_sku": product_sku,
            "buyer_business": business_name,
            "buyer_units_ordered": self.quantity,
            "group_total_quantity": self.group_total_quantity,
            "wholesale_unit_trigger": self.wholesale_unit_trigger,
            "buyer_trigger_proximity_pct": str(self.buyer_trigger_proximity_pct),
            "effective_discount_pct": str(self.effective_discount_pct),
            "retail_ceiling_unit_price_zar": str(self.retail_unit_price),
            "wholesale_floor_unit_price_zar": str(self.wholesale_unit_price),
            "buyer_unit_price_zar": str(self.unit_cost),
            "product_savings_zar": str(self.product_savings_zar),
            "gross_subtotal_product_zar": str(self.gross_subtotal_product),
            "supplier_marketplace_fee_zar": str(self.supplier_marketplace_fee_zar),
            "supplier_net_payout_zar": str(self.supplier_net_payout_zar),
            "freight_corridor": f"{self.supplier_hub} -> {self.delivery_zone}",
            "solo_freight_quote_zar": str(self.solo_freight_quote_zar),
            "carrier_actual_cost_zar": str(self.carrier_actual_cost_zar),
            "buyer_quoted_freight_zar": str(self.buyer_quoted_freight_zar),
            "buyer_shipping_discount_zar": str(self.buyer_shipping_discount_zar),
            "platform_freight_arbitrage_zar": str(self.platform_freight_arbitrage_zar),
            "buyer_service_fee_zar": str(self.buyer_service_fee_zar),
            "total_buyer_surplus_zar": str(self.total_buyer_surplus_zar),
            "total_platform_revenue_zar": str(self.total_platform_revenue_zar),
            "final_amount_zar": str(self.final_amount_zar),
            "final_amount_rlusd": str(self.final_amount_rlusd),
            "deposit_amount_zar": str(self.deposit_amount_zar),
            "deposit_amount_rlusd": str(self.deposit_amount_rlusd),
            "balance_due_zar": str(self.balance_due_zar),
            "balance_due_rlusd": str(self.balance_due_rlusd),
            "deposit_policy": self.deposit_policy_summary,
            "fx_rate_zar_per_rlusd": str(self.fx_rate_zar_per_rlusd),
        }


def _quantize_zar(value: Decimal) -> Decimal:
    return value.quantize(ZAR_QUANT, rounding=ROUND_HALF_UP)


def _quantize_rlusd(value: Decimal) -> Decimal:
    return value.quantize(RLUSD_QUANT, rounding=ROUND_HALF_UP)


def calculate_corridor_freight_split(
        *,
        supplier_hub: str,
        delivery_zone: str,
        buyer_quantity: int,
        group_total_quantity: int,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]:
    """
    Computes solo vs. carrier bulk freight and splits the gross corridor shipping surplus:
    - 25% passed to buyer as shipping discount
    - 75% retained by StokSafe as freight arbitrage revenue
    """
    corridor = CORRIDOR_FREIGHT_RATES_ZAR.get((supplier_hub, delivery_zone), DEFAULT_CORRIDOR_RATE)

    solo_freight = _quantize_zar(
        corridor["solo_base"] + (corridor["solo_per_unit"] * Decimal(buyer_quantity))
    )

    total_pool_linehaul = corridor["bulk_linehaul_base"] + (
            corridor["bulk_per_unit"] * Decimal(group_total_quantity)
    )
    share_ratio = Decimal(buyer_quantity) / Decimal(group_total_quantity)
    carrier_actual_cost = _quantize_zar((total_pool_linehaul * share_ratio) + corridor["local_drop_fee"])

    gross_surplus = _quantize_zar(max(Decimal("0.00"), solo_freight - carrier_actual_cost))
    buyer_shipping_discount = _quantize_zar(gross_surplus * BUYER_SHIPPING_SURPLUS_SHARE)
    platform_freight_arbitrage = _quantize_zar(gross_surplus - buyer_shipping_discount)
    buyer_quoted_freight = _quantize_zar(solo_freight - buyer_shipping_discount)

    return (
        solo_freight,
        carrier_actual_cost,
        gross_surplus,
        buyer_shipping_discount,
        platform_freight_arbitrage,
        buyer_quoted_freight,
    )


def calculate_floor_ceiling_unit_price(
        *,
        retail_unit_price_zar: Decimal,
        wholesale_unit_price_zar: Decimal,
        buyer_quantity: int,
        wholesale_unit_trigger: int,
) -> tuple[Decimal, Decimal, Decimal]:
    if wholesale_unit_trigger < 1:
        raise ValueError("wholesale_unit_trigger must be at least 1 unit.")
    if wholesale_unit_price_zar > retail_unit_price_zar:
        raise ValueError("wholesale_unit_price_zar (floor) cannot exceed retail_unit_price_zar (ceiling).")

    retail = _quantize_zar(retail_unit_price_zar)
    wholesale = _quantize_zar(wholesale_unit_price_zar)
    spread = retail - wholesale

    raw_proximity = Decimal(buyer_quantity) / Decimal(wholesale_unit_trigger)
    clamped_proximity = min(raw_proximity, Decimal("1.0000"))

    proximity_pct = (clamped_proximity * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    discount_per_unit = _quantize_zar(spread * clamped_proximity)
    buyer_unit_price = _quantize_zar(retail - discount_per_unit)

    effective_discount_pct = (
        ((discount_per_unit / retail) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if retail > Decimal("0.00")
        else Decimal("0.00")
    )

    return proximity_pct, effective_discount_pct, buyer_unit_price


def calculate_participant_pricing(
        *,
        quantity: int,
        new_group_total_quantity: int,
        retail_unit_price_zar: Decimal,
        wholesale_unit_price_zar: Decimal,
        wholesale_unit_trigger: int,
        supplier_hub: str,
        delivery_zone: str,
        fx_rate_zar_per_rlusd: Decimal = Decimal("18.20"),
) -> PricingBreakdown:
    if quantity < 1:
        raise ValueError("Participant quantity must be at least 1 unit.")
    if new_group_total_quantity < quantity:
        raise ValueError("Group total quantity cannot be less than participant quantity.")

    retail_price = _quantize_zar(retail_unit_price_zar)
    wholesale_price = _quantize_zar(wholesale_unit_price_zar)

    # 1. Floor-to-ceiling proximity unit pricing & two-sided supplier fee
    proximity_pct, effective_discount_pct, unit_cost = calculate_floor_ceiling_unit_price(
        retail_unit_price_zar=retail_price,
        wholesale_unit_price_zar=wholesale_price,
        buyer_quantity=quantity,
        wholesale_unit_trigger=wholesale_unit_trigger,
    )

    units_remaining = max(0, wholesale_unit_trigger - quantity)
    unit_savings = _quantize_zar(retail_price - unit_cost)
    product_savings_zar = _quantize_zar(unit_savings * Decimal(quantity))

    gross_subtotal_product = _quantize_zar(unit_cost * Decimal(quantity))
    supplier_marketplace_fee = _quantize_zar(gross_subtotal_product * SUPPLIER_MARKETPLACE_FEE_RATE)
    supplier_net_payout = _quantize_zar(gross_subtotal_product - supplier_marketplace_fee)

    # 2. Corridor freight arbitrage (25% buyer discount / 75% StokSafe revenue)
    (
        solo_freight,
        carrier_actual_cost,
        gross_shipping_surplus,
        buyer_shipping_discount,
        platform_freight_arbitrage,
        buyer_quoted_freight,
    ) = calculate_corridor_freight_split(
        supplier_hub=supplier_hub,
        delivery_zone=delivery_zone,
        buyer_quantity=quantity,
        group_total_quantity=new_group_total_quantity,
    )

    # 3. Buyer 5% service fee & total revenue reconciliation
    buyer_service_fee = _quantize_zar((gross_subtotal_product + buyer_quoted_freight) * BUYER_SERVICE_FEE_RATE)
    total_buyer_surplus = _quantize_zar(product_savings_zar + buyer_shipping_discount)
    total_platform_revenue = _quantize_zar(
        platform_freight_arbitrage + buyer_service_fee + supplier_marketplace_fee
    )

    final_amount_zar = _quantize_zar(gross_subtotal_product + buyer_quoted_freight + buyer_service_fee)
    final_amount_rlusd = _quantize_rlusd(final_amount_zar / fx_rate_zar_per_rlusd)

    # 4. 20% commitment deposit (100% retained by StokSafe if buyer defaults; 100% refunded if pool fails MOQ)
    deposit_amount_zar = _quantize_zar(final_amount_zar * DEPOSIT_RATE)
    balance_due_zar = _quantize_zar(final_amount_zar - deposit_amount_zar)

    deposit_amount_rlusd = _quantize_rlusd(final_amount_rlusd * DEPOSIT_RATE)
    balance_due_rlusd = _quantize_rlusd(final_amount_rlusd - deposit_amount_rlusd)

    deposit_policy_summary = (
        "20% commitment deposit is 100% forfeited to StokSafe if buyer cancels after committing, "
        "and 100% refunded via XRPL EscrowCancel if the group fails to pool minimum SMB units before deadline."
    )

    return PricingBreakdown(
        quantity=quantity,
        group_total_quantity=new_group_total_quantity,
        wholesale_unit_trigger=wholesale_unit_trigger,
        units_remaining_to_trigger=units_remaining,
        buyer_trigger_proximity_pct=proximity_pct,
        effective_discount_pct=effective_discount_pct,
        retail_unit_price=retail_price,
        wholesale_unit_price=wholesale_price,
        unit_cost=unit_cost,
        unit_savings_zar=unit_savings,
        product_savings_zar=product_savings_zar,
        gross_subtotal_product=gross_subtotal_product,
        supplier_marketplace_fee_zar=supplier_marketplace_fee,
        supplier_net_payout_zar=supplier_net_payout,
        supplier_hub=supplier_hub,
        delivery_zone=delivery_zone,
        solo_freight_quote_zar=solo_freight,
        carrier_actual_cost_zar=carrier_actual_cost,
        gross_shipping_surplus_zar=gross_shipping_surplus,
        buyer_shipping_discount_zar=buyer_shipping_discount,
        platform_freight_arbitrage_zar=platform_freight_arbitrage,
        buyer_quoted_freight_zar=buyer_quoted_freight,
        buyer_service_fee_zar=buyer_service_fee,
        total_buyer_surplus_zar=total_buyer_surplus,
        total_platform_revenue_zar=total_platform_revenue,
        final_amount_zar=final_amount_zar,
        final_amount_rlusd=final_amount_rlusd,
        deposit_rate=DEPOSIT_RATE,
        deposit_amount_zar=deposit_amount_zar,
        deposit_amount_rlusd=deposit_amount_rlusd,
        balance_due_zar=balance_due_zar,
        balance_due_rlusd=balance_due_rlusd,
        deposit_policy_summary=deposit_policy_summary,
        fx_rate_zar_per_rlusd=fx_rate_zar_per_rlusd,
    )
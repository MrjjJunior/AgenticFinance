"""
Independent Policy Co-Signer microservice.

This is a SEPARATE service from the procurement agent — different process,
different port (default 8001), own wallet seed, own limits. It exists so
that the spending limits are enforced SOMEWHERE THE AGENT DOES NOT CONTROL:

* The cosigner holds the only copy of its own seed. The agent asks it to
  sign over HTTP and the cosigner decides INDEPENDENTLY, by reading the
  transaction itself (it does not trust the agent's declared amount or
  destination).
* The Human Owner sets the limits through THIS service's admin API —
  never through the agent. Changes take effect immediately.

Endpoints
---------
GET  /health              liveness probe
GET  /limits              current cap, allowlist, spend today
POST /cosign              agent requests the weight-1 signature
POST /admin/limits        Human Owner sets cap / allowlist  (X-Admin-Token)
POST /admin/spend/reset   Human Owner zeroes today's spend    (X-Admin-Token)

Run (from the repo root):
    venv\\Scripts\\python -m uvicorn cosigner_service.main:create_app --factory --port 8001
"""

from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation
from os import getenv as os_getenv
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from xrpl.models.transactions import Transaction
from xrpl.transaction import sign
from xrpl.wallet import Wallet

try:
    # Package import (uvicorn from repo root, pytest)
    from .limits_store import LimitsStore
except ImportError:  # pragma: no cover
    # Flat import (uvicorn with cwd=cosigner_service)
    from limits_store import LimitsStore

logger = logging.getLogger("cosigner_service")

# Shared .env written by setup_wallets.py / setup_demo.py (contains the
# cosigner seed and the seed values for cap / allowlist). Real environment
# variables always take precedence over the file. Loaded inside create_app
# (not at import time) so importing this module in tests stays side-effect free.
_ENV_FILE = Path(__file__).resolve().parent.parent / "procurement_agent" / ".env"

_DEFAULT_STORE_PATH = Path(__file__).resolve().parent / "cosigner_limits.json"


def _env(name: str, default: str = "") -> str:
    return os_getenv(name, default)


def _require_seed_value(name: str) -> str:
    value = os_getenv(name, "")
    if not value:
        raise RuntimeError(
            f"{name} is not set. The cosigner service needs its own wallet "
            f"seed - run procurement_agent/setup_wallets.py first (creates "
            f"procurement_agent/.env), or export {name}."
        )
    return value


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class CosignRequest(BaseModel):
    """
    The agent's cosign request. NOTE: `amount_rlusd` and
    `destination_address` are ADVISORY. The service extracts the
    authoritative amount and destination from `tx_json` itself — a
    compromised agent cannot lie its way past the cap.
    """

    tx_json: dict[str, Any]
    amount_rlusd: str = "0"
    destination_address: str = ""


class AdminLimitsUpdate(BaseModel):
    """Human Owner's limit change. Both fields optional."""

    daily_cap_rlusd: Optional[str] = None
    approved_suppliers: Optional[list[str]] = None


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app(
    seed: Optional[str] = None,
    store_path: Optional[Path] = None,
    admin_token: Optional[str] = None,
    rlusd_currency_hex: Optional[str] = None,
    rlusd_issuer: Optional[str] = None,
    main_account_address: Optional[str] = None,
    seed_daily_cap: Optional[str] = None,
    seed_suppliers: Optional[list[str]] = None,
) -> FastAPI:
    """
    Build the FastAPI app. All parameters optional — defaults come from
    the environment (procurement_agent/.env). Tests inject their own
    wallet/store so they never touch real keys.
    """
    load_dotenv(_ENV_FILE, override=False)

    seed = seed or _require_seed_value("POLICY_COSIGNER_SEED")
    rlusd_currency_hex = (
        rlusd_currency_hex
        or _env("RLUSD_CURRENCY_HEX", "524C555344000000000000000000000000000000")
    )
    rlusd_issuer = rlusd_issuer or _env("RLUSD_ISSUER", "")
    main_account_address = main_account_address or _env("MAIN_ACCOUNT_ADDRESS", "")
    admin_token = admin_token if admin_token is not None else _env("COSIGNER_ADMIN_TOKEN", "")
    store_path = Path(store_path) if store_path else _DEFAULT_STORE_PATH

    seed_daily_cap = seed_daily_cap or _env("DAILY_SPENDING_CAP_RLUSD", "5000.00")
    if seed_suppliers is None:
        raw = _env("APPROVED_SUPPLIER_ADDRESSES", "")
        seed_suppliers = [a.strip() for a in raw.split(",") if a.strip()]

    wallet = Wallet.from_seed(seed)
    store = LimitsStore(store_path, seed_daily_cap, seed_suppliers)

    app = FastAPI(
        title="Policy Co-Signer",
        description=(
            "Independent second-signature service. Enforces the Human "
            "Owner's spending limits somewhere the agent does not control."
        ),
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # demo: frontend opened via file://
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    @app.get("/health", tags=["Health"])
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": "policy-cosigner",
            "cosigner_address": wallet.classic_address,
        }

    # ------------------------------------------------------------------
    # Limits (read-only) — what the agent's mandate check reads
    # ------------------------------------------------------------------

    @app.get("/limits", tags=["Limits"])
    def limits() -> dict[str, Any]:
        return store.snapshot()

    # ------------------------------------------------------------------
    # Admin API — THE HUMAN OWNER'S control plane
    # ------------------------------------------------------------------

    def _check_admin(header_token: Optional[str]) -> None:
        if admin_token and header_token != admin_token:
            raise HTTPException(
                status_code=403,
                detail={"refused": True, "reason": "Invalid or missing X-Admin-Token."},
            )

    @app.post("/admin/limits", tags=["Admin"])
    def set_limits(
        update: AdminLimitsUpdate,
        x_admin_token: Optional[str] = Header(default=None),
    ) -> dict[str, Any]:
        _check_admin(x_admin_token)

        new_cap: Optional[Decimal] = None
        if update.daily_cap_rlusd is not None:
            try:
                new_cap = Decimal(update.daily_cap_rlusd)
            except InvalidOperation as exc:
                raise HTTPException(
                    status_code=422,
                    detail={"reason": f"daily_cap_rlusd is not a number: {exc}"},
                ) from exc
            if new_cap <= 0:
                raise HTTPException(
                    status_code=422,
                    detail={"reason": "daily_cap_rlusd must be positive."},
                )

        new_suppliers: Optional[list[str]] = None
        if update.approved_suppliers is not None:
            new_suppliers = [s.strip() for s in update.approved_suppliers if s.strip()]
            if not new_suppliers:
                raise HTTPException(
                    status_code=422,
                    detail={"reason": "approved_suppliers must contain at least one address."},
                )

        snapshot = store.set_limits(daily_cap=new_cap, suppliers=new_suppliers)
        logger.warning(
            "ADMIN LIMIT CHANGE | cap=%s | suppliers=%d",
            snapshot["daily_cap_rlusd"],
            len(snapshot["approved_suppliers"]),
        )
        return snapshot

    @app.post("/admin/spend/reset", tags=["Admin"])
    def reset_spend(x_admin_token: Optional[str] = Header(default=None)) -> dict[str, Any]:
        _check_admin(x_admin_token)
        logger.warning("ADMIN SPEND RESET by Human Owner")
        return store.reset_spend()

    # ------------------------------------------------------------------
    # Cosign — the agent asks; the service decides
    # ------------------------------------------------------------------

    def _refused(reason: str) -> HTTPException:
        return HTTPException(
            status_code=403,
            detail={"refused": True, "reason": reason},
        )

    def _extract_payment(tx_json: dict[str, Any]) -> Optional[tuple[Decimal, str]]:
        """
        Self-inspect the transaction. Returns (value, destination) for a
        real RLUSD payment, or None for administrative ops (TicketCreate,
        TrustSet, ...) that move no funds and are not subject to payment
        rules. Raises 403 for anything suspicious.
        """
        tx_type = tx_json.get("TransactionType", "")
        if tx_type != "Payment":
            return None

        amount = tx_json.get("Amount")
        # An XRP payment is a drops-STRING amount; the pool account may
        # only ever move RLUSD, never XRP.
        if isinstance(amount, str):
            raise _refused(
                "Refusing an XRP payment: the stokvel pool account may only "
                "send RLUSD (IOU) payments, never XRP."
            )
        if not isinstance(amount, dict):
            raise _refused("Payment has no recognizable RLUSD amount.")

        currency = str(amount.get("currency", ""))
        if currency.upper() != rlusd_currency_hex.upper():
            shown = currency if len(currency) <= 20 else currency[:17] + "..."
            raise _refused(
                f"Refusing non-RLUSD token payment (currency={shown}). Only "
                "RLUSD may leave the pool."
            )

        try:
            value = Decimal(str(amount.get("value", "0")))
        except InvalidOperation as exc:
            raise _refused(f"Payment amount is not a valid number: {exc}") from exc
        if value <= 0:
            raise _refused("Payment value must be positive.")

        destination = str(tx_json.get("Destination", ""))
        if not destination:
            raise _refused("Payment has no destination.")
        return value, destination

    def _enforce_payment_policy(value: Decimal, destination: str, tx_json: dict[str, Any]) -> None:
        """THE independent checks — same as an on-ledger guard would be."""
        cap = Decimal(store.snapshot()["daily_cap_rlusd"])
        errors: list[str] = []

        if value > cap:
            errors.append(
                f"Amount {value} RLUSD exceeds the daily cap of {cap} RLUSD"
            )

        spent = Decimal(store.snapshot()["spent_today_rlusd"])
        if spent + value > cap:
            errors.append(
                f"Payment of {value} RLUSD would bring today's signed spend "
                f"to {spent + value} RLUSD, exceeding the daily cap of {cap} RLUSD"
            )

        allowlist = store.snapshot()["approved_suppliers"]
        if destination not in allowlist:
            errors.append(
                f"Destination {destination} is NOT on the cosigner's approved "
                "supplier list (set by the Human Owner)"
            )

        if rlusd_issuer and _amount_issuer_mismatch(tx_json):
            errors.append(
                "Payment amount is not issued by the configured RLUSD issuer"
            )

        if errors:
            raise _refused("; ".join(errors))

    def _amount_issuer_mismatch(tx_json: dict[str, Any]) -> bool:
        amount = tx_json.get("Amount")
        if isinstance(amount, dict):
            return str(amount.get("issuer", "")) != rlusd_issuer
        return False

    @app.post("/cosign", tags=["Cosign"])
    def cosign(request: CosignRequest) -> dict[str, Any]:
        tx_json = request.tx_json

        # 1. The transaction MUST originate from the stokvel pool account.
        #    The cosigner refuses to be used as a signing oracle for
        #    anyone else's transactions.
        if main_account_address and tx_json.get("Account") != main_account_address:
            raise _refused(
                "Transaction Account does not match the stokvel pool account "
                "the cosigner is bound to."
            )

        # 2. Rebuild the transaction exactly as the agent serialized it.
        #    (Round-trip verified: signatures over the rebuilt tx are
        #    byte-identical to signatures over the original object.)
        try:
            tx = Transaction.from_xrpl(tx_json)
            tx.validate()
        except Exception as exc:  # noqa: BLE001
            raise _refused(f"Could not parse transaction: {exc}") from exc

        # 3. Self-inspect: is this a real RLUSD payment, and may it proceed?
        payment = _extract_payment(tx_json)
        recorded_spend: Optional[Decimal] = None
        if payment is not None:
            value, destination = payment
            _enforce_payment_policy(value, destination, tx_json)

        # 4. Sign with the cosigner's OWN seed (multisign -> Signers array).
        signed = sign(tx, wallet, multisign=True)
        blob = signed.blob()

        # 5. Bookkeeping: record signed spend for REAL payments only.
        if payment is not None:
            recorded_spend = store.record_spend(payment[0])
            logger.warning(
                "COSIGNED payment | value=%s RLUSD | destination=%s | spend_today=%s",
                payment[0],
                payment[1],
                recorded_spend,
            )
        else:
            logger.info(
                "COSIGNED admin op | type=%s (no funds at risk)",
                tx_json.get("TransactionType", "?"),
            )

        return {
            "signed_tx_blob": blob,
            "cosigner_address": wallet.classic_address,
            "recorded_spend_rlusd": str(recorded_spend) if recorded_spend is not None else "0",
        }

    return app

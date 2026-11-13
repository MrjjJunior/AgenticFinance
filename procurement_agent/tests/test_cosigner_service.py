"""
Tests for the independent Policy Co-Signer microservice.

Runs the service in-process (fastapi TestClient) with a throwaway wallet
and a temp-file limits store — no Testnet, no real keys.

The cosign requests below deliberately declare WRONG amount/destination
values, proving the service self-inspects the transaction instead of
trusting the agent.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from xrpl.wallet import Wallet

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cosigner_service.main import create_app  # noqa: E402

RLUSD_HEX = "524C555344000000000000000000000000000000"
MAIN = str(Wallet.create().classic_address)
SUPPLIER = str(Wallet.create().classic_address)
ISSUER = str(Wallet.create().classic_address)
STRANGER = str(Wallet.create().classic_address)


@pytest.fixture()
def cosigner(tmp_path):
    app = create_app(
        seed=Wallet.create().seed,
        store_path=tmp_path / "cosigner_limits.json",
        admin_token="test-token",
        rlusd_currency_hex=RLUSD_HEX,
        rlusd_issuer=ISSUER,
        main_account_address=MAIN,
        seed_daily_cap="1000.00",
        seed_suppliers=[SUPPLIER],
    )
    return TestClient(app)


def _payment(
    destination: str = SUPPLIER,
    value: str = "500",
    issuer: str = ISSUER,
    currency: str = RLUSD_HEX,
    account: str = MAIN,
) -> dict:
    return {
        "TransactionType": "Payment",
        "Account": account,
        "Destination": destination,
        "Amount": {"currency": currency, "issuer": issuer, "value": value},
    }


def _cosign(client: TestClient, tx_json: dict) -> object:
    """
    Send a cosign request with DELIBERATELY WRONG advisory fields
    (amount 999, destination = a stranger) — the service must ignore
    them and self-inspect tx_json.
    """
    return client.post(
        "/cosign",
        json={
            "tx_json": tx_json,
            "amount_rlusd": "999",           # lie
            "destination_address": STRANGER,  # lie
        },
    )


# ---------------------------------------------------------------------------
# Happy path: independent signing + spend bookkeeping
# ---------------------------------------------------------------------------

def test_payment_within_cap_is_signed_and_spend_recorded(cosigner):
    resp = _cosign(cosigner, _payment(value="500"))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["signed_tx_blob"]
    assert data["cosigner_address"].startswith("r")
    # Spend was recorded from the TX (500), not from the agent's declared
    # 999 — the service self-inspects.
    assert data["recorded_spend_rlusd"] == "500"
    limits = cosigner.get("/limits").json()
    assert limits["spent_today_rlusd"] == "500"
    assert limits["daily_cap_rlusd"] == "1000.00"


def test_admin_op_ticketcreate_is_signed_without_payment_rules(cosigner):
    resp = _cosign(
        cosigner,
        {"TransactionType": "TicketCreate", "Account": MAIN, "TicketCount": 1},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["recorded_spend_rlusd"] == "0"
    assert cosigner.get("/limits").json()["spent_today_rlusd"] == "0"


# ---------------------------------------------------------------------------
# Independent refusals — the whole point of the separate service
# ---------------------------------------------------------------------------

def test_payment_over_cap_refused(cosigner):
    resp = _cosign(cosigner, _payment(value="1500"))
    assert resp.status_code == 403
    detail = resp.json()["detail"]
    assert detail["refused"] is True
    assert "cap" in detail["reason"].lower()
    assert cosigner.get("/limits").json()["spent_today_rlusd"] == "0"


def test_cumulative_spend_over_cap_refused(cosigner):
    assert _cosign(cosigner, _payment(value="700")).status_code == 200
    # 700 + 400 = 1100 > cap 1000
    resp = _cosign(cosigner, _payment(value="400"))
    assert resp.status_code == 403
    assert "exceed" in resp.json()["detail"]["reason"].lower()


def test_unapproved_destination_refused(cosigner):
    resp = _cosign(cosigner, _payment(destination=STRANGER, value="100"))
    assert resp.status_code == 403
    assert "approved supplier list" in resp.json()["detail"]["reason"]


def test_xrp_payment_refused(cosigner):
    # A string Amount = XRP drops. Build it explicitly here.
    tx = {
        "TransactionType": "Payment",
        "Account": MAIN,
        "Destination": SUPPLIER,
        "Amount": "1000000",
    }
    resp = _cosign(cosigner, tx)
    assert resp.status_code == 403
    assert "xrp" in resp.json()["detail"]["reason"].lower()


def test_non_rlusd_token_refused(cosigner):
    resp = _cosign(cosigner, _payment(value="100", currency="USD"))
    assert resp.status_code == 403
    assert "rlusd" in resp.json()["detail"]["reason"].lower()


def test_wrong_issuer_refused(cosigner):
    resp = _cosign(cosigner, _payment(value="100", issuer=STRANGER))
    assert resp.status_code == 403
    assert "issuer" in resp.json()["detail"]["reason"].lower()


def test_transaction_from_another_account_refused(cosigner):
    """The cosigner must never be a signing oracle for other accounts."""
    resp = _cosign(cosigner, _payment(account=STRANGER, value="100"))
    assert resp.status_code == 403
    assert "pool account" in resp.json()["detail"]["reason"]


# ---------------------------------------------------------------------------
# Human Owner control plane
# ---------------------------------------------------------------------------

def test_admin_limits_requires_token(cosigner):
    resp = cosigner.post("/admin/limits", json={"daily_cap_rlusd": "10.00"})
    assert resp.status_code == 403
    resp = cosigner.post(
        "/admin/limits",
        json={"daily_cap_rlusd": "10.00"},
        headers={"X-Admin-Token": "wrong"},
    )
    assert resp.status_code == 403


def test_admin_cap_change_enforced_immediately(cosigner):
    resp = cosigner.post(
        "/admin/limits",
        json={"daily_cap_rlusd": "100.00"},
        headers={"X-Admin-Token": "test-token"},
    )
    assert resp.status_code == 200
    assert resp.json()["daily_cap_rlusd"] == "100.00"

    # A payment that was fine under the old cap is now refused.
    resp = _cosign(cosigner, _payment(value="500"))
    assert resp.status_code == 403
    assert "cap of 100.00" in resp.json()["detail"]["reason"]


def test_admin_allowlist_change_enforced(cosigner):
    resp = cosigner.post(
        "/admin/limits",
        json={"approved_suppliers": [STRANGER]},
        headers={"X-Admin-Token": "test-token"},
    )
    assert resp.status_code == 200

    resp = _cosign(cosigner, _payment(destination=SUPPLIER, value="100"))
    assert resp.status_code == 403


def test_admin_spend_reset(cosigner):
    assert _cosign(cosigner, _payment(value="500")).status_code == 200
    resp = cosigner.post(
        "/admin/spend/reset", headers={"X-Admin-Token": "test-token"}
    )
    assert resp.status_code == 200
    assert resp.json()["spent_today_rlusd"] == "0"
    # And spending works again after the reset.
    assert _cosign(cosigner, _payment(value="500")).status_code == 200


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def test_limits_survive_service_restart(tmp_path):
    store_path = tmp_path / "cosigner_limits.json"

    first = TestClient(
        create_app(
            seed=Wallet.create().seed,
            store_path=store_path,
            admin_token="t",
            rlusd_currency_hex=RLUSD_HEX,
            rlusd_issuer=ISSUER,
            main_account_address=MAIN,
            seed_daily_cap="1000.00",
            seed_suppliers=[SUPPLIER],
        )
    )
    first.post(
        "/admin/limits",
        json={"daily_cap_rlusd": "55.55", "approved_suppliers": [SUPPLIER, STRANGER]},
        headers={"X-Admin-Token": "t"},
    )

    # Second "restart": different seed values, same store — human's values win.
    second = TestClient(
        create_app(
            seed=Wallet.create().seed,
            store_path=store_path,
            admin_token="t",
            rlusd_currency_hex=RLUSD_HEX,
            rlusd_issuer=ISSUER,
            main_account_address=MAIN,
            seed_daily_cap="9999.00",
            seed_suppliers=[],
        )
    )
    limits = second.get("/limits").json()
    assert limits["daily_cap_rlusd"] == "55.55"
    assert limits["approved_suppliers"] == [SUPPLIER, STRANGER]

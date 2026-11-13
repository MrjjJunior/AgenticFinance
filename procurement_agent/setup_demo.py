"""
One-shot demo setup: provisions everything needed so the Procurement Agent can
execute a REAL autonomous payment on XRPL Testnet (Path A) and get blocked on
over-cap invoices (Path B).

WHAT IT DOES
------------
1. Funds 3 fresh Testnet accounts from the faucet:
       SUPPLIER    - the vendor that will receive the RLUSD payment
       ISSUER      - issues our Testnet RLUSD (replaces the placeholder issuer)
       KYB AUTH    - trusted authority that issues the KYBVerified credential
2. Main account (agent + cosigner MULTISIG - master key is disabled):
       TrustSet to accept RLUSD from the new issuer.
3. Issuer pays the main account 25,000 RLUSD.
4. Supplier sets its own RLUSD trustline (so it can receive the payment).
5. KYB authority issues an XLS-70 `KYBVerified` credential to the supplier,
   and the supplier accepts it.
6. Verifies the ledger state EXACTLY the way the agent's Step 2 does
   (account_objects type=CREDENTIAL, hex CredentialType match).
7. Updates .env (RLUSD_ISSUER, APPROVED_SUPPLIER_ADDRESSES, new seeds) and
   patches frontend/index.html so the "Load demo data" button targets the
   real supplier.

AFTER RUNNING
-------------
Restart the backend, then demo:
    APPROVED  : submit the demo invoice (1,480 RLUSD, within the 5,000 cap)
    ESCALATED : tick "simulate a different invoice" and set total 6,000 RLUSD
                (1,480 + 6,000 > 5,000 cap -> agent refuses, returns blob)

Run from procurement_agent/:
    .\\venv\\Scripts\\python setup_demo.py

Testnet only. Never reuse these keys on Mainnet.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from xrpl.clients import JsonRpcClient
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import AccountLines, AccountObjects, AccountObjectType, Feature
from xrpl.models.transactions import CredentialAccept, CredentialCreate, Payment, TrustSet
from xrpl.models.transactions.account_set import AccountSet, AccountSetAsfFlag
from xrpl.models.transactions.trust_set import TrustSetFlag
from xrpl.transaction import autofill, multisign, sign, submit_and_wait
from xrpl.wallet import Wallet, generate_faucet_wallet

TESTNET_URL = "https://s.altnet.rippletest.net:51234/"
ENV_PATH = Path(__file__).resolve().parent / ".env"
FRONTEND_PATH = Path(__file__).resolve().parent.parent / "frontend" / "index.html"

RLUSD_HEX = "524C555344000000000000000000000000000000"  # "RLUSD" + zero padding
KYB_TYPE_HEX = "KYBVerified".encode().hex().upper()
KYB_URI_HEX = "https://stokvel-kyb.example/supplier".encode().hex().upper()
TRUSTLINE_LIMIT = "1000000"
ISSUE_AMOUNT = "25000"

OLD_DEMO_SUPPLIER = "rSupplierAlpha000000000000000000"


def step(msg: str) -> None:
    print(f"\n=== {msg}")


def _ok(label: str, response) -> None:
    result = response.result["meta"]["TransactionResult"]
    if result != "tesSUCCESS":
        print(f"    [FAIL] {label}: {result}")
        raise SystemExit(1)
    print(f"    [OK] {label} -> tesSUCCESS  hash={response.result.get('hash', '')[:16]}...")


# ---------------------------------------------------------------------------
# .env helpers
# ---------------------------------------------------------------------------

def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    return env


def upsert_env_line(key: str, value: str) -> None:
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    found = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            found = True
            break
    if not found:
        lines.append(f"{key}={value}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Submission helpers
# ---------------------------------------------------------------------------

def fund_wallet(label: str) -> Wallet:
    client = JsonRpcClient(TESTNET_URL)
    for attempt in range(1, 4):
        try:
            print(f"    [{label}] requesting funds from Testnet faucet (attempt {attempt})...")
            return generate_faucet_wallet(client)
        except Exception as exc:  # noqa: BLE001
            if attempt == 3:
                raise
            print(f"    [{label}] failed: {exc} - retrying in 10s...")
            time.sleep(10)


def submit_single(tx, client: JsonRpcClient, wallet: Wallet, label: str):
    response = submit_and_wait(tx, client, wallet)
    _ok(label, response)
    return response


def submit_multisig(tx, client: JsonRpcClient, agent: Wallet, cosigner: Wallet, label: str):
    """Main-account transactions: agent (w=1) + cosigner (w=1) = quorum 2."""
    autofilled = autofill(tx, client, signers_count=2)
    sig_agent = sign(autofilled, agent, multisign=True)
    sig_cosigner = sign(autofilled, cosigner, multisign=True)
    combined = multisign(autofilled, [sig_agent, sig_cosigner])
    response = submit_and_wait(combined, client)
    _ok(label, response)
    return response


# ---------------------------------------------------------------------------
# Verification (mirrors the agent's Step 2 logic exactly)
# ---------------------------------------------------------------------------

def verify_kyb_credential(client: JsonRpcClient, supplier_address: str) -> bool:
    request = AccountObjects(account=supplier_address, type=AccountObjectType.CREDENTIAL)
    objects = client.request(request).result.get("account_objects", [])
    for obj in objects:
        if (
            obj.get("LedgerEntryType") == "Credential"
            and obj.get("CredentialType", "").upper() == KYB_TYPE_HEX
        ):
            return True
    return False


def get_rlusd_balance(client: JsonRpcClient, account: str) -> float:
    response = client.request(AccountLines(account=account))
    total = 0.0
    for line in response.result.get("lines", []):
        if line.get("currency", "").upper() == RLUSD_HEX:
            total += float(line.get("balance", "0"))
    return total


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    env = load_env()
    main_address = env.get("MAIN_ACCOUNT_ADDRESS", "")
    agent_seed = env.get("AGENT_SEED", "")
    cosigner_seed = env.get("POLICY_COSIGNER_SEED", "")

    if not (main_address and agent_seed and cosigner_seed):
        print("ERROR: run setup_wallets.py first (needs MAIN_ACCOUNT_ADDRESS,")
        print("AGENT_SEED and POLICY_COSIGNER_SEED in .env).")
        return 1

    client = JsonRpcClient(TESTNET_URL)
    agent_wallet = Wallet.from_seed(agent_seed)
    cosigner_wallet = Wallet.from_seed(cosigner_seed)

    step("0/9 Checking Credentials (XLS-70) amendment on Testnet...")
    features = client.request(Feature()).result.get("features", {})
    cred_feature = [f for f in features.values() if f.get("name") == "Credentials"]
    if not cred_feature or not cred_feature[0].get("enabled"):
        print("    [FAIL] Credentials amendment not enabled on this network.")
        return 1
    print("    [OK] Credentials amendment enabled")

    step("1/9 Funding SUPPLIER, ISSUER and KYB-AUTHORITY wallets (3 faucet calls)...")
    supplier = fund_wallet("SUPPLY")
    issuer = fund_wallet("ISSUER")
    kyb_authority = fund_wallet("KYBAUT")
    print(f"    Supplier     : {supplier.classic_address}")
    print(f"    RLUSD issuer : {issuer.classic_address}")
    print(f"    KYB authority: {kyb_authority.classic_address}")

    step("2/9 Issuer enables Default Ripple BEFORE any lines are created "
         "(line flags are baked in at creation)...")
    submit_single(
        AccountSet(
            account=issuer.classic_address,
            set_flag=AccountSetAsfFlag.ASF_DEFAULT_RIPPLE,
        ),
        client, issuer, "DefaultRipple (issuer)",
    )

    step("3/9 Main account (multisig): RLUSD trustline to new issuer...")
    submit_multisig(
        TrustSet(
            account=main_address,
            limit_amount=IssuedCurrencyAmount(
                currency=RLUSD_HEX, issuer=issuer.classic_address, value=TRUSTLINE_LIMIT
            ),
        ),
        client, agent_wallet, cosigner_wallet, "TrustSet (main)",
    )

    step("4/9 Issuer pays main account 25,000 RLUSD...")
    submit_single(
        Payment(
            account=issuer.classic_address,
            destination=main_address,
            amount=IssuedCurrencyAmount(
                currency=RLUSD_HEX, issuer=issuer.classic_address, value=ISSUE_AMOUNT
            ),
        ),
        client, issuer, "RLUSD issue -> main",
    )

    step("5/9 Supplier sets RLUSD trustline...")
    submit_single(
        TrustSet(
            account=supplier.classic_address,
            limit_amount=IssuedCurrencyAmount(
                currency=RLUSD_HEX, issuer=issuer.classic_address, value=TRUSTLINE_LIMIT
            ),
        ),
        client, supplier, "TrustSet (supplier)",
    )

    step("6/9 Issuer clears NoRipple on its side of both lines (safety net: "
         "holder-to-holder transfers ripple THROUGH the issuer)...")
    for counterparty, label in ((main_address, "main"), (supplier.classic_address, "supplier")):
        submit_single(
            TrustSet(
                account=issuer.classic_address,
                limit_amount=IssuedCurrencyAmount(
                    currency=RLUSD_HEX, issuer=counterparty, value=TRUSTLINE_LIMIT
                ),
                flags=TrustSetFlag.TF_CLEAR_NO_RIPPLE,
            ),
            client, issuer, f"ClearNoRipple ({label})",
        )

    step("7/9 KYB authority issues XLS-70 'KYBVerified' credential to supplier...")
    submit_single(
        CredentialCreate(
            account=kyb_authority.classic_address,
            subject=supplier.classic_address,
            credential_type=KYB_TYPE_HEX,
            uri=KYB_URI_HEX,
        ),
        client, kyb_authority, "CredentialCreate",
    )

    step("8/9 Supplier accepts the credential...")
    submit_single(
        CredentialAccept(
            account=supplier.classic_address,
            issuer=kyb_authority.classic_address,
            credential_type=KYB_TYPE_HEX,
        ),
        client, supplier, "CredentialAccept",
    )

    step("9/9 Verifying ledger state the way the agent's Step 2 does...")
    if not verify_kyb_credential(client, supplier.classic_address):
        print("    [FAIL] agent-style KYB check did NOT find the credential!")
        return 1
    print(f"    [OK] KYB credential visible for {supplier.classic_address}")
    main_balance = get_rlusd_balance(client, main_address)
    print(f"    [OK] main account RLUSD balance: {main_balance:,.2f}")
    if main_balance <= 0:
        print("    [FAIL] main account holds no RLUSD")
        return 1

    # ------------------------------------------------------------------ .env
    step("Updating .env ...")
    print(f"    RLUSD_ISSUER: {env.get('RLUSD_ISSUER', '(unset)')} -> {issuer.classic_address}")
    upsert_env_line("RLUSD_ISSUER", issuer.classic_address)
    upsert_env_line("APPROVED_SUPPLIER_ADDRESSES", supplier.classic_address)
    upsert_env_line("SUPPLIER_ADDRESS", supplier.classic_address)
    upsert_env_line("ISSUER_SEED", issuer.seed)
    upsert_env_line("SUPPLIER_SEED", supplier.seed)
    upsert_env_line("KYB_AUTHORITY_ADDRESS", kyb_authority.classic_address)
    upsert_env_line("KYB_AUTHORITY_SEED", kyb_authority.seed)
    print(f"    Wrote {ENV_PATH}")

    # ------------------------------------------------------------- frontend
    if FRONTEND_PATH.exists():
        import re

        text = FRONTEND_PATH.read_text(encoding="utf-8")
        pattern = re.compile(r'orderSupplier: "[^"]*"')
        if pattern.search(text):
            FRONTEND_PATH.write_text(
                pattern.sub(f'orderSupplier: "{supplier.classic_address}"', text, count=1),
                encoding="utf-8",
            )
            print(f"    Patched frontend demo data to use supplier {supplier.classic_address}")
        else:
            print("    Note: could not find demo supplier in index.html -")
            print("          update the demo fields manually.")
    else:
        print("    Note: frontend/index.html not found - skipped patching.")

    # ------------------------------------------------------------- summary
    print("\nSETUP COMPLETE. Demo script for the judges:")
    print("  1. Restart the backend:  .\\venv\\Scripts\\python -m uvicorn app.main:app --reload")
    print("  2. frontend/index.html -> Load demo data -> Process invoice")
    print(f"     APPROVED (Path A): 1,480 RLUSD < 5,000 cap -> autonomous payment,")
    print(f"     agent + cosigner only, explorer link in the result card.")
    print(f"  3. Tick 'Simulate a different invoice' and set stated total 6000:")
    print(f"     ESCALATED (Path B): 1,480 spent + 6,000 > 5,000 cap -> agent")
    print(f"     refuses, returns partially-signed blob for the weight-2 owner.")
    print("  (Restarting the server resets the in-memory daily spend.)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(130)

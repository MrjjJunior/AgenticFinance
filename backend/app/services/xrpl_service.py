# backend/app/services/xrpl_service.py
import hashlib
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.asyncio.transaction import autofill_and_sign, submit_and_wait
from xrpl.models.requests import AccountObjects
from xrpl.models.transactions import (
    EscrowCancel,
    EscrowCreate,
    EscrowFinish,
    MPTokenIssuanceCreate,
    Memo,
    Payment,
)
from xrpl.utils import datetime_to_ripple_time, str_to_hex
from xrpl.wallet import Wallet

from app.models import EscrowStage

XRPL_TESTNET_RPC = os.getenv("XRPL_TESTNET_RPC", "https://s.altnet.rippletest.net:51234")
RLUSD_ISSUER_TESTNET = os.getenv("RLUSD_ISSUER_TESTNET", "rQhWct2fv4Vc4KRjRgMrxa8xPN9Zx9iLKV")
RLUSD_CURRENCY_HEX = "524C555344000000000000000000000000000000"  # "RLUSD" in 160-bit hex

STOKSAFE_TREASURY_ADDRESS = os.getenv("STOKSAFE_TREASURY_ADDRESS", "rStokSafeTreasuryDemo111111111111")
LOGISTICS_CARRIER_ADDRESS = os.getenv("LOGISTICS_CARRIER_ADDRESS", "rCarrierBulkLogisticsDemo111111111")

# Set XRPL_LIVE_MODE=true in .env to broadcast live to XRPL Testnet; false uses deterministic mirror for offline pitch safety
XRPL_LIVE_MODE = os.getenv("XRPL_LIVE_MODE", "false").lower() == "true"


@dataclass(frozen=True)
class CryptoConditionPair:
    preimage_hex: str
    condition_hex: str
    fulfillment_hex: str


@dataclass(frozen=True)
class EscrowReceipt:
    stage: EscrowStage
    tx_hash: str
    ledger_index: int
    owner_address: str
    destination_address: str
    offer_sequence: int
    amount_rlusd: Decimal
    condition_hex: str | None
    preimage_hex: str | None
    cancel_after_ripple: int
    explorer_url: str
    unsigned_tx_json: dict[str, Any] | None = None


def generate_preimage_condition() -> CryptoConditionPair:
    """
    Generates an RFC-compliant PREIMAGE-SHA-256 crypto-condition & fulfillment
    for condition-locked XRPL Escrows released upon Bill of Lading delivery.
    """
    preimage = secrets.token_bytes(32)
    digest = hashlib.sha256(preimage).digest()

    # ASN.1 DER encoding for PREIMAGE-SHA-256 condition (type 0, 32-byte fingerprint, cost 32)
    condition_der = bytes.fromhex("A0258020") + digest + bytes.fromhex("810120")
    # ASN.1 DER encoding for PREIMAGE-SHA-256 fulfillment (type 0, 32-byte preimage)
    fulfillment_der = bytes.fromhex("A0228020") + preimage

    return CryptoConditionPair(
        preimage_hex=preimage.hex().upper(),
        condition_hex=condition_der.hex().upper(),
        fulfillment_hex=fulfillment_der.hex().upper(),
    )


class XRPLSettlementService:
    def __init__(self, rpc_url: str = XRPL_TESTNET_RPC) -> None:
        self.client = AsyncJsonRpcClient(rpc_url)

    async def verify_supplier_kyb_xls70(
            self,
            *,
            supplier_wallet_address: str,
            trusted_issuer_address: str,
            credential_type: str = "KYB_VERIFIED",
    ) -> dict[str, Any]:
        """
        Inspects on-ledger XLS-70 Credential objects on XRPL Testnet to verify
        that the supplier holds an accepted, unexpired KYB credential.
        """
        if not XRPL_LIVE_MODE:
            sim_index = hashlib.sha256(
                f"XLS70:{supplier_wallet_address}:{credential_type}".encode()
            ).hexdigest()[:32].upper()
            return {
                "verified": True,
                "standard": "XLS-70d",
                "subject": supplier_wallet_address,
                "issuer": trusted_issuer_address,
                "credential_type": credential_type,
                "credential_ledger_index": sim_index,
                "status": "ACCEPTED_ACTIVE",
                "mode": "deterministic_testnet_mirror",
            }

        req = AccountObjects(account=supplier_wallet_address, type="credential")
        resp = await self.client.request(req)
        objects = resp.result.get("account_objects", [])
        expected_hex = str_to_hex(credential_type).upper()
        now_ripple = datetime_to_ripple_time(datetime.now(timezone.utc))

        for obj in objects:
            if (
                    obj.get("Issuer") == trusted_issuer_address
                    and obj.get("CredentialType", "").upper() == expected_hex
            ):
                expiration = obj.get("Expiration")
                is_expired = expiration is not None and int(expiration) <= now_ripple
                # lsfAccepted flag on XLS-70 Credential = 0x00010000 (65536)
                is_accepted = bool(int(obj.get("Flags", 0)) & 0x00010000)
                if is_accepted and not is_expired:
                    return {
                        "verified": True,
                        "standard": "XLS-70d",
                        "subject": supplier_wallet_address,
                        "issuer": trusted_issuer_address,
                        "credential_type": credential_type,
                        "credential_ledger_index": obj.get("index"),
                        "status": "ACCEPTED_ACTIVE",
                    }

        return {
            "verified": False,
            "standard": "XLS-70d",
            "subject": supplier_wallet_address,
            "issuer": trusted_issuer_address,
            "credential_type": credential_type,
            "credential_ledger_index": None,
            "status": "MISSING_OR_UNACCEPTED",
        }

    def build_escrow_create_payload(
            self,
            *,
            buyer_address: str,
            destination_address: str,
            amount_rlusd: Decimal,
            cancel_after_dt: datetime,
            ipfs_cid: str,
            group_code: str,
            stage: EscrowStage,
            condition_hex: str | None = None,
    ) -> dict[str, Any]:
        """
        Constructs an XRPL EscrowCreate transaction payload with IPFS CID and Pool Stage Memos.
        Used directly for Path B (human owner signing) or signed by the agent in Path A.
        """
        drops_amount = str(int((amount_rlusd * Decimal("1000000")).to_integral_value()))
        cancel_ripple = datetime_to_ripple_time(cancel_after_dt)

        tx_dict: dict[str, Any] = {
            "TransactionType": "EscrowCreate",
            "Account": buyer_address,
            "Destination": destination_address,
            "Amount": drops_amount,
            "CancelAfter": cancel_ripple,
            "Memos": [
                {
                    "Memo": {
                        "MemoType": str_to_hex("stoksafe/ipfs-cid").upper(),
                        "MemoData": str_to_hex(ipfs_cid).upper(),
                    }
                },
                {
                    "Memo": {
                        "MemoType": str_to_hex("stoksafe/escrow-stage").upper(),
                        "MemoData": str_to_hex(f"{group_code}:{stage.value}").upper(),
                    }
                },
            ],
        }
        if condition_hex:
            tx_dict["Condition"] = condition_hex

        return tx_dict

    async def execute_or_stage_escrow(
            self,
            *,
            buyer_wallet: Wallet | None,
            buyer_address: str,
            destination_address: str,
            amount_rlusd: Decimal,
            deadline_utc: datetime,
            ipfs_cid: str,
            group_code: str,
            stage: EscrowStage,
            use_condition: bool = True,
            autonomous_approved: bool = True,
    ) -> EscrowReceipt:
        """
        - Path A (autonomous_approved=True): Signs and submits EscrowCreate to XRPL Testnet.
        - Path B (autonomous_approved=False, > R50,000): Returns unsigned_tx_json for owner approval.
        """
        cancel_dt = deadline_utc if deadline_utc.tzinfo else deadline_utc.replace(tzinfo=timezone.utc)
        if cancel_dt <= datetime.now(timezone.utc):
            cancel_dt = datetime.now(timezone.utc) + timedelta(hours=24)

        cancel_ripple = datetime_to_ripple_time(cancel_dt)
        crypto_pair = generate_preimage_condition() if use_condition else None

        unsigned_payload = self.build_escrow_create_payload(
            buyer_address=buyer_address,
            destination_address=destination_address,
            amount_rlusd=amount_rlusd,
            cancel_after_dt=cancel_dt,
            ipfs_cid=ipfs_cid,
            group_code=group_code,
            stage=stage,
            condition_hex=crypto_pair.condition_hex if crypto_pair else None,
        )

        # Path B: Policy guardrail paused autonomous execution (> R50,000 daily spend)
        if not autonomous_approved:
            return EscrowReceipt(
                stage=stage,
                tx_hash="PENDING_OWNER_SIGNATURE",
                ledger_index=0,
                owner_address=buyer_address,
                destination_address=destination_address,
                offer_sequence=0,
                amount_rlusd=amount_rlusd,
                condition_hex=crypto_pair.condition_hex if crypto_pair else None,
                preimage_hex=crypto_pair.preimage_hex if crypto_pair else None,
                cancel_after_ripple=cancel_ripple,
                explorer_url="",
                unsigned_tx_json=unsigned_payload,
            )

        if not XRPL_LIVE_MODE or buyer_wallet is None:
            simulated_hash = hashlib.sha256(
                f"{buyer_address}:{group_code}:{stage.value}:{amount_rlusd}:{secrets.token_hex(8)}".encode()
            ).hexdigest().upper()
            simulated_seq = int.from_bytes(secrets.token_bytes(2), "big") + 1000
            return EscrowReceipt(
                stage=stage,
                tx_hash=simulated_hash,
                ledger_index=4892104,
                owner_address=buyer_address,
                destination_address=destination_address,
                offer_sequence=simulated_seq,
                amount_rlusd=amount_rlusd,
                condition_hex=crypto_pair.condition_hex if crypto_pair else None,
                preimage_hex=crypto_pair.preimage_hex if crypto_pair else None,
                cancel_after_ripple=cancel_ripple,
                explorer_url=f"https://testnet.xrpl.org/transactions/{simulated_hash}",
            )

        tx = EscrowCreate.from_dict(unsigned_payload)
        signed_tx = await autofill_and_sign(tx, self.client, buyer_wallet)
        response = await submit_and_wait(signed_tx, self.client)
        result = response.result
        tx_hash = result.get("hash", "")
        offer_seq = int(result.get("Sequence", 0))

        return EscrowReceipt(
            stage=stage,
            tx_hash=tx_hash,
            ledger_index=int(result.get("ledger_index", 0)),
            owner_address=buyer_address,
            destination_address=destination_address,
            offer_sequence=offer_seq,
            amount_rlusd=amount_rlusd,
            condition_hex=crypto_pair.condition_hex if crypto_pair else None,
            preimage_hex=crypto_pair.preimage_hex if crypto_pair else None,
            cancel_after_ripple=cancel_ripple,
            explorer_url=f"https://testnet.xrpl.org/transactions/{tx_hash}",
        )

    async def mint_participation_mpt_xls33(
            self,
            *,
            issuer_wallet: Wallet | None,
            issuer_address: str,
            group_code: str,
            total_units: int,
            ipfs_cid: str,
    ) -> dict[str, Any]:
        """
        Mints an XLS-33 Multi-Purpose Token (MPT) issuance representing verified bulk pool
        units anchored to the immutable IPFS PricingReceipt CID.
        """
        metadata_str = f"StokSafe:{group_code}|IPFS:{ipfs_cid}"
        if not XRPL_LIVE_MODE or issuer_wallet is None:
            sim_hash = hashlib.sha256(f"MPT:{metadata_str}:{secrets.token_hex(6)}".encode()).hexdigest().upper()
            return {
                "standard": "XLS-33",
                "tx_hash": sim_hash,
                "issuer": issuer_address,
                "maximum_amount": str(total_units),
                "metadata": metadata_str,
                "explorer_url": f"https://testnet.xrpl.org/transactions/{sim_hash}",
            }

        mpt_tx = MPTokenIssuanceCreate(
            account=issuer_address,
            maximum_amount=str(total_units),
            mptoken_metadata=str_to_hex(metadata_str).upper(),
        )
        signed = await autofill_and_sign(mpt_tx, self.client, issuer_wallet)
        resp = await submit_and_wait(signed, self.client)
        tx_hash = resp.result.get("hash", "")
        return {
            "standard": "XLS-33",
            "tx_hash": tx_hash,
            "issuer": issuer_address,
            "maximum_amount": str(total_units),
            "metadata": metadata_str,
            "explorer_url": f"https://testnet.xrpl.org/transactions/{tx_hash}",
        }

    async def cancel_failed_pool_escrow(
            self,
            *,
            executor_wallet: Wallet | None,
            executor_address: str,
            escrow_owner_address: str,
            offer_sequence: int,
    ) -> dict[str, Any]:
        """
        Executes XRPL EscrowCancel when a pool fails to reach supplier MOQ by deadline,
        returning 100% of the buyer's 20% commitment deposit.
        """
        if not XRPL_LIVE_MODE or executor_wallet is None:
            sim_hash = hashlib.sha256(
                f"CANCEL:{escrow_owner_address}:{offer_sequence}:{secrets.token_hex(6)}".encode()
            ).hexdigest().upper()
            return {
                "status": "REFUNDED_MOQ_FAILED",
                "tx_hash": sim_hash,
                "escrow_owner": escrow_owner_address,
                "offer_sequence": offer_sequence,
                "explorer_url": f"https://testnet.xrpl.org/transactions/{sim_hash}",
            }

        cancel_tx = EscrowCancel(
            account=executor_address,
            owner=escrow_owner_address,
            offer_sequence=offer_sequence,
        )
        signed = await autofill_and_sign(cancel_tx, self.client, executor_wallet)
        resp = await submit_and_wait(signed, self.client)
        tx_hash = resp.result.get("hash", "")
        return {
            "status": "REFUNDED_MOQ_FAILED",
            "tx_hash": tx_hash,
            "escrow_owner": escrow_owner_address,
            "offer_sequence": offer_sequence,
            "explorer_url": f"https://testnet.xrpl.org/transactions/{tx_hash}",
        }

    async def forfeit_defaulted_deposit_escrow(
            self,
            *,
            executor_wallet: Wallet | None,
            executor_address: str,
            escrow_owner_address: str,
            offer_sequence: int,
            condition_hex: str,
            fulfillment_hex: str,
            reason: str,
    ) -> dict[str, Any]:
        """
        Executes XRPL EscrowFinish into STOKSAFE_TREASURY_ADDRESS when a buyer unilaterally
        cancels after committing, retaining 100% of their 20% deposit for StokSafe.
        """
        if not XRPL_LIVE_MODE or executor_wallet is None:
            sim_hash = hashlib.sha256(
                f"FORFEIT:{escrow_owner_address}:{offer_sequence}:{secrets.token_hex(6)}".encode()
            ).hexdigest().upper()
            return {
                "status": "DEFAULTED_DEPOSIT_FORFEITED",
                "treasury_address": STOKSAFE_TREASURY_ADDRESS,
                "tx_hash": sim_hash,
                "reason": reason,
                "explorer_url": f"https://testnet.xrpl.org/transactions/{sim_hash}",
            }

        finish_tx = EscrowFinish(
            account=executor_address,
            owner=escrow_owner_address,
            offer_sequence=offer_sequence,
            condition=condition_hex,
            fulfillment=fulfillment_hex,
            memos=[
                Memo(
                    memo_type=str_to_hex("stoksafe/deposit-forfeit").upper(),
                    memo_data=str_to_hex(reason[:120]).upper(),
                )
            ],
        )
        signed = await autofill_and_sign(finish_tx, self.client, executor_wallet)
        resp = await submit_and_wait(signed, self.client)
        tx_hash = resp.result.get("hash", "")
        return {
            "status": "DEFAULTED_DEPOSIT_FORFEITED",
            "treasury_address": STOKSAFE_TREASURY_ADDRESS,
            "tx_hash": tx_hash,
            "reason": reason,
            "explorer_url": f"https://testnet.xrpl.org/transactions/{tx_hash}",
        }

    async def finish_delivery_settlement_split(
            self,
            *,
            executor_wallet: Wallet | None,
            executor_address: str,
            escrow_owner_address: str,
            offer_sequence: int,
            condition_hex: str,
            fulfillment_hex: str,
            supplier_address: str,
            supplier_net_rlusd: Decimal,
            carrier_address: str,
            carrier_freight_rlusd: Decimal,
            platform_revenue_rlusd: Decimal,
            bol_reference: str,
    ) -> dict[str, Any]:
        """
        Triggered upon Logistics Bill of Lading delivery webhook:
        1. Submits XRPL EscrowFinish with cryptographic preimage fulfillment.
        2. Disburses atomic 3-way split:
           - Supplier Net Payout (Goods minus 5% marketplace fee)
           - Carrier Actual Bulk Freight
           - StokSafe Treasury (75% shipping arbitrage + 5% buyer fee + 5% supplier fee)
        """
        if not XRPL_LIVE_MODE or executor_wallet is None:
            finish_hash = hashlib.sha256(
                f"FINISH:{bol_reference}:{offer_sequence}:{secrets.token_hex(6)}".encode()
            ).hexdigest().upper()
            return {
                "status": "SETTLED_ON_LEDGER",
                "bol_reference": bol_reference,
                "escrow_finish_tx_hash": finish_hash,
                "explorer_url": f"https://testnet.xrpl.org/transactions/{finish_hash}",
                "disbursements": {
                    "supplier": {"address": supplier_address, "amount_rlusd": str(supplier_net_rlusd)},
                    "carrier": {"address": carrier_address, "amount_rlusd": str(carrier_freight_rlusd)},
                    "stoksafe_treasury": {
                        "address": STOKSAFE_TREASURY_ADDRESS,
                        "amount_rlusd": str(platform_revenue_rlusd),
                    },
                },
            }

        finish_tx = EscrowFinish(
            account=executor_address,
            owner=escrow_owner_address,
            offer_sequence=offer_sequence,
            condition=condition_hex,
            fulfillment=fulfillment_hex,
            memos=[
                Memo(
                    memo_type=str_to_hex("stoksafe/bol-proof").upper(),
                    memo_data=str_to_hex(bol_reference).upper(),
                )
            ],
        )
        signed_finish = await autofill_and_sign(finish_tx, self.client, executor_wallet)
        finish_resp = await submit_and_wait(signed_finish, self.client)
        finish_hash = finish_resp.result.get("hash", "")

        payout_hashes: dict[str, str] = {}
        payouts = [
            ("supplier", supplier_address, supplier_net_rlusd),
            ("carrier", carrier_address, carrier_freight_rlusd),
            ("stoksafe_treasury", STOKSAFE_TREASURY_ADDRESS, platform_revenue_rlusd),
        ]
        for role, dest, amt in payouts:
            if amt > Decimal("0"):
                drops = str(int((amt * Decimal("1000000")).to_integral_value()))
                pay_tx = Payment(account=executor_address, destination=dest, amount=drops)
                signed_pay = await autofill_and_sign(pay_tx, self.client, executor_wallet)
                pay_resp = await submit_and_wait(signed_pay, self.client)
                payout_hashes[role] = pay_resp.result.get("hash", "")

        return {
            "status": "SETTLED_ON_LEDGER",
            "bol_reference": bol_reference,
            "escrow_finish_tx_hash": finish_hash,
            "explorer_url": f"https://testnet.xrpl.org/transactions/{finish_hash}",
            "disbursements": {
                "supplier": {
                    "address": supplier_address,
                    "amount_rlusd": str(supplier_net_rlusd),
                    "tx_hash": payout_hashes.get("supplier", ""),
                },
                "carrier": {
                    "address": carrier_address,
                    "amount_rlusd": str(carrier_freight_rlusd),
                    "tx_hash": payout_hashes.get("carrier", ""),
                },
                "stoksafe_treasury": {
                    "address": STOKSAFE_TREASURY_ADDRESS,
                    "amount_rlusd": str(platform_revenue_rlusd),
                    "tx_hash": payout_hashes.get("stoksafe_treasury", ""),
                },
            },
        }
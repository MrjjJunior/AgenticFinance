import base64
import hashlib
import json
import os
from dataclasses import dataclass
from typing import Any
import httpx

PINATA_JWT = os.getenv("PINATA_JWT", "")
PINATA_PIN_JSON_URL = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
IPFS_GATEWAY_BASE = os.getenv("IPFS_GATEWAY_BASE", "https://gateway.pinata.cloud/ipfs")

@dataclass(frozen=True)
class IPFSPinResult:
    cid: str
    sha256_hex: str
    gateway_url: str
    pinned_remotely: bool
    canonical_payload: dict[str, Any]

def compute_deterministic_cidv1(canonical_bytes: bytes) -> tuple[str, str]:
    digest = hashlib.sha256(canonical_bytes).digest()
    sha256_hex = digest.hex()
    cid_bytes = bytes([0x01, 0x55, 0x12, 0x20]) + digest
    b32_encoded = base64.b32encode(cid_bytes).decode("ascii").lower().rstrip("=")
    return f"b{b32_encoded}", sha256_hex

class IPFSReceiptService:
    def __init__(self, pinata_jwt: str = PINATA_JWT) -> None:
        self.pinata_jwt = pinata_jwt.strip()

    async def pin_pricing_receipt(
        self,
        *,
        receipt_dict: dict[str, Any],
        group_code: str,
        buyer_wallet: str,
    ) -> IPFSPinResult:
        canonical_json = json.dumps(receipt_dict, sort_keys=True, separators=(",", ":"))
        canonical_bytes = canonical_json.encode("utf-8")
        local_cid, sha256_hex = compute_deterministic_cidv1(canonical_bytes)

        if not self.pinata_jwt:
            return IPFSPinResult(
                cid=local_cid,
                sha256_hex=sha256_hex,
                gateway_url=f"{IPFS_GATEWAY_BASE}/{local_cid}",
                pinned_remotely=False,
                canonical_payload=receipt_dict,
            )

        headers = {
            "Authorization": f"Bearer {self.pinata_jwt}",
            "Content-Type": "application/json",
        }
        body = {
            "pinataMetadata": {
                "name": f"stoksafe-receipt-{group_code}-{buyer_wallet[:10]}",
                "keyvalues": {"group_code": group_code, "buyer_wallet": buyer_wallet},
            },
            "pinataContent": receipt_dict,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(PINATA_PIN_JSON_URL, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
            remote_cid = data.get("IpfsHash", local_cid)

        return IPFSPinResult(
            cid=remote_cid,
            sha256_hex=sha256_hex,
            gateway_url=f"{IPFS_GATEWAY_BASE}/{remote_cid}",
            pinned_remotely=True,
            canonical_payload=receipt_dict,
        )


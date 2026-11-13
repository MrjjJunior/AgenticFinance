"""
Policy Co-Signer – HTTP CLIENT for the independent cosigner microservice.

This module contains NO signing keys and NO policy state. It is purely a
transport adapter: the agent sends the autofilled transaction to the
cosigner service (default http://localhost:8001/cosign), and the service —
which holds the cosigner's own seed and the Human Owner's limits — decides
independently whether to sign.

Why a separate service?
-----------------------
* Limits are enforced SOMEWHERE THE AGENT DOES NOT CONTROL. A compromised
  or buggy agent process cannot relax a cap that lives in another process
  with its own seed and its own config file.
* The Human Owner sets limits through the cosigner service's admin API —
  never through the agent.

Contract
--------
POST /cosign  body: {"tx_json": {...}, "amount_rlusd": "...", "destination_address": "..."}
→ 200 {"signed_tx_blob": "<hex>", "cosigner_address": "...", "recorded_spend_rlusd": "..."}
→ 403 {"detail": {"refused": true, "reason": "..."}}

The cosigner self-inspects `tx_json` (it does NOT trust the declared
amount/destination) — the declared fields are advisory only.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

import httpx
from xrpl.models.transactions import Transaction

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class PolicyCosignerError(Exception):
    """Raised when the Policy Co-Signer service refuses to sign (or is unreachable)."""


class PolicyCosigner:
    """
    Async HTTP client for the independent Policy Co-Signer microservice.

    Instantiate once per request (cheap; no persistent connection state).
    The cosigner's seed NEVER lives in this process — that is the whole
    point of the split.
    """

    def __init__(self) -> None:
        settings = get_settings()
        base = settings.policy_cosigner_base_url.rstrip("/")
        self._cosign_url = f"{base}/cosign"
        self._limits_url = f"{base}/limits"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def sign_transaction(
        self,
        autofilled_tx: Transaction,
        transaction_amount_rlusd: Decimal,
        destination_address: str,
    ) -> Transaction:
        """
        Ask the cosigner service to add its weight-1 signature.

        Parameters
        ----------
        autofilled_tx:
            The autofilled (but not yet signed) transaction object.
        transaction_amount_rlusd:
            Parsed transaction value — ADVICE ONLY. The service extracts
            the authoritative amount from the tx itself.
        destination_address:
            The supplier XRPL address — ADVICE ONLY. The service extracts
            the destination from the tx itself.

        Returns
        -------
        Transaction
            Cosigner-signed tx (signature in the `Signers` array), rebuilt
            from the hex blob the service returned.

        Raises
        ------
        PolicyCosignerError
            If the cosigner's independent checks fail (HTTP 403) or the
            service is unreachable / returns garbage.
        """
        payload: dict[str, Any] = {
            # Round-trip verified: signing the rebuilt tx produces the exact
            # same signature as signing the original object.
            "tx_json": autofilled_tx.to_xrpl(),
            "amount_rlusd": str(transaction_amount_rlusd),
            "destination_address": destination_address,
        }

        logger.info(
            "PolicyCosigner: requesting signature from %s | amount=%s RLUSD | destination=%s",
            self._cosign_url,
            transaction_amount_rlusd,
            destination_address,
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self._cosign_url, json=payload)
        except httpx.HTTPError as exc:
            raise PolicyCosignerError(
                f"Could not reach Policy Co-Signer service at {self._cosign_url}: {exc}"
            ) from exc

        if response.status_code == 403:
            reason = self._extract_reason(response)
            logger.warning("PolicyCosigner REFUSED to sign | reason=%s", reason)
            raise PolicyCosignerError(
                f"Policy Co-Signer refused to sign transaction: {reason}"
            )

        if response.status_code != 200:
            raise PolicyCosignerError(
                f"Policy Co-Signer service error (HTTP {response.status_code}): "
                f"{response.text[:300]}"
            )

        data = response.json()
        blob = data.get("signed_tx_blob")
        if not blob:
            raise PolicyCosignerError(
                "Policy Co-Signer returned a response without signed_tx_blob"
            )

        try:
            cosigner_signed_tx = Transaction.from_blob(blob)
        except Exception as exc:  # noqa: BLE001
            raise PolicyCosignerError(
                f"Could not parse signed transaction blob from cosigner: {exc}"
            ) from exc

        logger.info(
            "PolicyCosigner: signature applied | cosigner_address=%s",
            data.get("cosigner_address", "unknown"),
        )
        return cosigner_signed_tx

    async def get_limits(self) -> dict[str, Any]:
        """
        Fetch the Human Owner's live limits and today's spend from the
        cosigner service. Used by the agent's mandate check so that a cap
        the owner just changed takes effect IMMEDIATELY, without restarting
        the agent.

        Falls back to local settings if the service is unreachable.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(self._limits_url)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning(
                "Could not read limits from cosigner service (%s) — "
                "falling back to local config | error=%s",
                self._limits_url,
                exc,
            )
            return {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_reason(response: httpx.Response) -> str:
        """Pull a human-readable refusal reason out of the 403 response."""
        try:
            detail = response.json().get("detail", {})
            if isinstance(detail, dict):
                return str(detail.get("reason", detail))
            return str(detail)
        except Exception:  # noqa: BLE001
            return response.text[:300]

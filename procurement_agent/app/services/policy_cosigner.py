"""
PolicyCosigner – mocked second-signature service (weight = 1).

In production this would be a hardened microservice with its own HSM or
secrets manager, callable over mTLS. Here it is a self-contained class
that:

  1. Re-validates the transaction against the agreed policy limits before
     signing (defence-in-depth – the cosigner is an independent check,
     NOT just a rubber stamp).
  2. Signs the already-autofilled transaction using its own seed with
     multisign=True (placing the signature in the XRPL `Signers` array).
  3. NEVER signs if the transaction amount exceeds the policy cap or if
     the destination is not on the approved list.

Security notes
--------------
* The cosigner uses its OWN wallet seed (policy_cosigner_seed), not the
  main account's seed or the agent's seed.
* multisign=True is mandatory: without it xrpl-py would put the signature
  in TxnSignature, making it a single-signed tx that would be rejected by
  the ledger because the master key is disabled.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional

from xrpl.models.transactions import Transaction
from xrpl.transaction import sign
from xrpl.wallet import Wallet

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class PolicyCosignerError(Exception):
    """Raised when the Policy Co-Signer refuses to sign."""


class PolicyCosigner:
    """
    Mocked Policy Co-Signer service.

    Instantiate once at application startup and reuse across requests.
    In production, replace the body of `sign_transaction` with an HTTP
    call to the external cosigner microservice.
    """

    def __init__(self) -> None:
        settings = get_settings()

        # SECURITY: Load the cosigner's OWN wallet – not the main account.
        self._wallet: Wallet = Wallet.from_seed(settings.policy_cosigner_seed)
        self._daily_cap: Decimal = settings.daily_spending_cap_rlusd
        self._approved_suppliers: list[str] = settings.approved_supplier_list
        self._rlusd_issuer: str = settings.rlusd_issuer

        logger.info(
            "PolicyCosigner initialised | address=%s",
            self._wallet.classic_address,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def sign_transaction(
        self,
        autofilled_tx: Transaction,
        transaction_amount_rlusd: Decimal,
        destination_address: str,
    ) -> Transaction:
        """
        Validate policy constraints independently and return the cosigner's
        signed version of the transaction (multisign=True).

        Parameters
        ----------
        autofilled_tx:
            The autofilled (but not yet signed) transaction object.
        transaction_amount_rlusd:
            Parsed transaction value used for the independent cap check.
        destination_address:
            The supplier XRPL address – independently verified against the
            cosigner's own allowlist (not the agent's cached copy).

        Returns
        -------
        Transaction
            Cosigner-signed tx with signature placed in the `Signers` array.

        Raises
        ------
        PolicyCosignerError
            If the cosigner's independent checks fail. This is the
            last line of defence against a compromised agent.
        """
        self._independent_policy_check(transaction_amount_rlusd, destination_address)

        logger.info(
            "PolicyCosigner: signing transaction | destination=%s | amount=%s RLUSD",
            destination_address,
            transaction_amount_rlusd,
        )

        # multisign=True is MANDATORY – places sig in Signers[], not TxnSignature
        cosigner_signed_tx = sign(
            autofilled_tx,
            self._wallet,
            multisign=True,  # ← critical security invariant
        )

        logger.info(
            "PolicyCosigner: signature applied | cosigner_address=%s",
            self._wallet.classic_address,
        )
        return cosigner_signed_tx

    @property
    def address(self) -> str:
        return self._wallet.classic_address

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _independent_policy_check(
        self,
        amount: Decimal,
        destination: str,
    ) -> None:
        """
        The cosigner runs its OWN policy checks, independent of the agent.
        This prevents an agent bug or compromise from bypassing limits.
        """
        errors: list[str] = []

        if amount > self._daily_cap:
            errors.append(
                f"Amount {amount} RLUSD exceeds policy cap {self._daily_cap} RLUSD"
            )

        if destination not in self._approved_suppliers:
            errors.append(
                f"Destination {destination} is NOT on the cosigner's approved list"
            )

        if errors:
            reason = "; ".join(errors)
            logger.warning(
                "PolicyCosigner REFUSED to sign | reasons=%s", reason
            )
            raise PolicyCosignerError(
                f"Policy Co-Signer refused to sign transaction: {reason}"
            )

"""
Application configuration loaded from environment variables.

Copy .env.example to .env and populate before running.
Never commit real seeds or API keys to version control.
"""

from __future__ import annotations

from decimal import Decimal
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # XRPL Network
    # ------------------------------------------------------------------
    xrpl_node_url: str = "https://s.altnet.rippletest.net:51234/"

    # The Stokvel pool account whose master key is DISABLED.
    # All transactions originate from this address.
    main_account_address: str = "rMAIN_ACCOUNT_ADDRESS_PLACEHOLDER"

    # ------------------------------------------------------------------
    # RLUSD Token Config (Testnet)
    # ------------------------------------------------------------------
    # Hex-encoded currency code for RLUSD
    rlusd_currency_hex: str = "524C555344000000000000000000000000000000"
    # Testnet RLUSD issuer (Gateway)
    rlusd_issuer: str = "rQhWct2fv4Vc4KRjRgMrxa8xPN9Zx9iLKV"

    # ------------------------------------------------------------------
    # AI Agent Identity  (delegated signer – weight 1)
    # SECURITY: This seed MUST be the Agent's OWN wallet seed.
    #           It is NEVER the main account's seed.
    # ------------------------------------------------------------------
    agent_seed: str = "sAGENT_SEED_PLACEHOLDER"

    # ------------------------------------------------------------------
    # Policy Co-Signer – INDEPENDENT microservice (weight 1)
    # The agent talks to it over HTTP and NEVER holds its seed.
    # The cosigner service keeps its own limits (human-controlled) and
    # enforces them independently of anything the agent says.
    # ------------------------------------------------------------------
    policy_cosigner_seed: str = "sCOSIGNER_SEED_PLACEHOLDER"
    policy_cosigner_base_url: str = "http://localhost:8001"

    # ------------------------------------------------------------------
    # LLM Configuration
    # ------------------------------------------------------------------
    groq_api_key: str = "gsk-PLACEHOLDER"
    llm_model: str = "llama-3.3-70b-versatile"
    # Defaults to Groq; override to point at an OpenAI-compatible stub.
    groq_base_url: str = "https://api.groq.com/openai/v1"

    # ------------------------------------------------------------------
    # Mandate / Business Rules
    # ------------------------------------------------------------------
    # Daily spending cap per member in RLUSD
    daily_spending_cap_rlusd: Decimal = Decimal("5000.00")

    # ------------------------------------------------------------------
    # KYB / Allowlist (XLS-70)
    # ------------------------------------------------------------------
    # Comma-separated XRPL addresses of KYB-approved suppliers
    approved_supplier_addresses: str = (
        "rSupplierAlpha000000000000000000,"
        "rSupplierBeta0000000000000000000"
    )
    # The DID / Credential type to look for on-ledger
    kyb_credential_type: str = "KYBVerified"

    @property
    def approved_supplier_list(self) -> list[str]:
        return [
            addr.strip()
            for addr in self.approved_supplier_addresses.split(",")
            if addr.strip()
        ]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

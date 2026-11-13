"""
LimitsStore – file-backed state for the Policy Co-Signer microservice.

Holds EXACTLY TWO things the Human Owner controls:
  * the daily RLUSD spending cap
  * the approved supplier allowlist

plus the running total of signed spend per calendar day.

Design notes
------------
* Lives in its own process with its own wallet seed — the agent cannot
  read or change it except through the cosigner's HTTP API.
* Seeded ONCE from procurement_agent/.env on first run. After that the
  values only change through the admin API (POST /admin/limits) — i.e.
  the Human Owner is in sole control.
* Persisted to JSON so caps and today's spend survive service restarts.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import date
from decimal import Decimal
from pathlib import Path


def _today() -> str:
    return date.today().isoformat()


class LimitsStore:
    """Thread-safe JSON store for cap / allowlist / daily signed spend.

    Uses an RLock because mutating methods (set_limits, reset_spend) call
    snapshot() while holding the lock.
    """

    def __init__(self, path: Path, seed_daily_cap: str, seed_suppliers: list[str]):
        self._path = path
        self._lock = threading.RLock()
        self._data = self._load_or_seed(seed_daily_cap, seed_suppliers)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load_or_seed(self, seed_daily_cap: str, seed_suppliers: list[str]) -> dict:
        if self._path.exists():
            with open(self._path, encoding="utf-8") as fh:
                data = json.load(fh)
            # Backfill in case of an older file shape
            data.setdefault("daily_cap_rlusd", seed_daily_cap)
            data.setdefault("approved_suppliers", seed_suppliers)
            data.setdefault("spend", {})
            return data

        data = {
            "daily_cap_rlusd": seed_daily_cap,
            "approved_suppliers": seed_suppliers,
            "spend": {},
        }
        self._write(data)
        return data

    def _write(self, data: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        os.replace(tmp, self._path)

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def snapshot(self) -> dict:
        """Everything the /limits endpoint (and the Owner Console) shows."""
        with self._lock:
            return {
                "daily_cap_rlusd": str(self._data["daily_cap_rlusd"]),
                "approved_suppliers": list(self._data["approved_suppliers"]),
                "spent_today_rlusd": str(self.spent_today_locked()),
                "date": _today(),
            }

    def spent_today_locked(self) -> Decimal:
        return Decimal(str(self._data["spend"].get(_today(), "0")))

    # ------------------------------------------------------------------
    # Mutators (admin API + cosign bookkeeping)
    # ------------------------------------------------------------------

    def set_limits(
        self,
        daily_cap: Decimal | None = None,
        suppliers: list[str] | None = None,
    ) -> dict:
        with self._lock:
            if daily_cap is not None:
                self._data["daily_cap_rlusd"] = str(daily_cap)
            if suppliers is not None:
                self._data["approved_suppliers"] = suppliers
            self._write(self._data)
            return self.snapshot()

    def record_spend(self, amount: Decimal) -> Decimal:
        """Add to today's signed-spend total; returns the new total."""
        with self._lock:
            key = _today()
            current = Decimal(str(self._data["spend"].get(key, "0")))
            new_total = current + amount
            self._data["spend"][key] = str(new_total)
            self._write(self._data)
            return new_total

    def reset_spend(self) -> dict:
        """Zero today's spend (demo convenience — Human Owner action)."""
        with self._lock:
            self._data["spend"][_today()] = "0"
            self._write(self._data)
            return self.snapshot()

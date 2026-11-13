# Procurement Agent — Web Console (Minimal Frontend)

A tiny, zero-dependency frontend for the **Stokvel AI Procurement Agent**.
It is a single `index.html` file — no build step, no npm, no framework.
Open it in a browser and start submitting invoices.

> The full step-by-step guide lives in the [root README](../README.md).
> Fastest way to run everything (cosigner + backend + this UI):
> `.\start_all.ps1` from the repo root.

**What it does:** sends an order intent + scanned invoice to the agent
backend's `POST /api/v1/process-invoice` and displays the outcome of the
4-step workflow:

| Outcome | Meaning |
|---|---|
| **APPROVED** | Verified → payment auto-executed on XRPL Testnet by Agent(1) + Policy Co-Signer(1) (Path A) |
| **ESCALATED** | Outside the mandate (e.g. over daily cap) → a half-signed transaction is returned for the Human Owner (Path B) |
| **REJECTED** | AI or ledger verification failed → nothing is sent to XRPL |

## The UI at a glance

1. **Header** — agent backend URL + Policy Co-Signer URL, each with a
   health dot (click **Check** to refresh).
2. **Owner console** — the Human Owner's control plane, talking directly to
   the cosigner service (`/limits`, `/admin/limits`, `/admin/spend/reset`):
   - daily RLUSD cap
   - approved supplier addresses (one per line)
   - **Save limits** — takes effect on the agent's *next* invoice, no restart
   - **Reset today's spend** — demo convenience
   - optional admin token (only needed if `COSIGNER_ADMIN_TOKEN` is set)
3. **Invoice form** — order intent, scanned-invoice fields, supplier details.
   **Load demo data** pre-fills a realistic invoice (~1,480 RLUSD).
   Tick **"Simulate a different invoice"** to override the invoice's
   address/items/total and test mismatches + escalation.
4. **Result card** — one panel per step; on escalation it shows the
   half-signed blob the Human Owner can countersign (weight 2).

## Quick start (manual)

```powershell
# 1. Cosigner service (independent limits) — from the REPO ROOT
python -m uvicorn cosigner_service.main:create_app --factory --port 8001

# 2. Agent backend
cd procurement_agent
.\venv\Scripts\python -m uvicorn app.main:app --port 8000

# 3. Open index.html (double-click, or serve it:)
#    cd frontend && python -m http.server 5500
```

One-time provisioning before first use (wallets, RLUSD, KYB credential):
see the [root README](../README.md#quick-start-5-commands).

## Handling an ESCALATED invoice (Path B)

1. Click **Copy** next to the half-signed blob.
2. Countersign with the **Human Owner** wallet (weight 2) and submit —
   e.g. with xrpl-py: `sign(blob_tx, human_wallet, multisign=True)`, combine,
   `submit_and_wait()`. The seed is `HUMAN_OWNER_SEED` in
   `procurement_agent/.env`. One weight-2 signature meets the quorum of 2.
3. Verify on the [XRPL Testnet Explorer](https://testnet.xrpl.org/).

## Trying the different outcomes

- **APPROVED** — demo data works out of the box after `setup_demo.py`
  (the demo supplier has an on-ledger `KYBVerified` credential).
- **ESCALATED** — process the same invoice twice (cap exhausted), or tick
  "Simulate a different invoice" and set a total above the cap. Or change
  the cap in the Owner console to something small — that's the
  "human sets limits outside the agent" demo.
- **REJECTED** — change the invoice supplier address so it differs from the
  order (Step 1), or use an address with no KYB credential (Step 2).
- **ERROR** — stop the backend and submit → shows connection troubleshooting.

> **APPROVED submits a real transaction** to XRPL *Testnet* and calls the
> real Groq API for Step 1. Use test wallets only.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Backend dot red | Backend not running / wrong URL. Test `http://localhost:8000/api/v1/health` manually. |
| Cosigner dot red | Cosigner service not running — start it (see above), default `http://localhost:8001/health`. |
| `Failed to fetch` on submit | Same as backend dot. Confirm health URL in the browser first. |
| Save limits fails with 403 | The cosigner requires an admin token — set it in the token field (must match `COSIGNER_ADMIN_TOKEN`). |
| HTTP 500 mentioning LLM | The Groq key is missing/invalid — verification is fail-closed by design. |
| HTTP 422 on submit | A field failed backend validation — the error body lists which one. |
| Stale demo supplier address | Re-run `procurement_agent/setup_demo.py`; it re-patches the demo fields automatically. |

URLs and the admin token are stored in `localStorage` and persist between visits.

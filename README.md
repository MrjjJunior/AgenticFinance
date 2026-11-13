# Stokvel AI Procurement Agent

An XRPL multi-sig "procurement agent" for a community savings group (stokvel).
A scanned invoice arrives; an AI agent verifies it against the original order,
checks the supplier's on-ledger XLS-70 KYB credential, enforces the Human
Owner's spending mandate, and then either **executes the payment autonomously**
or **stops and hands the half-signed transaction to the human**.

```
                    ┌───────────────────────────────┐
   invoice JSON  →  │  Agent backend  (port 8000)   │  →  XRPL Testnet (RLUSD payment)
                    │  Step 1 LLM verification      │      multi-sig: Agent(1) + Cosigner(1)
                    │  Step 2 KYB/allowlist check   │      quorum 2, master key DISABLED
                    │  Step 3 mandate check         │
                    │  Step 4 execute / escalate    │
                    └───────────────┬───────────────┘
                                    │ HTTP  (agent holds NO cosigner key)
                    ┌───────────────▼───────────────┐
                    │  Policy Co-Signer (port 8001) │  ← Human Owner sets limits HERE
                    │  own seed, own limits file    │     (Owner Console in the frontend)
                    │  signs only if ITS rules pass │
                    └───────────────────────────────┘
```

The spending limits are enforced **somewhere the agent does not control**: a
separate process holding its own wallet seed and its own limits file. The
agent asks it to sign over HTTP and the cosigner re-derives the amount and
destination from the transaction itself — the agent cannot lie its way past
the cap.

---

## Quick start (5 commands)

```powershell
# 1. Install dependencies (once)
cd procurement_agent
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
cd ..

# 2. Create wallets + multisig signer list on XRPL Testnet (once)
.\procurement_agent\venv\Scripts\python procurement_agent\setup_wallets.py
#    → writes procurement_agent\.env (seeds). Add your OPENAI_API_KEY to that file.

# 3. Provision the demo world (once per fresh .env): supplier, RLUSD issuer,
#    trustlines, 25,000 RLUSD, XLS-70 KYB credential
.\procurement_agent\venv\Scripts\python procurement_agent\setup_demo.py

# 4. Start everything (cosigner :8001, backend :8000, opens the browser)
.\start_all.ps1

# 5. In the browser: click "Load demo data" → "Process invoice"
```

Requirements: Python 3.11+, internet access to XRPL Testnet, and an
**OpenAI API key** in `procurement_agent/.env` (`OPENAI_API_KEY=sk-...`).
The LLM verification step is fail-closed: without a working key the agent
refuses to process invoices rather than skipping the check.

---

## Using the app (step by step)

The frontend (`frontend/index.html`) has three zones:

1. **Owner console** (top) — YOUR limits: daily RLUSD cap, approved supplier
   list, "Reset today's spend". Saving writes them to the Policy Co-Signer
   service — never to the agent.
2. **Invoice form** (middle) — order intent, the scanned-invoice fields, and
   supplier details. "Load demo data" fills everything for you.
3. **Result card** (bottom) — one panel per workflow step, and on escalation
   the half-signed transaction blob for the Human Owner.

### The demo script (for judges)

| # | Do | Expect |
|---|----|--------|
| 1 | "Load demo data" → "Process invoice" | **APPROVED** — LLM verification, on-ledger KYB check, mandate OK, agent+cosigner sign, payment lands on Testnet. Explorer link shown. |
| 2 | Repeat immediately | **ESCALATED** — daily cap now exhausted (spend is tracked in the cosigner service, survives restarts). Agent signs once and stops; cosigner never contacted. |
| 3 | In the Owner console: set cap to **100**, Save | **Your limit, set outside the agent.** The next invoice is blocked by Step 3 (mandate) — or by the cosigner's own refusal if you bypass the agent. |
| 4 | "Reset today's spend", restore cap **5000**, process a fresh invoice | **APPROVED** again — proving the owner console really controls the limits. |
| 5 | (Optional, for judges) POST the payment tx directly to `http://localhost:8001/cosign` pretending the cap is fine | **403 refused** — the independent service blocks even a rogue agent. |

### Results explained

- **APPROVED (Path A)** — autonomous execution. Multi-sig transaction on
  Testnet: Agent weight 1 + Policy Co-Signer weight 1 = quorum 2. The main
  account's master key is disabled, so *no single party* can move funds.
- **ESCALATED (Path B)** — a rule was broken. The agent drafts + signs the
  payment (weight 1) and returns the half-signed blob. The Human Owner
  (weight 2) can countersign and submit it, or ignore it.
- **REJECTED** — verification failed (invoice mismatch, unknown supplier, no
  on-ledger KYB credential). Nothing is ever sent to the ledger.

---

## Running pieces manually (if you don't want start_all.ps1)

```powershell
# Terminal 1 — Policy Co-Signer (independent limits service)
cd <repo root>
procurement_agent\venv\Scripts\python -m uvicorn cosigner_service.main:create_app --factory --port 8001

# Terminal 2 — agent backend
cd procurement_agent
.\venv\Scripts\python -m uvicorn app.main:app --port 8000

# Browser: open frontend/index.html
```

Interactive API docs: http://localhost:8000/docs and http://localhost:8001/docs

Useful cosigner endpoints (what the Owner Console uses):

| Endpoint | Purpose |
|----------|---------|
| `GET /limits` | cap, approved suppliers, signed spend today |
| `POST /admin/limits` | Human Owner sets cap / allowlist (optional `X-Admin-Token` header) |
| `POST /admin/spend/reset` | zeroes today's signed spend (demo convenience) |
| `POST /cosign` | the agent's only cosigner call — signs or refuses |

---

## Configuration (`procurement_agent/.env`)

| Key | Meaning |
|-----|---------|
| `MAIN_ACCOUNT_ADDRESS` | Stokvel pool (multisig, master key disabled) |
| `AGENT_SEED` | Agent's own delegated signer (weight 1) |
| `POLICY_COSIGNER_SEED` | **Only** the cosigner service uses this |
| `HUMAN_OWNER_SEED` | The weight-2 countersigner (kept offline) |
| `RLUSD_ISSUER` | The Testnet RLUSD gateway this demo issued from |
| `APPROVED_SUPPLIER_ADDRESSES` | Seed value for the cosigner's allowlist (first run only — afterwards change via Owner Console) |
| `DAILY_SPENDING_CAP_RLUSD` | Seed value for the cosigner's cap (first run only) |
| `OPENAI_API_KEY` | Required — real LLM verification (fail-closed) |
| `LLM_MODEL` | Default `gpt-4o-mini` |
| `OPENAI_BASE_URL` | Optional — point at an OpenAI-compatible stub for testing |
| `COSIGNER_ADMIN_TOKEN` | Optional — protects the cosigner admin endpoints |

The cosigner's *live* limits live in `cosigner_service/cosigner_limits.json`
(seeded once from `.env`, then owned by the admin API). Delete that file to
re-seed from `.env`.

## Security model

- **On-ledger**: main account master key disabled; signer list quorum 2 =
  Agent(1) + Cosigner(1) + Human(2). No single party can move funds.
- **Outside the agent**: the cosigner service holds its own seed, enforces
  the Human Owner's cap + allowlist by reading the transaction itself
  (declared fields are ignored), refuses XRP or non-RLUSD payments, refuses
  transactions not from the pool account, and records signed spend
  persistently.
- **In the agent**: LLM verification fail-closed; ticket-based sequencing
  prevents duplicate payments; the cosigner is never contacted when the
  mandate is already broken.

## Troubleshooting

- **Port already in use** — `Get-NetTCPConnection -LocalPort 8000 -State Listen` →
  `Stop-Process -Id <OwningProcess>`; or just rerun `start_all.ps1` (it stops
  its own previous run).
- **LLM errors (HTTP 500, "LLM verification call failed")** — the key is
  missing/invalid; the workflow is fail-closed by design.
- **"Policy Co-Signer refused"** — read the reason: cap, allowlist, issuer,
  XRP-only rule, or wrong source account. That refusal is a *feature*.
- **`tecPATH_DRY` on Testnet after re-running setup** — trustline flags are
  baked in at creation; `setup_demo.py` handles this (issuer Default Ripple
  *before* trustlines + issuer-side NoRipple clear). Run it once more.
- **Frontend shows red dots** — the services aren't running or the URLs are
  wrong; both URL fields are editable in the header.

Details of what is verified and what is still a demo shortcut: see
[CHECKLIST.md](CHECKLIST.md).

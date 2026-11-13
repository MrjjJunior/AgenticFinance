# Stokvel AI Procurement Agent — Verified Feature Checklist

Last verified: 2026-11-13, all live on **XRPL Testnet** with the split
cosigner microservice and the real Groq LLM call.
Run `procurement_agent\venv\Scripts\pytest tests\ -q` → **27 passed**.

---

## Part 1 — The five workflow features

| # | Feature | Status | Evidence |
|---|---------|--------|----------|
| 1 | **AI Document Verification** | ✅ **REAL LLM** | `_call_llm_for_verification` makes a real Groq-compatible `chat.completions` call (`response_format=json_object`, temperature 0), parses + normalises the reply, and **fails closed** (raises `ProcurementAgentError`) on missing key / API error / unparseable JSON. Deterministic checks (address/total/item-count) still run first. Tests cover: LLM-reported discrepancy → REJECTED, placeholder key → abort, network error → abort, bad JSON → abort. |
| 2 | **Ledger Credential Checking** | ✅ Works | Real `AccountObjects(type=CREDENTIAL)` query vs Testnet; demo supplier holds an accepted XLS-70 `KYBVerified` credential. |
| 3 | **Mandate Enforcement** | ✅ **Now external** | Cap + spend read live from the cosigner service (`GET /limits`); the agent has no API to change them. A cap change via the Owner Console affected the very next invoice **without an agent restart** (live: cap 5000 → 100 → invoice blocked citing "cap of 100.00"). |
| 4 | **Autonomous Execution (Path A)** | ✅ Works | Live explorer tx `205A216B…F7D633` (HTTP-cosigner build): agent(1) + cosigner(1) via HTTP, ticket-based sequencing, no human. Earlier build: `514A0F01…B272`. |
| 5 | **Escalation (Path B)** | ✅ Works | Live: 6,000 over-cap → `ESCALATED, EXCEEDS_DAILY_CAP`, 685-char half-signed blob + `tx_dict` for the weight-2 Human Owner; **cosigner never contacted for the payment** (test-asserted invariant). |

## Part 2 — MVP criteria scorecard

| Criterion | Status | Evidence |
|-----------|--------|----------|
| **≥1 autonomous Testnet transaction** | ✅ **MET** | Explorer txs above, executed with zero human interaction. |
| **Limits enforced somewhere the agent doesn't control** | ✅ **MET** | (a) On-ledger: master key disabled, quorum 2 = agent(1)+cosigner(1)+human(2) — agent cannot move funds alone. (b) **Independent cosigner service** (`cosigner_service/`, port 8001): separate process, own seed, own JSON limits store; self-inspects the tx (ignores the agent's declared amount/destination — proven live: declared "1", actual 6000 → refused 403); refuses XRP / non-RLUSD / non-issuer / foreign-account txs; records signed spend persistently. |
| **Human sets limits outside the agent** | ✅ **MET** | Owner Console in the frontend + `POST /admin/limits` (+ optional `X-Admin-Token`). Limits live in `cosigner_limits.json`, seeded once from `.env`, then owned exclusively by the admin API. Live demo: cap change blocked the next invoice instantly. |
| **Blocked-path demo** | ✅ **MET** | Same run: APPROVED (1,480) → ESCALATED (6,000 over cap) → ESCALATED again under the owner's new cap of 100 → rogue direct-cosign refused 403. |

**All four MVP criteria met.**

## Remaining notes (honest gaps)

- **Groq quota**: if the configured key reaches its API limit (429), check the Groq account quota or set `GROQ_BASE_URL=http://127.0.0.1:18099/v1`
  in `.env` — `start_all.ps1` will then auto-start the included
  OpenAI-compatible stub (`procurement_agent/llm_stub.py`) and the full demo
  runs offline. The agent's code path is identical either way (real client,
  fail-closed).
- The payment is a ticket-based RLUSD `Payment` (not native `EscrowCreate` —
  XRPL escrow doesn't support IOU amounts; documented in code).
- The Human Owner's weight-2 countersignature of escalated blobs is manual
  (`HUMAN_OWNER_SEED` in `.env`).
- Agent's own in-memory spend tracker is now only a fallback when the
  cosigner service is unreachable; the cosigner's file-backed store is
  authoritative.

## Reproduce

```powershell
.\start_all.ps1        # cosigner :8001 + backend :8000 + browser
```

1. **Load demo data → Process invoice** → APPROVED (explorer link).
2. Repeat → ESCALATED (cap exhausted; spend survives restarts).
3. Owner console: cap 100 → Save → next invoice blocked by YOUR limit.
4. "Reset today's spend" → APPROVED again.

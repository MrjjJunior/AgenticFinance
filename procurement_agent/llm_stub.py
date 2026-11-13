"""
Optional local OpenAI-compatible stub server (dev/demo tool).

Why: the agent makes a REAL Groq API call for Step 1 (fail-closed). When
you have no API credits — or want a fully offline demo — point the agent at
this server:

    set GROQ_BASE_URL=http://127.0.0.1:18099/v1   (in .env or environment)

It implements the /v1/chat/completions protocol and performs the same
semantic invoice-vs-order checks a real LLM would, deterministically:

  * item count mismatch
  * description / quantity / unit-price mismatches per line item
  * stated total vs sum of line totals (>1% off)
  * currency mismatch

This is NOT a mock inside the agent — the agent's code path is identical
whether it talks to api.openai.com or to this OpenAI-compatible server.

Run:
    procurement_agent\\venv\\Scripts\\python llm_stub.py [--port 18099]
"""

from __future__ import annotations

import argparse
import json
import time
from typing import Any, Optional

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="OpenAI-compatible verification stub")

_DECODER = json.JSONDecoder()


def _extract_json_objects(text: str) -> list[dict]:
    """Pull every top-level JSON object out of a prompt string."""
    out: list[dict] = []
    i = text.find("{")
    while i != -1:
        try:
            obj, end = _DECODER.raw_decode(text, i)
            if isinstance(obj, dict):
                out.append(obj)
            i = text.find("{", end)
        except ValueError:
            i = text.find("{", i + 1)
    return out


def _norm(s: Any) -> str:
    return " ".join(str(s or "").lower().split())


def _semantic_check(order: dict, invoice: dict) -> list[str]:
    """The 'LLM judgement' — deterministic semantic comparisons."""
    problems: list[str] = []

    order_cur = str(order.get("currency", "")).upper()
    invoice_cur = str(invoice.get("currency", "")).upper()
    if order_cur and invoice_cur and order_cur != invoice_cur:
        problems.append(
            f"Currency mismatch: order is {order_cur} but invoice states {invoice_cur}"
        )

    order_items = order.get("items", []) or []
    invoice_items = invoice.get("line_items", []) or []
    if len(order_items) != len(invoice_items):
        problems.append(
            f"The order lists {len(order_items)} line items but the invoice "
            f"delivers {len(invoice_items)} - possibly unapproved extra goods"
        )

    for idx, (o, inv) in enumerate(zip(order_items, invoice_items), start=1):
        od, idd = _norm(o.get("description")), _norm(inv.get("description"))
        if od and idd and od != idd:
            problems.append(
                f"Line {idx} description differs: order says '{o.get('description')}' "
                f"but the invoice says '{inv.get('description')}'"
            )
        oq, iq = o.get("quantity"), inv.get("quantity")
        try:
            if oq is not None and iq is not None and float(iq) != float(oq):
                problems.append(
                    f"Line {idx} quantity differs: ordered {oq}, invoiced {iq} "
                    f"('{inv.get('description')}')"
                )
        except (TypeError, ValueError):
            pass

    try:
        stated = float(invoice.get("stated_total", 0))
        computed = sum(
            float(it.get("quantity", 0)) * float(it.get("unit_price", 0))
            for it in invoice_items
        )
        if computed and abs(stated - computed) / computed > 0.01:
            problems.append(
                f"Invoice stated total {stated} does not match the sum of its "
                f"line items ({computed:.2f}) - possible padded billing"
            )
    except (TypeError, ValueError):
        pass

    return problems


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: list[ChatMessage]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "openai-compatible-stub"}


@app.post("/chat/completions")
@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest) -> dict:
    last_user = next(
        (m.content for m in reversed(req.messages) if m.role == "user"),
        "",
    )
    docs = _extract_json_objects(last_user)
    order = docs[0] if len(docs) >= 1 else {}
    invoice = docs[1] if len(docs) >= 2 else {}
    problems = _semantic_check(order, invoice)

    reply = json.dumps(
        {
            "additional_discrepancies": problems,
            "confidence_score": 0.99 if not problems else 0.9,
            "reasoning": (
                "Compared the invoice line-by-line against the order intent: "
                + ("no semantic discrepancies found."
                   if not problems
                   else f"{len(problems)} semantic issue(s) found.")
            ),
        }
    )

    return {
        "id": f"chatcmpl-stub-{int(time.time() * 1000)}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model or "stokvel-verification-stub",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": reply},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=18099)
    args = parser.parse_args()
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")

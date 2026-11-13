"""
FastAPI router for the AI Procurement Agent.

Exposes:
  POST /api/v1/process-invoice

The endpoint receives an invoice processing request, delegates the full
four-step workflow to ProcurementAgent, and returns a structured response
indicating whether the invoice was:
  - APPROVED   (Path A – transaction submitted to XRPL Testnet)
  - ESCALATED  (Path B – partially-signed tx returned for Human Owner)
  - REJECTED   (AI or ledger verification failed)
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.models.schemas import (
    InvoiceOutcome,
    ProcessInvoiceRequest,
    ProcessInvoiceResponse,
)
from app.services.procurement_agent import ProcurementAgent, ProcurementAgentError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Procurement Agent"])


# ---------------------------------------------------------------------------
# Dependency – one agent instance per request
# (stateless; shared spend-ledger is module-level)
# ---------------------------------------------------------------------------

def _get_agent() -> ProcurementAgent:
    return ProcurementAgent()


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/process-invoice",
    response_model=ProcessInvoiceResponse,
    summary="Process an OCR-scanned invoice and execute the payment workflow",
    description=(
        "Runs the four-step AI Procurement workflow:\n\n"
        "1. **AI Verification** – LLM cross-checks invoice vs order intent\n"
        "2. **Ledger Verification** – Supplier allowlist + XLS-70 KYB credential\n"
        "3. **Mandate Check** – Daily spending cap + approved supplier list\n"
        "4. **Execution Route**\n"
        "   - **Path A (Autonomous):** EscrowCreate signed by Agent + CoSigner, submitted to Testnet\n"
        "   - **Path B (Escalation):** Partially-signed tx returned for Human Owner countersignature\n"
    ),
    responses={
        200: {"description": "Workflow completed (see `outcome` field for APPROVED/ESCALATED/REJECTED)"},
        422: {"description": "Invalid request payload"},
        500: {"description": "Internal agent or XRPL error"},
    },
)
async def process_invoice(
    payload: ProcessInvoiceRequest,
    request: Request,
) -> ProcessInvoiceResponse:
    """
    Main invoice processing endpoint.

    Returns HTTP 200 for all three outcomes (APPROVED / ESCALATED / REJECTED).
    HTTP 5xx is reserved for unexpected infrastructure failures.
    """
    client_host = request.client.host if request.client else "unknown"
    logger.info(
        "POST /api/v1/process-invoice | client=%s | order_id=%s | invoice=%s",
        client_host,
        payload.order_intent.order_id,
        payload.parsed_invoice.invoice_number,
    )

    try:
        agent = _get_agent()
        result: ProcessInvoiceResponse = await agent.process_invoice(
            order_intent=payload.order_intent,
            parsed_invoice=payload.parsed_invoice,
            supplier_details=payload.supplier_details,
        )
    except ProcurementAgentError as exc:
        logger.error(
            "ProcurementAgentError | order_id=%s | error=%s",
            payload.order_intent.order_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "AGENT_EXECUTION_FAILED",
                "message": str(exc),
                "order_id": payload.order_intent.order_id,
            },
        )
    except Exception as exc:
        logger.exception(
            "Unexpected error processing invoice | order_id=%s",
            payload.order_intent.order_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": f"An unexpected error occurred: {exc}",
                "order_id": payload.order_intent.order_id,
            },
        )

    # Log the outcome prominently for ops visibility
    _log_outcome(result, payload.order_intent.order_id)

    return result


# ---------------------------------------------------------------------------
# Health / readiness probes
# ---------------------------------------------------------------------------


@router.get(
    "/health",
    summary="Liveness probe",
    tags=["Health"],
    include_in_schema=False,
)
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "procurement-agent"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _log_outcome(result: ProcessInvoiceResponse, order_id: str) -> None:
    if result.outcome == InvoiceOutcome.APPROVED:
        tx = result.submitted_tx
        logger.info(
            "APPROVED (Path A) | order_id=%s | hash=%s | explorer=%s",
            order_id,
            tx.xrpl_tx_hash if tx else "N/A",
            tx.explorer_url if tx else "N/A",
        )
    elif result.outcome == InvoiceOutcome.ESCALATED:
        ar = result.approval_request
        logger.warning(
            "ESCALATED (Path B) | order_id=%s | reason=%s | detail=%s",
            order_id,
            ar.escalation_reason if ar else "N/A",
            ar.human_readable_reason if ar else "N/A",
        )
    else:
        logger.warning(
            "REJECTED | order_id=%s | reason=%s",
            order_id,
            result.rejection_reason,
        )

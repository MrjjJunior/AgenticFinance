"""
FastAPI application entry point for the AI Procurement Agent.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.agent_router import router as agent_router
from app.core.config import get_settings
from app.core.logging_config import setup_logging


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings = get_settings()

    import logging
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("AI Procurement Agent starting up")
    logger.info("XRPL Node   : %s", settings.xrpl_node_url)
    logger.info("Main Account: %s", settings.main_account_address)
    logger.info("Daily Cap   : %s RLUSD", settings.daily_spending_cap_rlusd)
    logger.info("=" * 60)

    yield

    logger.info("AI Procurement Agent shutting down.")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Stokvel AI Procurement Agent",
        description=(
            "XRPL multi-sig procurement backend for Stokvel pools. "
            "Implements a four-step AI-verified invoice workflow with "
            "autonomous execution (Path A) and human escalation (Path B)."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS – tighten origins for production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(agent_router)

    return app


app = create_app()

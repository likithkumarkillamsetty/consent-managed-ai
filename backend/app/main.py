from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import consents, consent_gate, audit, analytics, training


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_db()
    yield


app = FastAPI(
    title="Consent-Managed Data Pipelines for Enterprise AI (DEPA-Inspired)",
    description=(
        "Consent-Managed Data Pipelines for Enterprise AI.\n\n"
        "- **Module 1: Consent Management & Consent Gate**: DEPA-inspired consent lifecycle, purpose-binding, real-time gate evaluation, and audit logging.\n"
        "- **Module 2: Consent-Aware ML Training Pipeline & Lineage Tracking**: Gated dataset access, automatic record filtering, ML training, model persistence, and per-record training lineage."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(consents.router)
app.include_router(consent_gate.router)
app.include_router(audit.router)
app.include_router(analytics.router)
app.include_router(training.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "project": "Consent-Managed Data Pipelines for Enterprise AI (DEPA-Inspired)",
        "modules": [
            "Module 1: Consent Management & Consent Gate",
            "Module 2: Consent-Aware ML Training Pipeline & Data Lineage",
        ],
        "status": "healthy",
        "docs": "/docs",
        "note": "This module implements a DEPA/Account-Aggregator-inspired consent management model for the project. It is not an official Account Aggregator implementation.",
    }


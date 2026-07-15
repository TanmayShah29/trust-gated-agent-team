from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .chain.database import init_db
from .api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="TrustChain",
    description="Trust-Gated Multi-Agent Research Team with Cryptographic Audit Trail",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "TrustChain",
        "version": "1.0.0",
        "description": "Trust-Gated Multi-Agent Research Team",
        "endpoints": {
            "health": "GET /api/health",
            "run": "POST /api/run",
            "chain": "GET /api/chain/{run_id}",
            "verify": "GET /api/chain/{run_id}/verify",
            "tamper": "POST /api/chain/{run_id}/tamper",
            "trust_scores": "GET /api/chain/{run_id}/trust-scores",
            "audit_report": "GET /api/chain/{run_id}/audit-report",
        },
    }


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

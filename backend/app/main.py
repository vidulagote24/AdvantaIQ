"""AdvantaIQ — AI-Powered Financial Advisor Intelligence Platform.
Unified Backend Application: Merging Member 1 Intelligence Engine & Member 2 Advisor Workflow API.
"""

from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api import clients, insights, metrics
from app.api.v1.routes import router as v1_router
from app.data.repositories import client_repository

app = FastAPI(
    title="AdvantaIQ Advisor Intelligence Platform API",
    version="1.0.0",
    description=(
        "Unified Intelligence Platform answering 'Why this client, why now?' for wealth advisors. "
        "Provides deterministic financial analytics, explainable multi-signal priority scoring, "
        "evidence-backed insight cards, draft advisor meeting briefs, and interactive advisor workflow tracking."
    ),
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration for Member 2 React/Vite Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include Member 1 Intelligence Routers (/api/clients, /api/insights, /api/metrics)
app.include_router(clients.router, prefix=settings.API_V1_STR)
app.include_router(insights.router, prefix=settings.API_V1_STR)
app.include_router(metrics.router, prefix=settings.API_V1_STR)

# Include Member 2 Advisor Workflow Routers (/api/v1/...)
app.include_router(v1_router, prefix="/api/v1")

@app.get("/health", tags=["System"], summary="Health check and engine status")
def health_check():
    """Returns application health status, version, timestamp, and persistent database counts."""
    with client_repository._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM clients")
        client_count = cursor.fetchone()["cnt"]
        
    return {
        "status": "healthy",
        "service": "AdvantaIQ Advisor Intelligence Platform",
        "version": settings.VERSION,
        "environment": "hackathon-local",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": {
            "status": "connected",
            "type": "sqlite",
            "clients_loaded": client_count
        },
        "engine_mode": "deterministic_decision_support"
    }

@app.get("/", tags=["System"], summary="API Root and Documentation Pointer")
def root():
    return {
        "service": "AdvantaIQ Advisor Intelligence API",
        "status": "online",
        "version": settings.VERSION,
        "documentation": "/docs",
        "endpoints": {
            "v1_worklist": "/api/v1/advisors/worklist",
            "v1_clients": "/api/v1/clients",
            "v1_health": "/api/v1/health",
            "member1_clients": f"{settings.API_V1_STR}/clients",
            "member1_insights": f"{settings.API_V1_STR}/insights",
            "member1_metrics": f"{settings.API_V1_STR}/metrics/summary"
        }
    }

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Provides consistent JSON error response formatting for unhandled exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "path": request.url.path,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

"""FinTech Platform: Advisor Dynamic Summary.
Role: Data, Analytics & Intelligence Engine (Member 1).

Main application entry point configuring FastAPI, CORS, API routes, and health checks.
"""

from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.api import clients, insights, metrics
from app.data.repositories import client_repository

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Intelligence engine answering 'Why this client, why now?' for wealth advisors. "
        "Provides deterministic financial analytics, explainable priority scoring, "
        "evidence-backed insight generation, and empirical evaluation metrics."
    ),
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration for Member 2 Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(clients.router, prefix=settings.API_V1_STR)
app.include_router(insights.router, prefix=settings.API_V1_STR)
app.include_router(metrics.router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["System"], summary="Health check and engine status")
def health_check():
    """Returns application health status, version, timestamp, and persistent database counts."""
    with client_repository._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM clients")
        client_count = cursor.fetchone()["cnt"]
        
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
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
        "message": "Welcome to FinTech Platform: Advisor Dynamic Summary API",
        "version": settings.VERSION,
        "docs_url": "/docs",
        "health_url": "/health",
        "api_endpoints": {
            "clients": f"{settings.API_V1_STR}/clients",
            "insights": f"{settings.API_V1_STR}/insights",
            "metrics_summary": f"{settings.API_V1_STR}/metrics/summary"
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


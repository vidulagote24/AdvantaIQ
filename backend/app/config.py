import os
from pathlib import Path
from typing import List

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    PROJECT_NAME: str = "Advisor Dynamic Summary - Intelligence Engine"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1")
    
    DB_PATH: Path = BASE_DIR / "advisor_platform.db"
    
    CORS_ORIGINS: List[str] = [
        origin.strip() for origin in os.getenv(
            "CORS_ORIGINS", 
            "http://localhost:3000,http://localhost:5173,http://localhost:8080,http://127.0.0.1:3000,http://127.0.0.1:5173"
        ).split(",") if origin.strip()
    ]
    
    # Dataset Parameters
    DATASET_RANDOM_SEED: int = int(os.getenv("DATASET_RANDOM_SEED", "42"))
    DATASET_CLIENT_COUNT: int = int(os.getenv("DATASET_CLIENT_COUNT", "200"))
    
    # Financial Analytics & Alert Thresholds
    FRESHNESS_WARNING_DAYS: int = int(os.getenv("FRESHNESS_WARNING_DAYS", "45"))
    FRESHNESS_STALE_THRESHOLD_DAYS: int = int(os.getenv("FRESHNESS_STALE_THRESHOLD_DAYS", "90"))
    REVIEW_OVERDUE_THRESHOLD_DAYS: int = int(os.getenv("REVIEW_OVERDUE_THRESHOLD_DAYS", "180"))
    DRIFT_ALERT_THRESHOLD_PCT: float = float(os.getenv("DRIFT_ALERT_THRESHOLD_PCT", "5.0"))
    PERSISTENCE_MIN_PERIODS: int = int(os.getenv("PERSISTENCE_MIN_PERIODS", "2"))
    
    # Initial Heuristic Weights (as specified by prompt section 6)
    WEIGHT_GOAL_URGENCY: float = 0.25
    WEIGHT_DEVIATION_PERSISTENCE: float = 0.25
    WEIGHT_ALLOCATION_MISMATCH: float = 0.20
    WEIGHT_REVIEW_RECENCY: float = 0.15
    WEIGHT_EVIDENCE_QUALITY: float = 0.15

settings = Settings()

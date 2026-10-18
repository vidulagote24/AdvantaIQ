"""Metrics and Evaluation Summary API Endpoints.

Exposes actual evaluation results: Precision@10, Recall@10, False Positive Rate,
Calculation Accuracy, and Return-Only Baseline comparison.
"""

from fastapi import APIRouter
from app.schemas import EvaluationSummarySchema
from app.data.repositories import client_repository
from app.services.evaluation import evaluate_engines

router = APIRouter(prefix="/metrics", tags=["Metrics & Evaluation"])

@router.get("/summary", response_model=EvaluationSummarySchema, summary="Get prototype evaluation and baseline comparison")
def get_metrics_summary():
    """Returns empirical evaluation metrics derived from the generated synthetic dataset and planted test scenarios.
    
    Demonstrates mathematically why return-only ranking fails to identify critical goal shortfalls
    and produces high false-alarm rates.
    """
    return evaluate_engines(client_repository)

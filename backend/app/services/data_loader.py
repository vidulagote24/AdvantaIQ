import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone

from ..models.schemas import ClientProfile, AdvisorInsight, WorklistResponse
from .scoring import calculate_urgency_score, REFERENCE_DATE

def get_synthetic_data_path() -> Path:
    # Try relative to backend
    current_dir = Path(__file__).resolve().parent
    # current_dir is backend/app/services
    repo_root = current_dir.parents[2]
    candidate = repo_root / 'shared' / 'data' / 'synthetic' / 'clients.json'
    if candidate.exists():
        return candidate
    
    # Fallback to absolute E:\AdvantaIQ
    fallback = Path('E:/AdvantaIQ/shared/data/synthetic/clients.json')
    if fallback.exists():
        return fallback

    raise FileNotFoundError(f'Synthetic client data file not found at {candidate} or {fallback}')

def load_clients() -> List[ClientProfile]:
    file_path = get_synthetic_data_path()
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        raw_list = json.load(f)
    return [ClientProfile(**item) for item in raw_list]

def build_advisor_insights() -> List[AdvisorInsight]:
    clients = load_clients()
    insights: List[AdvisorInsight] = []

    for client in clients:
        (
            score,
            level,
            drivers,
            evidence,
            category,
            summary,
            action
        ) = calculate_urgency_score(client)

        last_contact = datetime.fromisoformat(client.lastContactDate.replace('Z', '+00:00'))
        days_since_review = (REFERENCE_DATE.date() - last_contact.date()).days
        is_review_overdue = (days_since_review - client.reviewCadenceDays) > 0

        insight = AdvisorInsight(
            id=f'ins_{client.id}',
            clientId=client.id,
            clientName=client.fullName,
            totalAum=client.totalAum,
            cashBalance=client.cashBalance,
            riskTolerance=client.riskTolerance,
            urgencyScore=score,
            urgencyLevel=level,
            primaryCategory=category,
            summary=summary,
            detectedAt=REFERENCE_DATE.isoformat(),
            daysSinceLastReview=days_since_review,
            isReviewOverdue=is_review_overdue,
            dataFreshnessDays=client.dataQuality.daysSinceSync,
            scoreDrivers=drivers,
            evidence=evidence,
            suggestedAction=action
        )
        insights.append(insight)

    # Sort strictly descending by urgency score
    insights.sort(key=lambda x: x.urgencyScore, reverse=True)
    return insights

def get_worklist_response(urgency_filter: Optional[str] = None) -> WorklistResponse:
    all_insights = build_advisor_insights()

    critical_count = sum(1 for i in all_insights if i.urgencyLevel == 'critical')
    high_count = sum(1 for i in all_insights if i.urgencyLevel == 'high')
    medium_count = sum(1 for i in all_insights if i.urgencyLevel == 'medium')
    low_count = sum(1 for i in all_insights if i.urgencyLevel == 'low')

    filtered = all_insights
    if urgency_filter and urgency_filter.lower() != 'all':
        filtered = [i for i in all_insights if i.urgencyLevel.lower() == urgency_filter.lower()]

    return WorklistResponse(
        totalCount=len(all_insights),
        criticalCount=critical_count,
        highCount=high_count,
        mediumCount=medium_count,
        lowCount=low_count,
        items=filtered
    )

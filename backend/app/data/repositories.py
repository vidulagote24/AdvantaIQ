"""Data Access and Persistence Repository.

Manages SQLite storage for:
- Synthetic client records
- Advisor notes
- Insight status transitions and audit logs
- Deterministic calculation caching
"""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from app.config import settings
from app.data.generate_synthetic_data import generate_synthetic_dataset
from app.services.analytics import (
    calculate_performance_gap,
    calculate_goal_trajectory,
    calculate_allocation_drift,
    evaluate_persistence,
    evaluate_advice_follow_through,
    assess_data_quality_and_freshness
)
from app.services.prioritization import compute_priority_score
from app.services.insights import generate_client_insights
from app.services.advisor_brief import generate_advisor_brief
from app.schemas import (
    ClientSummarySchema,
    ClientDetailSchema,
    InsightSchema,
    AdvisorNoteSchema,
    AdvisorBriefSchema,
    InsightStatusEnum,
    SeverityEnum,
    ConfidenceEnum
)

class ClientRepository:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.DB_PATH
        self._init_db()
        self._ensure_dataset_loaded()
        
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Creates SQLite tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Clients table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    client_id TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    risk_profile TEXT NOT NULL,
                    data_as_of TEXT NOT NULL,
                    planted_scenario_id TEXT,
                    raw_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Advisor notes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS advisor_notes (
                    note_id TEXT PRIMARY KEY,
                    client_id TEXT NOT NULL,
                    author TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (client_id) REFERENCES clients (client_id)
                )
            """)
            
            # Insight status overrides table (for workflow actions)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS insight_statuses (
                    insight_id TEXT PRIMARY KEY,
                    client_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Audit log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    log_id TEXT PRIMARY KEY,
                    action TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()

    def _ensure_dataset_loaded(self):
        """Loads synthetic dataset if clients table is empty."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM clients")
            count = cursor.fetchone()["cnt"]
            
            if count == 0:
                dataset = generate_synthetic_dataset(
                    num_clients=settings.DATASET_CLIENT_COUNT,
                    seed=settings.DATASET_RANDOM_SEED
                )
                for c in dataset["clients"]:
                    cursor.execute("""
                        INSERT INTO clients (client_id, display_name, risk_profile, data_as_of, planted_scenario_id, raw_data)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        c["client_id"],
                        c["display_name"],
                        c["risk_profile"],
                        c["data_as_of"],
                        c.get("planted_scenario_id"),
                        json.dumps(c)
                    ))
                conn.commit()

    def get_raw_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT raw_data FROM clients WHERE client_id = ?", (client_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return json.loads(row["raw_data"])

    def evaluate_client(self, client_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], List[InsightSchema]]:
        """Executes full deterministic analytics, scoring, and insight generation pipeline for a client."""
        as_of_date = client_data.get("data_as_of", "2026-03-31")
        portfolio = client_data.get("portfolio", {})
        goal = client_data.get("goal", {})
        hist_perf = client_data.get("historical_performance", [])
        advice_hist = client_data.get("advice_history", [])
        
        # 1. Performance gap (latest period)
        latest_perf = hist_perf[0] if hist_perf else {}
        perf_gap = calculate_performance_gap(
            client_return_pct=latest_perf.get("client_return_pct"),
            benchmark_return_pct=latest_perf.get("benchmark_return_pct"),
            benchmark_id=latest_perf.get("benchmark_id"),
            period_start=latest_perf.get("period_start"),
            period_end=latest_perf.get("period_end"),
            aligned=latest_perf.get("aligned", True)
        )
        
        # 2. Goal trajectory
        goal_traj = calculate_goal_trajectory(
            goal_amount=goal.get("goal_amount", 0.0),
            current_value=portfolio.get("total_value", 0.0),
            start_date=goal.get("start_date", "2020-01-01"),
            goal_date=goal.get("goal_date", "2035-12-31"),
            as_of_date=as_of_date,
            initial_amount=goal.get("initial_amount", 0.0),
            monthly_contribution=goal.get("monthly_contribution", 0.0),
            assumed_annual_rate_pct=goal.get("assumed_annual_rate_pct", 6.0)
        )
        
        # 3. Allocation drift
        drift_eval = calculate_allocation_drift(
            holdings=portfolio.get("holdings", []),
            target_allocation=portfolio.get("target_allocation"),
            drift_alert_threshold_pct=settings.DRIFT_ALERT_THRESHOLD_PCT
        )
        
        # 4. Persistence
        persistence_eval = evaluate_persistence(
            historical_periods=hist_perf,
            min_periods=settings.PERSISTENCE_MIN_PERIODS
        )
        
        # 5. Advice follow-through
        advice_eval = evaluate_advice_follow_through(
            advice_records=advice_hist,
            current_portfolio_snapshot=portfolio
        )
        
        # 6. Data quality & freshness
        data_quality = assess_data_quality_and_freshness(
            client_data=client_data,
            as_of_date=as_of_date,
            stale_threshold_days=settings.FRESHNESS_STALE_THRESHOLD_DAYS,
            warning_threshold_days=settings.FRESHNESS_WARNING_DAYS
        )
        
        analytics_results = {
            "performance_gap": perf_gap,
            "goal_trajectory": goal_traj,
            "allocation_drift": drift_eval,
            "persistence": persistence_eval,
            "advice_follow_through": advice_eval,
            "data_quality": data_quality
        }
        
        # Prioritization score
        prioritization = compute_priority_score(
            goal_trajectory=goal_traj,
            performance_gap=perf_gap,
            persistence=persistence_eval,
            drift_eval=drift_eval,
            last_review_date_str=client_data.get("last_review_date", "2025-01-01"),
            as_of_date_str=as_of_date,
            data_quality=data_quality
        )
        
        # Insights
        insights = generate_client_insights(
            client_data=client_data,
            analytics_results=analytics_results,
            prioritization_result=prioritization
        )
        
        # Apply any persisted status overrides from SQLite
        insight_statuses = self._get_insight_statuses(client_data["client_id"])
        for ins in insights:
            if ins.insight_id in insight_statuses:
                ins.status = InsightStatusEnum(insight_statuses[ins.insight_id]["status"])
                
        return analytics_results, prioritization, insights

    def _get_insight_statuses(self, client_id: str) -> Dict[str, Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT insight_id, status, reason, updated_at FROM insight_statuses WHERE client_id = ?", (client_id,))
            return {row["insight_id"]: dict(row) for row in cursor.fetchall()}

    def get_all_clients_summary(
        self,
        search: Optional[str] = None,
        risk_profile: Optional[str] = None,
        severity: Optional[str] = None
    ) -> List[ClientSummarySchema]:
        """Returns summarized client list ranked deterministically by priority score."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT raw_data FROM clients")
            rows = cursor.fetchall()
            
        summaries: List[ClientSummarySchema] = []
        for r in rows:
            c = json.loads(r["raw_data"])
            
            if search:
                s_lower = search.lower()
                if s_lower not in c["display_name"].lower() and s_lower not in c["client_id"].lower():
                    continue
                    
            if risk_profile and c["risk_profile"] != risk_profile:
                continue
                
            analytics, prior, insights = self.evaluate_client(c)
            
            if severity and prior["severity"].value != severity:
                continue
                
            last_review = c.get("last_review_date", "2025-01-01")
            as_of = c.get("data_as_of", "2026-03-31")
            try:
                days = (datetime.strptime(as_of, "%Y-%m-%d").date() - datetime.strptime(last_review, "%Y-%m-%d").date()).days
            except Exception:
                days = 999
                
            active_insights = sum(1 for ins in insights if ins.status == InsightStatusEnum.ACTIVE)
            primary_concern = prior["contributing_signals"][0] if prior["contributing_signals"] else "Normal monitoring"
            
            summaries.append(
                ClientSummarySchema(
                    client_id=c["client_id"],
                    display_name=c["display_name"],
                    risk_profile=c["risk_profile"],
                    total_portfolio_value=c.get("portfolio", {}).get("total_value", 0.0),
                    goal_name=c.get("goal", {}).get("goal_name", "Primary Goal"),
                    goal_progress_pct=analytics["goal_trajectory"].get("progress_pct", 0.0),
                    priority_score=prior["overall_score"],
                    severity=prior["severity"],
                    confidence_level=prior["confidence_level"],
                    last_review_date=last_review,
                    days_since_review=days,
                    data_as_of=as_of,
                    active_insight_count=active_insights,
                    primary_concern=primary_concern,
                    planted_scenario_id=c.get("planted_scenario_id")
                )
            )
            
        # Deterministic sorting: priority_score DESC, then client_id ASC
        summaries.sort(key=lambda s: (-s.priority_score, s.client_id))
        return summaries

    def get_client_detail(self, client_id: str) -> Optional[ClientDetailSchema]:
        """Returns full detailed client profile with calculated metrics and notes."""
        raw = self.get_raw_client(client_id)
        if not raw:
            return None
            
        analytics, prior, insights = self.evaluate_client(raw)
        notes = self.get_client_notes(client_id)
        
        last_review = raw.get("last_review_date", "2025-01-01")
        as_of = raw.get("data_as_of", "2026-03-31")
        try:
            days = (datetime.strptime(as_of, "%Y-%m-%d").date() - datetime.strptime(last_review, "%Y-%m-%d").date()).days
        except Exception:
            days = 999
            
        goal_data = raw.get("goal", {})
        goal_traj = analytics["goal_trajectory"]
        
        goal_schema = {
            "goal_name": goal_data.get("goal_name", "Primary Goal"),
            "goal_amount": goal_data.get("goal_amount", 0.0),
            "goal_date": goal_data.get("goal_date", ""),
            "current_value": raw.get("portfolio", {}).get("total_value", 0.0),
            "progress_pct": goal_traj.get("progress_pct", 0.0),
            "modeled_target_value": goal_traj.get("modeled_target_value"),
            "trajectory_status": goal_traj.get("trajectory_status", "UNKNOWN"),
            "shortfall_amount": goal_traj.get("shortfall_amount"),
            "shortfall_pct": goal_traj.get("shortfall_pct"),
            "monthly_contribution_assumed": goal_data.get("monthly_contribution", 0.0),
            "assumed_return_rate_pct": goal_data.get("assumed_annual_rate_pct", 6.0),
            "assumptions_description": goal_traj.get("assumptions_description", "")
        }
        
        return ClientDetailSchema(
            client_id=raw["client_id"],
            display_name=raw["display_name"],
            risk_profile=raw["risk_profile"],
            data_as_of=as_of,
            last_review_date=last_review,
            days_since_review=days,
            portfolio=raw.get("portfolio", {}),
            goal=goal_schema,
            historical_performance=raw.get("historical_performance", []),
            advice_history=raw.get("advice_history", []),
            notes=notes,
            insights=insights,
            priority_score=prior["overall_score"],
            score_components=prior["score_components"],
            severity=prior["severity"],
            confidence_level=prior["confidence_level"],
            confidence_reason=prior["confidence_reason"],
            data_warnings=prior["data_quality_warnings"],
            suggested_review=prior["suggested_review"],
            planted_scenario_id=raw.get("planted_scenario_id")
        )

    def get_client_brief(self, client_id: str) -> Optional[AdvisorBriefSchema]:
        """Generates evidence-backed advisor brief for client review."""
        raw = self.get_raw_client(client_id)
        if not raw:
            return None
        analytics, prior, insights = self.evaluate_client(raw)
        return generate_advisor_brief(raw, analytics, prior, insights)

    def get_all_insights(
        self,
        sort: str = "priority",
        severity: Optional[str] = None,
        type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[InsightSchema]:
        """Aggregates all insights across clients and ranks them."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT raw_data FROM clients")
            rows = cursor.fetchall()
            
        all_insights: List[InsightSchema] = []
        for r in rows:
            c = json.loads(r["raw_data"])
            _, _, insights = self.evaluate_client(c)
            for ins in insights:
                if severity and ins.severity.value != severity:
                    continue
                if type and ins.type.value != type:
                    continue
                if status and ins.status.value != status:
                    continue
                all_insights.append(ins)
                
        if sort == "priority":
            all_insights.sort(key=lambda x: (-x.score, x.client_id, x.insight_id))
        elif sort == "created_at":
            all_insights.sort(key=lambda x: x.created_at, reverse=True)
            
        return all_insights

    def update_insight_status(self, insight_id: str, status: InsightStatusEnum, reason: Optional[str] = None) -> bool:
        """Updates insight status with audit logging."""
        # Extract client_id from insight_id (pattern: INSIGHT-{client_id}-{type})
        parts = insight_id.split("-")
        client_id = f"{parts[1]}-{parts[2]}" if len(parts) >= 3 else "UNKNOWN"
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO insight_statuses (insight_id, client_id, status, reason, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (insight_id, client_id, status.value, reason))
            
            # Audit log
            cursor.execute("""
                INSERT INTO audit_log (log_id, action, entity_type, entity_id, details)
                VALUES (?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), "UPDATE_STATUS", "INSIGHT", insight_id, json.dumps({"status": status.value, "reason": reason})))
            
            conn.commit()
            return True

    def add_client_note(self, client_id: str, author: str, content: str, category: str) -> AdvisorNoteSchema:
        """Adds an advisor note with audit trail."""
        note_id = f"NOTE-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO advisor_notes (note_id, client_id, author, content, category, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (note_id, client_id, author, content, category, now_iso))
            
            # Audit log
            cursor.execute("""
                INSERT INTO audit_log (log_id, action, entity_type, entity_id, details)
                VALUES (?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), "ADD_NOTE", "CLIENT", client_id, json.dumps({"note_id": note_id, "author": author, "category": category})))
            
            conn.commit()
            
        return AdvisorNoteSchema(
            note_id=note_id,
            client_id=client_id,
            author=author,
            content=content,
            category=category,
            created_at=now_iso
        )

    def get_client_notes(self, client_id: str) -> List[AdvisorNoteSchema]:
        """Retrieves advisor notes for a client."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT note_id, client_id, author, content, category, created_at
                FROM advisor_notes
                WHERE client_id = ?
                ORDER BY created_at DESC
            """, (client_id,))
            return [AdvisorNoteSchema(**dict(row)) for row in cursor.fetchall()]

# Singleton repository instance
client_repository = ClientRepository()

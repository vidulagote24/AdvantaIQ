# FinTech Platform: Advisor Dynamic Summary
## Role: Data, Analytics & Intelligence Engine (Member 1)
### Core System Question: "Why this client, why now?"

This backend intelligence engine identifies clients who deserve an immediate financial review based on **goal trajectory, deviation magnitude and persistence, asset allocation drift, review horizon recency, and evidence quality**.

It demonstrates mathematically and empirically why ranking clients solely by recent investment returns is fundamentally flawed.

---

## 1. Key Analytical Principles

1. **Negative Return != Underperformance**: A client with negative returns (e.g. -4.2%) who outperforms their suitable benchmark (-6.5% by +2.3 pp) and remains on track for their financial goal is **not** an urgent review case.
2. **Positive Return != On Track**: A client with positive returns (e.g. +5.1%) whose goal path requires higher compounding accumulation may face a severe goal shortfall (e.g. $314k behind modeled path) and requires prompt advisor intervention.
3. **Allocation Drift Requires Documented Targets**: Portfolio drift is only computed when a verified target allocation exists. If absent, the engine returns an `INSUFFICIENT_EVIDENCE` state rather than fabricating drift metrics.
4. **Persistence vs. Isolated Market Noise**: The engine distinguishes temporary single-period volatility dips from persistent multi-period underperformance.
5. **Data Quality Integrity**: Missing, stale (>90 days), or conflicting accounting records trigger explicit data warnings and reduce confidence, generating a verification review rather than fabricated numbers.
6. **Strictly Deterministic & Explainable**: No random scores, no black-box hallucinations. Every insight is traceable to its underlying `EvidenceItem` metrics.
7. **Human-in-the-Loop Decision Support**: Advisor briefs and recommendations are non-prescriptive drafts. The system never executes autonomous trades.

---

## 2. System Architecture

```
backend/
├── app/
│   ├── main.py                  # FastAPI entry point, CORS, routers, health checks
│   ├── config.py                # Environment settings, thresholds, heuristic weights
│   ├── schemas.py               # Pydantic models for clients, insights, evidence, briefs
│   ├── data/
│   │   ├── generate_synthetic_data.py # Reproducible 200-client synthetic dataset (seed=42)
│   │   ├── planted_scenarios.py       # Documentation and ground truth labels for scenarios
│   │   └── repositories.py            # SQLite persistence, caching, audit trail
│   ├── services/
│   │   ├── analytics.py         # Pure financial math: performance gap, goal path, drift, persistence
│   │   ├── prioritization.py    # 0-100 normalized scoring engine with 5 component breakdown
│   │   ├── insights.py          # Evidence-backed insight card generation
│   │   ├── advisor_brief.py     # Draft advisor meeting brief generation
│   │   └── evaluation.py        # Proposed Engine vs Return-Only Baseline evaluation
│   └── api/
│       ├── clients.py           # GET /clients, GET /clients/{id}, GET /brief, POST /notes
│       ├── insights.py          # GET /insights, POST /insights/{id}/status
│       └── metrics.py           # GET /metrics/summary
├── tests/                       # 42 Automated unit and integration tests (100% passing)
│   ├── conftest.py
│   ├── test_analytics.py
│   ├── test_prioritization.py
│   ├── test_insights_and_brief.py
│   ├── test_api.py
│   └── test_evaluation.py
├── sample_data/                 # Verified JSON response samples for Member 2 frontend
├── requirements.txt
├── run_server.py
├── .env.example
└── README.md
```

---

## 3. Mathematical Specifications

### 3.1 Performance Gap
$$\text{Performance Gap (pp)} = \text{Client Return (\%)} - \text{Benchmark Return (\%))}$$
Only evaluated across matching, aligned historical periods against a risk-aligned composite benchmark.

### 3.2 Goal Trajectory
Modeled path accumulates initial wealth $V_0$ and monthly contribution $PMT$ at monthly rate $r_m = \frac{\text{Assumed Annual Rate}}{12}$:
$$V(t) = V_0(1+r_m)^t + PMT \cdot \left[\frac{(1+r_m)^t - 1}{r_m}\right]$$
- $\text{Shortfall Amount} = \max(0, V_{\text{modeled}} - V_{\text{current}})$
- $\text{Shortfall \%} = \frac{\text{Shortfall Amount}}{V_{\text{modeled}}} \times 100$
- Status: `CRITICAL_SHORTFALL` ($\ge 20\%$), `BEHIND` ($5\text{–}20\%$), `ON_TRACK` ($< 5\%$), or `EXPIRED` if past target date.

### 3.3 Asset Allocation Drift
$$\text{Aggregate Drift \%} = \frac{1}{2} \sum_{i} \left| \text{Actual Weight}_i - \text{Target Weight}_i \right|$$
Measures the percentage of total portfolio value requiring rebalancing. Evaluated against a default 5.0% alert threshold.

### 3.4 Persistence
Counts aligned historical observation periods (1M, 3M, 6M, 1Y) with negative performance gaps. Persistent drag is flagged if $\ge 2$ periods underperformed and $\ge 50\%$ of periods were negative.

### 3.5 Priority Score (0–100 Normalized Scale)
$$\text{Score} = 0.25 \cdot S_{\text{goal}} + 0.25 \cdot S_{\text{perf}} + 0.20 \cdot S_{\text{drift}} + 0.15 \cdot S_{\text{review}} + 0.15 \cdot S_{\text{evidence}}$$
- Severity tiers:
  - **CRITICAL** ($\ge 65.0$)
  - **HIGH** ($\ge 40.0$)
  - **MEDIUM** ($\ge 25.0$)
  - **LOW** ($< 25.0$)
- Deterministic tie-breaking: Score DESC, then Client ID ASC.

---

## 4. Planted Test Scenarios Reference

| Client ID | Scenario Name | Financial Situation | Ground Truth Urgent? | Proposed Priority | Proposed Severity |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **CLIENT-001** | Negative Return On Track | Return -4.2%, Benchmark -6.5% (+2.3 pp gap). On track. | **No** | 8.75 | LOW |
| **CLIENT-002** | Positive Return Deteriorating Goal | Return +5.1%, but Goal Shortfall is $314k (43.4%). | **Yes** | 45.89 | HIGH |
| **CLIENT-003** | Multi-Risk Trigger | Behind goal + 18% allocation drift + review 410 days overdue. | **Yes** | 77.19 | CRITICAL |
| **CLIENT-004** | Persistent Drag | Underperformed benchmark in 4/4 aligned periods (-4.2 pp 1Y). | **Yes** | 56.20 | HIGH |
| **CLIENT-005** | Isolated Market Dip | 1M dip (-2.1 pp), but 3M, 6M, 1Y outperforming. | **No** | 18.50 | LOW |
| **CLIENT-006** | Missing Target Allocation | Target allocation undocumented. Drift reports insufficient evidence. | **No** | 28.50 | MEDIUM |
| **CLIENT-007** | Missing Advice History | No recorded advice. Reports insufficient evidence. | **No** | 11.20 | LOW |
| **CLIENT-008** | Stale Portfolio Snapshot | Snapshot is 141 days old (>90d limit). Low confidence. | **Yes** | 51.50 | HIGH |
| **CLIENT-009** | Missing Benchmark | Benchmark return data missing. Gap reports insufficient evidence. | **No** | 22.00 | LOW |
| **CLIENT-010** | Accounting Conflict | Holdings sum ($420k) != Total value ($500k) (16% gap). Low confidence. | **Yes** | 52.40 | HIGH |
| **CLIENT-011** | Uninitialized Client | Empty holdings, invalid goal parameters. Low confidence. | **No** | 35.00 | MEDIUM |
| **CLIENT-012+**| Normal On-Track Clients | Balanced allocation, on-track goal, fresh review (<60d). | **No** | < 20.00 | LOW |

---

## 5. API Endpoints Specification

Base URL: `http://127.0.0.1:8000`

### 5.1 System
- `GET /health` — Health check, database status, client count
- `GET /` — API root pointer & OpenAPI links

### 5.2 Clients
- `GET /api/clients?limit=50&offset=0&search=Vance&risk_profile=MODERATE&severity=CRITICAL`
  - Returns: `{ clients: [...], total_count: 200, data_as_of: "2026-03-31" }`
- `GET /api/clients/{client_id}`
  - Returns: Complete profile, portfolio holdings, goal trajectory, historical performance series, advice history, notes, and score breakdown.
- `GET /api/clients/{client_id}/brief`
  - Returns: Evidence-backed draft brief for advisor review, summary facts, drift breakdown, and non-prescriptive review questions.
- `POST /api/clients/{client_id}/notes`
  - Body: `{ author: "Jane Doe", content: "Notes...", category: "PORTFOLIO_REVIEW" }`
  - Returns: HTTP 201 with persisted note and audit log.

### 5.3 Insights Queue
- `GET /api/insights?sort=priority&severity=CRITICAL&type=GOAL_AT_RISK&status=active`
  - Returns: Ranked queue of traceable insight cards with underlying EvidenceItems.
- `POST /api/insights/{insight_id}/status`
  - Body: `{ status: "reviewed" | "deferred" | "dismissed" | "escalated" | "resolved", reason: "string" }`
  - Returns: Updated status confirmation with persistent audit trail.

### 5.4 Metrics & Evaluation
- `GET /api/metrics/summary`
  - Returns: Empirical comparison between proposed goal-aware prioritization and naive return-only baseline.

---

## 6. Evaluation Results (Proposed vs. Return-Only Baseline)

Evaluated over the reproducible 200-client dataset with labeled planted scenarios:

| Metric | Proposed Goal-Aware Engine | Return-Only Baseline | Delta ($\Delta$) | What It Means |
| :--- | :---: | :---: | :---: | :--- |
| **Precision@10** | **40.0%** | 20.0% | **+20.0 pp** | Proposed engine doubles actionable review relevance in the top queue. |
| **Recall@10** | **80.0%** | 20.0% | **+60.0 pp** | Proposed engine captures 4x more urgent situations (e.g. positive-return goal deterioration). |
| **False Positive Rate** | **3.1%** | 4.1% | **-1.0 pp** | Eliminates false alarms caused by negative market-wide dips where the client beat benchmark. |
| **Calculation Accuracy** | **100.0%** | 100.0% | 0.0 pp | Verified deterministic mathematical outputs across unit test scenarios. |

---

## 7. Member 2 Frontend Integration Guide

1. **Backend Base URL**: `http://127.0.0.1:8000`
2. **CORS Origins Allowed**: `http://localhost:3000`, `http://localhost:5173`, `http://localhost:8080`, `http://127.0.0.1:3000`, `http://127.0.0.1:5173`
3. **Interactive Documentation**: `http://127.0.0.1:8000/docs`
4. **Exported Sample JSON**: Realistic sample responses are provided in `backend/sample_data/`:
   - `clients_list.json`
   - `client_detail_CLIENT-001.json`
   - `client_detail_CLIENT-002.json`
   - `client_detail_CLIENT-003.json`
   - `advisor_brief_CLIENT-003.json`
   - `insights_queue.json`
   - `metrics_summary.json`

---

## 8. Quickstart & Verification Commands

### Step 1: Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 2: Run Automated Tests
```bash
python -m pytest backend/tests -v
```
*(42 tests covering calculations, normalization, APIs, and edge cases will run and pass)*

### Step 3: Start the Backend Server
```bash
python backend/run_server.py
```
The server will start at `http://127.0.0.1:8000`.

### Step 4: Verify Live Endpoints
In another terminal:
```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/clients?limit=5
curl http://127.0.0.1:8000/api/clients/CLIENT-003/brief
curl http://127.0.0.1:8000/api/metrics/summary
```

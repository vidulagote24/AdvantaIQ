# AdvantaIQ

> **AI-Powered Financial Advisor Intelligence Platform**  
> *"Know Who Needs Attention. Understand Why. Act at the Right Time."*

---

## 1. Overview & Architecture

AdvantaIQ empowers wealth management advisors to proactively identify at-risk client relationships, detect portfolio drift, prevent cash drag, adhere to mandatory fiduciary review cadences, and execute structured follow-up workflows.

The platform is built with a decoupled 3-tier architecture:
- **Frontend (`frontend/`):** React 18, TypeScript, and Vite. Features a prioritized advisor worklist, multi-currency selector (INR default, USD, EUR, GBP, AED), an interactive Evidence Inspector ("Understand Why"), a deterministic Review Brief generator, and full Advisor Workflow action tracking (notes, deferrals, resolutions).
- **Backend (`backend/`):** Python 3.11+ and FastAPI with Pydantic schemas. Features a deterministic, explainable multi-signal urgency scoring engine (0–100 scale, category maxima strictly sum to 100) and REST endpoints.
- **Shared Data & Fixtures (`shared/`):** 100% synthetic investor personas adhering to strict privacy and compliance safeguards (zero real PII, zero external public AI API dependencies).

---

## 2. Quickstart & Running Locally

### Backend (FastAPI)

1. **Set up environment & dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Run backend tests:**
   ```bash
   # From repository root
   python -m pytest backend/tests -v
   ```

3. **Start the FastAPI server:**
   ```bash
   # From backend directory
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   Interactive Swagger API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

### Frontend (React + Vite)

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Verify build & TypeScript contracts:**
   ```bash
   npm run build
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```
   The advisor dashboard will open at [http://localhost:5173](http://localhost:5173) (or `http://localhost:5174` if 5173 is in use).

---

## 3. Key Implemented Capabilities

### A. Explainable Multi-Signal Scoring Engine (0–100)
Every point awarded is auditable and backed by a concrete metric driver across 5 strictly bounded categories:
1. **Allocation Drift (Max 30 pts):** Equity and fixed income deviation beyond risk-tolerance thresholds (`±5.0%`).
2. **Goal Milestones & Funding (Max 30 pts):** Funding gaps and near-term deadlines (<90 days).
3. **Fiduciary Review Cadence (Max 20 pts):** Days elapsed since last meeting relative to client's mandatory cadence.
4. **Cash Drag & Excess Liquidity (Max 10 pts):** Uninvested cash exceeding 10% policy threshold.
5. **Data Freshness & Custodian Sync (Max 10 pts):** Custodian sync delays (>5 days) or missing cost basis.
*Total Theoretical Maximum:* Exactly 100 points.

### B. Global Multi-Currency Support
- **Default Display Currency:** INR (Indian Rupee, ₹) with Indian numbering format (`₹23,95,42,500`).
- **Supported Currencies:** INR (₹), USD ($), EUR (€), GBP (£), and AED (د.إ).
- **Mathematical Conversion:** Converted using institutional demo benchmark rates (`1 USD = 84.05 INR`).
- **Source Attribution:** Native records are denominated in USD; original source amounts remain visible on hover tooltips.
- **Score Invariance:** Currency selection **never** alters urgency scores, drift percentages, or worklist rankings.

### C. Advisor Workflow & Actions
- **Evidence & Diagnosis (Tab 1):** Point-by-point score driver breakdown, verified financial evidence table (Observed vs. Policy Threshold), and recommended next actions.
- **Deterministic Review Brief (Tab 2):** Generates a grounded client meeting memo without LLM hallucinations or external API dependencies. Includes 1-click clipboard export.
- **Advisor Notes (Tab 3):** Capture and view time-stamped meeting notes and rationale.
- **Defer Follow-up:** Select a follow-up date and record deferral rationale. Client remains in queue with a visible `Deferred: YYYY-MM-DD` status badge.
- **Resolve Insight:** Mark resolved with an audit resolution note. Original priority score and evidence are preserved.
- **Workflow Filtering:** Filter queue by `All Statuses`, `Open Action`, `Deferred`, and `Resolved`.
- **Persistence:** Local browser storage (`advantaiq_advisor_workflow_states`) labeled honestly as demo-only fallback pending Member 1 backend routes.

---

## 4. Test Suites & Verification Commands

Execute all automated verification checks from repository root or `frontend/`:

```bash
# 1. Frontend TypeScript & Production Bundle Check
npm run build --prefix frontend

# 2. Currency Service Unit Tests (Conversion, Formatting, Invariance)
node frontend/test_currency.mjs

# 3. Advisor Workflow Unit Tests (Notes, Deferrals, Briefs, Reopen, Invariance)
node --experimental-strip-types frontend/test_workflow.ts

# 4. Backend Regression Test Suite (FastAPI routes, scoring boundaries, sorting)
python -m pytest backend/tests -v

# 5. Mock vs. Live Consistency Suite (100% parity across scores, drivers, counts)
python backend/verify_consistency.py
```

---

## 5. Reproducible End-to-End Demo Script

1. Open `http://localhost:5174/` in your browser.
2. Verify default currency **INR (₹)**. Switch to **USD ($)** in the top right; observe values convert mathematically while urgency scores (`80`, `60`, `45`) remain invariant.
3. Click **Review** on the top client, **Eleanor Vance** (`cli_001`, Score: `80 / 100`, Critical).
4. In **Evidence & Diagnosis**, inspect the 5 score drivers, review cadence (`411d overdue`), custodian sync (`1d ago`), and the observed drift vs. policy threshold table.
5. In **Prepare Review Brief**, inspect the deterministic briefing memo and click **Copy Briefing Memo** to copy to clipboard.
6. In **Advisor Actions & Notes**:
   - Add a note: `"Called Eleanor Vance regarding 14.2% equity drift. Rebalancing proposed for next Monday."` and click **Save Note**.
   - Select **Defer Follow-Up**, set date to `2026-11-15`, enter reason `"Waiting for CPA tax-loss review"`, and click **Save Deferral**.
7. Close modal: observe the table row displays `DEFERRED: 2026-11-15` and a `1` note badge.
8. Filter by **Workflow: Deferred**; reload page (`F5`) to verify refresh persistence.
9. Open modal again, select **Mark as Resolved**, enter resolution notes, and observe the status update to `RESOLVED`.

---

## 6. Architecture & Handoff Documentation

- [BACKEND_WORKFLOW_CONTRACTS.md](file:///E:/AdvantaIQ/docs/BACKEND_WORKFLOW_CONTRACTS.md) — Proposed backend endpoints (`GET /workflow`, `PATCH /workflow/status`, `POST /notes`) for Member 1.
- [MEMBER_2_HANDOFF.md](file:///E:/AdvantaIQ/docs/MEMBER_2_HANDOFF.md) — Detailed Member 2 completion checklist, boundaries, and handoff instructions.
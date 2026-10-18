# Member 2 (Frontend Lead) Handoff Package

**Author:** Member 2 (Frontend, Advisor UX, Workflow & Demo Lead)  
**Recipient:** Member 1 (Backend & Data Lead)  
**Date:** 2026-10-18  
**Repository:** `E:\AdvantaIQ`  
**Branch:** `fix/milestone1-audit`  
**Status:** READY FOR HANDOFF (GO)

---

## 1. Executive Summary

Member 2 has completed all major frontend and UX deliverables for the AdvantaIQ MVP:
1. Prioritized Advisor Worklist with deterministic ranking, search, sorting, and urgency filters.
2. Global Currency Switcher with INR default, USD/EUR/GBP/AED conversions, and rate transparency.
3. 3-Tab Evidence & Diagnosis Modal (`EvidenceModal.tsx`):
   - **Tab 1:** Multi-factor score driver inspection and policy threshold comparison.
   - **Tab 2:** Deterministic, evidence-grounded Client Review Brief generator with 1-click clipboard export.
   - **Tab 3:** Advisor Actions & Notes (Record notes, Defer with date and rationale, Resolve with audit note).
4. Workflow Status Filtering in the main worklist (`All Statuses`, `Open Action`, `Deferred`, `Resolved`) and status badges in the `Workflow & Cadence` table column.
5. 100% test pass rate across frontend production build, currency unit tests, advisor workflow unit tests, backend regression tests, and mock/live parity checks.

---

## 2. Files & Components Owned or Modified by Member 2

| Path | Category | Purpose |
|---|---|---|
| `frontend/src/contracts/types.ts` | Contracts | Added `WorkflowStatus`, `AdvisorNote`, `ClientWorkflowState`, `ReviewBrief` types. |
| `frontend/src/services/currencyService.ts` | Currency | Centralized formatting, rate conversions, source attribution, and disclaimers. |
| `frontend/src/context/CurrencyContext.tsx` | Currency | React context providing currency selection and persistence. |
| `frontend/src/components/CurrencySelector.tsx` | UI | Compact header currency dropdown. |
| `frontend/src/services/workflowService.ts` | Workflow | `localStorage` persistence, status transitions, note creation, deterministic brief generation (`generateClientReviewBrief`), and plain-text briefing formatter (`formatBriefAsText`). |
| `frontend/src/context/WorkflowContext.tsx` | Workflow | React context providing reactive workflow state and cross-tab listener. |
| `frontend/src/components/EvidenceModal.tsx` | UI | 3-tab review experience: Evidence & Diagnosis, Review Brief, Advisor Actions & Notes. |
| `frontend/src/components/WorklistTable.tsx` | UI | Main worklist table, workflow dropdown filter, sort controls, and `Workflow & Cadence` column. |
| `frontend/src/components/UrgencyBadge.tsx` | UI | Urgency tier indicators (`Critical`, `High`, `Medium`, `Low`). |
| `frontend/src/components/WorklistSummary.tsx` | UI | High-level urgency metric cards. |
| `frontend/src/components/Header.tsx` | UI | Header with Mock/Live switch, currency dropdown, and system status indicator. |
| `frontend/src/App.tsx` | UI Root | App state, API loader, and modal trigger. |
| `frontend/test_currency.mjs` | Test | Unit tests for currency conversion and score invariance. |
| `frontend/test_workflow.ts` | Test | Unit tests for advisor workflow transitions, notes, brief generation, and invariance. |
| `backend/verify_consistency.py` | Test | Verifies 100% parity between Mock JSON and Live FastAPI responses. |
| `docs/BACKEND_WORKFLOW_CONTRACTS.md` | Contracts | Detailed REST API specifications for Member 1. |
| `README.md` | Docs | Full platform overview, setup guide, test commands, and demo script. |

---

## 3. Current Git & Working-Tree Status

- **Current Branch:** `fix/milestone1-audit`
- **Remote:** `https://github.com/vidulagote24/AdvantaIQ.git`
- **Commit Status:** Zero commits made; zero pushes executed. All changes reside cleanly in the working tree for Member 1 to review, commit, or merge.
- **Untracked Directories/Files:**
  - `README.md`, `backend/`, `docs/`, `frontend/`, `shared/`, `.gitignore`.

---

## 4. Existing API Dependencies & Frontend/Backend Boundary

### Endpoints Currently Consumed by Frontend:
1. `GET /api/v1/health` — Backend health check.
2. `GET /api/v1/advisors/worklist?urgency={all|critical|high|medium|low}` — Main worklist with scores, score drivers, and evidence.
3. `GET /api/v1/clients/{client_id}` — Individual client profile (fallback).

### Boundary Principle:
- The frontend supports both **Mock Mode** (default, offline-capable) and **Live Mode** (connects to FastAPI at `http://127.0.0.1:8000` via Vite proxy).
- Toggle switch in the header allows instantaneous switching without restarting servers.

---

## 5. Storage Limitation & Honest Labeling

- **Current Persistence Mechanism:** Browser `localStorage` under key `advantaiq_advisor_workflow_states`.
- **Honest Labeling:** The modal prominently informs the user:
  > *"Session Local Storage (Demo) — Notes and status updates are saved in your local browser storage for this hackathon evaluation."*
- **Behavior:** Notes, deferral dates, and resolutions survive page reloads and browser tab refreshes within the same browser session. They do not yet sync across different devices or browsers.

---

## 6. Exact Next Steps for Member 1

Member 1 should implement server-side persistence in `backend/app/api/v1/routes.py` for the three endpoints documented in [BACKEND_WORKFLOW_CONTRACTS.md](file:///E:/AdvantaIQ/docs/BACKEND_WORKFLOW_CONTRACTS.md):

1. **`GET /api/v1/clients/{client_id}/workflow`**
   - Returns client's current workflow status (`open`, `deferred`, `resolved`), deferral metadata, resolution notes, and note history.
2. **`PATCH /api/v1/clients/{client_id}/workflow/status`**
   - Updates workflow status. Validates that `deferredUntil` and `deferReason` are present if status is `deferred`, and `resolutionNote` is present if `resolved`.
   - **Crucial Rule:** Guarantees that the underlying portfolio urgency score, data freshness, and score drivers are **never mutated** by workflow state changes.
3. **`POST /api/v1/clients/{client_id}/notes`**
   - Appends an advisor note with `id`, `text`, `createdAt` timestamp, and `author`.

---

## 7. Known Scope Boundaries & Prohibited Assumptions

1. **Zero Public AI API Dependency:** The briefing memo generator is 100% deterministic and runs in `workflowService.ts`. Do not replace this with an external OpenAI/Anthropic/public LLM call that sends client PII or portfolio balances across the internet.
2. **No Trade Execution:** AdvantaIQ is a decision-support intelligence platform. Do not add endpoints that execute trades, move funds, or imply that recommended rebalances are automatically executed without advisor sign-off.
3. **Synthetic Data Disclosure:** All personas in `shared/data/synthetic/clients.json` are synthetic. Keep this clearly identified in all presentations and documentation.

---

## 8. Verification Commands

```bash
# Frontend build
npm run build --prefix frontend

# Currency tests
node frontend/test_currency.mjs

# Advisor workflow tests
node --experimental-strip-types frontend/test_workflow.ts

# Backend pytest suite
python -m pytest backend/tests -v

# Mock vs. Live consistency suite
python backend/verify_consistency.py
```

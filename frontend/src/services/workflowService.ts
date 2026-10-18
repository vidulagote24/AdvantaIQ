import type {
  AdvisorInsight,
  AdvisorNote,
  ClientWorkflowState,
  ReviewBrief,
  WorkflowStatus,
} from '../contracts/types.ts';

export const WORKFLOW_STORAGE_KEY = 'advantaiq_advisor_workflow_states';

export const WORKFLOW_DISCLAIMER =
  'Advisor workflow actions and notes are currently stored in your local browser session (Demo mode). API contracts for CRM backend synchronization are documented in docs/BACKEND_WORKFLOW_CONTRACTS.md.';

/**
 * Retrieve all workflow states from local storage.
 */
export function getAllWorkflowStates(): Record<string, ClientWorkflowState> {
  try {
    const raw = localStorage.getItem(WORKFLOW_STORAGE_KEY);
    if (raw) {
      return JSON.parse(raw);
    }
  } catch (err) {
    console.warn('Failed to parse workflow states from localStorage:', err);
  }
  return {};
}

/**
 * Persist workflow states dictionary to local storage.
 */
function saveAllWorkflowStates(states: Record<string, ClientWorkflowState>): void {
  try {
    localStorage.setItem(WORKFLOW_STORAGE_KEY, JSON.stringify(states));
  } catch (err) {
    console.error('Failed to save workflow state to localStorage:', err);
  }
}

/**
 * Get workflow state for a specific client. Defaults to 'open' if none exists.
 */
export function getClientWorkflowState(clientId: string): ClientWorkflowState {
  const all = getAllWorkflowStates();
  if (all[clientId]) {
    return all[clientId];
  }
  return {
    clientId,
    status: 'open',
    notes: [],
    updatedAt: new Date().toISOString(),
  };
}

/**
 * Update the workflow status of a client (open, deferred, resolved).
 */
export function updateClientWorkflowStatus(
  clientId: string,
  status: WorkflowStatus,
  details?: {
    deferredUntil?: string;
    deferReason?: string;
    resolutionNote?: string;
  }
): ClientWorkflowState {
  const all = getAllWorkflowStates();
  const current = all[clientId] || {
    clientId,
    status: 'open',
    notes: [],
    updatedAt: new Date().toISOString(),
  };

  const now = new Date().toISOString();
  const updated: ClientWorkflowState = {
    ...current,
    status,
    updatedAt: now,
  };

  if (status === 'deferred') {
    updated.deferredUntil = details?.deferredUntil || '';
    updated.deferReason = details?.deferReason || 'Advisor follow-up scheduled';
    // Clear resolved metadata if moving from resolved to deferred
    delete updated.resolvedAt;
    delete updated.resolutionNote;
  } else if (status === 'resolved') {
    updated.resolvedAt = now;
    updated.resolutionNote = details?.resolutionNote || 'Completed and verified by advisor';
    // Clear deferred metadata
    delete updated.deferredUntil;
    delete updated.deferReason;
  } else {
    // Reopened
    delete updated.deferredUntil;
    delete updated.deferReason;
    delete updated.resolvedAt;
    delete updated.resolutionNote;
  }

  all[clientId] = updated;
  saveAllWorkflowStates(all);
  return updated;
}

/**
 * Record an advisor note for a client.
 */
export function addAdvisorNote(
  clientId: string,
  text: string,
  author: string = 'Primary Advisor'
): AdvisorNote {
  const all = getAllWorkflowStates();
  const current = all[clientId] || {
    clientId,
    status: 'open',
    notes: [],
    updatedAt: new Date().toISOString(),
  };

  const newNote: AdvisorNote = {
    id: `note_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
    clientId,
    text: text.trim(),
    createdAt: new Date().toISOString(),
    author,
  };

  current.notes = [newNote, ...current.notes];
  current.updatedAt = new Date().toISOString();
  all[clientId] = current;
  saveAllWorkflowStates(all);

  return newNote;
}

/**
 * Deterministically generates an evidence-grounded review brief for an advisor.
 * Grounded solely on existing client portfolio metrics, goals, review schedule, and drivers.
 * Zero hallucination, zero public AI API dependency.
 */
export function generateClientReviewBrief(insight: AdvisorInsight): ReviewBrief {
  const keyIssues: string[] = [];
  const evidenceFindings: string[] = [];
  const suggestedAgenda: string[] = [];

  // Extract from positive score drivers
  for (const driver of insight.scoreDrivers) {
    if (driver.pointsAwarded > 0) {
      keyIssues.push(`${driver.category}: ${driver.rationale} (+${driver.pointsAwarded} pts)`);

      if (driver.category === 'Allocation Drift') {
        suggestedAgenda.push(
          'Review current asset allocation drift and present tax-loss harvested rebalance model.'
        );
        suggestedAgenda.push(
          'Re-verify risk profile suitability given recent market movements.'
        );
      } else if (driver.category === 'Goal Milestones') {
        suggestedAgenda.push(
          'Simulate goal milestone funding timeline and evaluate recurring contribution adjustment.'
        );
        suggestedAgenda.push(
          'Discuss potential milestone date flexibility or supplementary savings strategies.'
        );
      } else if (driver.category === 'Fiduciary Review') {
        suggestedAgenda.push(
          `Conduct annual fiduciary cadence check-in (last conducted ${insight.daysSinceLastReview} days ago).`
        );
        suggestedAgenda.push(
          'Review account beneficiaries, tax situation changes, and life events.'
        );
      } else if (driver.category === 'Cash Drag') {
        suggestedAgenda.push(
          'Analyze uninvested cash reserves and discuss high-yield deployment or dollar-cost averaging plan.'
        );
      } else if (driver.category === 'Data Freshness') {
        suggestedAgenda.push(
          'Investigate custodian sync delay with operations and refresh cost basis data.'
        );
      }
    }
  }

  // Extract from verified financial evidence
  if (Array.isArray(insight.evidence)) {
    for (const ev of insight.evidence) {
      evidenceFindings.push(
        `${ev.metricName}: ${ev.observedValue} (Threshold: ${ev.threshold})`
      );
    }
  }

  if (suggestedAgenda.length === 0) {
    suggestedAgenda.push('Confirm portfolio alignment and next scheduled annual check-in date.');
  }

  return {
    clientId: insight.clientId,
    clientName: insight.clientName,
    urgencyScore: insight.urgencyScore,
    urgencyLevel: insight.urgencyLevel,
    primaryCategory: insight.primaryCategory,
    executiveSummary: insight.summary,
    keyIssues,
    evidenceFindings,
    suggestedAgenda: Array.from(new Set(suggestedAgenda)), // deduplicate
    recommendedAction: insight.suggestedAction,
    preparedAt: new Date().toISOString(),
  };
}

/**
 * Format a review brief as ready-to-copy plaintext for advisor meeting memos or CRM logging.
 */
export function formatBriefAsText(
  brief: ReviewBrief,
  insight: AdvisorInsight,
  formattedAum: string,
  formattedCash: string
): string {
  const divider = '------------------------------------------------------------';
  return `ADVANTAIQ CLIENT REVIEW BRIEFING MEMO
${divider}
Client:              ${brief.clientName} (ID: ${brief.clientId})
Risk Profile:        ${insight.riskTolerance.toUpperCase()}
Total AUM:           ${formattedAum} (Orig: $${insight.totalAum.toLocaleString()} USD)
Cash Balance:        ${formattedCash} (Orig: $${insight.cashBalance.toLocaleString()} USD)
Priority Score:      ${brief.urgencyScore}/100 [${brief.urgencyLevel.toUpperCase()}]
Primary Concern:     ${brief.primaryCategory}
Generated On:        ${new Date(brief.preparedAt).toLocaleString()}
${divider}

1. EXECUTIVE SUMMARY & REASON FOR ATTENTION
   ${brief.executiveSummary}

2. ITEMISED SCORE DRIVERS
${brief.keyIssues.map((issue, idx) => `   ${idx + 1}. ${issue}`).join('\n')}

3. VERIFIED FINANCIAL EVIDENCE
${
  brief.evidenceFindings.length > 0
    ? brief.evidenceFindings.map((ev, idx) => `   • [${idx + 1}] ${ev}`).join('\n')
    : '   • No threshold breaches detected.'
}

4. SUGGESTED MEETING AGENDA & ADVISOR QUESTIONS
${brief.suggestedAgenda.map((q, idx) => `   ${idx + 1}. ${q}`).join('\n')}

5. RECOMMENDED NEXT ACTION
   ${brief.recommendedAction}

${divider}
NOTICE: Synthetic Demo Data • Fiduciary Human-in-the-Loop Required
AdvantaIQ Advisor Intelligence Platform
`;
}

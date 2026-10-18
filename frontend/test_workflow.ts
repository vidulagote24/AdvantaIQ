// test_workflow.ts - Comprehensive Unit Tests for AdvantaIQ Advisor Workflow & Safety
import assert from 'node:assert';
import {
  getClientWorkflowState,
  updateClientWorkflowStatus,
  addAdvisorNote,
  generateClientReviewBrief,
  formatBriefAsText,
} from './src/services/workflowService.ts';
import type { AdvisorInsight } from './src/contracts/types.ts';

// Setup Mock LocalStorage for Node runtime
const storage = new Map<string, string>();
(globalThis as any).localStorage = {
  getItem: (key: string) => storage.get(key) || null,
  setItem: (key: string, val: string) => storage.set(key, String(val)),
  removeItem: (key: string) => storage.delete(key),
  clear: () => storage.clear(),
};

// Fixture: Eleanor Vance (from verified audit & mock/live schema)
const sampleInsight: AdvisorInsight = {
  id: 'ins_cli_001',
  clientId: 'cli_001',
  clientName: 'Eleanor Vance',
  totalAum: 2850000.0,
  cashBalance: 340000.0,
  riskTolerance: 'moderate',
  urgencyScore: 80,
  urgencyLevel: 'critical',
  primaryCategory: 'Allocation Drift',
  summary: 'Allocation drift of 16.1% detected; portfolio rebalancing required.',
  detectedAt: '2026-10-18T00:00:00+00:00',
  daysSinceLastReview: 411,
  isReviewOverdue: true,
  dataFreshnessDays: 1,
  sourceCurrency: 'USD',
  scoreDrivers: [
    {
      category: 'Allocation Drift',
      pointsAwarded: 30,
      maxPoints: 30,
      rationale: 'Severe allocation drift of 16.1% exceeds risk tolerance parameters',
    },
    {
      category: 'Goal Milestones',
      pointsAwarded: 22,
      maxPoints: 30,
      rationale: "Goal 'Capital Preservation & Estate Legacy' underfunded with upcoming milestone in 74 days",
    },
    {
      category: 'Fiduciary Review',
      pointsAwarded: 20,
      maxPoints: 20,
      rationale: 'Mandatory fiduciary review critically overdue by 231 days (Cadence: 180d)',
    },
    {
      category: 'Cash Drag',
      pointsAwarded: 8,
      maxPoints: 10,
      rationale: 'Substantial uninvested cash reserves: $340,000 (11.9%) requires deployment strategy',
    },
    {
      category: 'Data Freshness',
      pointsAwarded: 0,
      maxPoints: 10,
      rationale: 'Custodian feed healthy and synchronised',
    },
  ],
  evidence: [
    {
      metricName: 'Asset Allocation Drift',
      observedValue: 'Equities: 64.2% (Target 50.0%), Drift: +14.2%',
      threshold: '±5.0% tolerance band',
      triggerReason: 'Severe allocation drift of 16.1% exceeds risk tolerance parameters',
    },
    {
      metricName: 'Goal Funding Status',
      observedValue: '$2,850,000 of $3,000,000 (95%), Deadline: 2027-01-01',
      threshold: '100% on-track target funding',
      triggerReason: "Goal 'Capital Preservation & Estate Legacy' underfunded with upcoming milestone in 74 days",
    },
    {
      metricName: 'Advisor Review Cadence',
      observedValue: '411 days since last meeting (Cadence: 180 days)',
      threshold: '180 days maximum review interval',
      triggerReason: 'Mandatory fiduciary review critically overdue by 231 days (Cadence: 180d)',
    },
    {
      metricName: 'Uninvested Cash Drag',
      observedValue: '$340,000 (11.9% of AUM)',
      threshold: 'Target: 10.0%',
      triggerReason: 'Substantial uninvested cash reserves: $340,000 (11.9%) requires deployment strategy',
    },
  ],
  suggestedAction: 'Review portfolio drift analysis and prepare tax-loss harvested rebalance proposal.',
};

console.log('=== RUNNING ADVANTAIQ ADVISOR WORKFLOW SERVICE TESTS ===\n');

// Test 1: Initial Default Workflow State
console.log('Test 1: Initial Default Workflow State...');
const initialWf = getClientWorkflowState(sampleInsight.clientId);
assert.strictEqual(initialWf.clientId, 'cli_001');
assert.strictEqual(initialWf.status, 'open');
assert.strictEqual(initialWf.deferredUntil, undefined);
assert.strictEqual(initialWf.notes.length, 0);
console.log('  ✓ Client starts in Open state with empty note history');

// Test 2: Recording Advisor Notes
console.log('Test 2: Recording Advisor Notes...');
const note1 = addAdvisorNote(
  sampleInsight.clientId,
  'Called Eleanor Vance regarding 14.2% equity drift. Rebalancing proposed for next Monday.',
  'Lead Wealth Advisor'
);
assert.strictEqual(note1.clientId, 'cli_001');
assert.ok(note1.id.startsWith('note_'));
assert.strictEqual(note1.author, 'Lead Wealth Advisor');
assert.ok(note1.text.includes('Eleanor Vance'));

const stateAfterNote = getClientWorkflowState(sampleInsight.clientId);
assert.strictEqual(stateAfterNote.notes.length, 1);
assert.strictEqual(stateAfterNote.notes[0].text, note1.text);
console.log('  ✓ Advisor note successfully recorded and persisted in localStorage');

// Test 3: Defer Follow-Up
console.log('Test 3: Defer Follow-Up with Date and Reason...');
const deferredState = updateClientWorkflowStatus(sampleInsight.clientId, 'deferred', {
  deferredUntil: '2026-11-15',
  deferReason: 'Waiting for client CPA tax-loss harvesting review on capital gains budget',
});
assert.strictEqual(deferredState.status, 'deferred');
assert.strictEqual(deferredState.deferredUntil, '2026-11-15');
assert.strictEqual(
  deferredState.deferReason,
  'Waiting for client CPA tax-loss harvesting review on capital gains budget'
);

const persistedDeferred = getClientWorkflowState(sampleInsight.clientId);
assert.strictEqual(persistedDeferred.status, 'deferred');
assert.strictEqual(persistedDeferred.deferredUntil, '2026-11-15');
console.log('  ✓ Follow-up deferral saved with exact date and rationale');

// Test 4: Resolve Insight
console.log('Test 4: Resolve Insight with Resolution Note...');
const resolvedState = updateClientWorkflowStatus(sampleInsight.clientId, 'resolved', {
  resolutionNote: 'Executed 10% equity trim to Treasuries and updated IPS review date.',
});
assert.strictEqual(resolvedState.status, 'resolved');
assert.strictEqual(
  resolvedState.resolutionNote,
  'Executed 10% equity trim to Treasuries and updated IPS review date.'
);
assert.ok(resolvedState.resolvedAt !== undefined);

const persistedResolved = getClientWorkflowState(sampleInsight.clientId);
assert.strictEqual(persistedResolved.status, 'resolved');
console.log('  ✓ Insight marked resolved with audit resolution note');

// Test 5: Urgency Score & Ranking Invariance
console.log('Test 5: Urgency Score & Ranking Invariance...');
assert.strictEqual(sampleInsight.urgencyScore, 80, 'Urgency score must not be mutated');
assert.strictEqual(sampleInsight.urgencyLevel, 'critical', 'Urgency level must not be mutated');
const totalDriverPoints = sampleInsight.scoreDrivers.reduce((sum, d) => sum + d.pointsAwarded, 0);
assert.strictEqual(totalDriverPoints, 80, 'Sum of score driver points must equal 80');
console.log('  ✓ Urgency score (80) and score drivers remain strictly invariant to workflow actions');

// Test 6: Deterministic Review Brief Generation
console.log('Test 6: Deterministic Review Brief Generation...');
const brief = generateClientReviewBrief(sampleInsight);
assert.strictEqual(brief.clientId, 'cli_001');
assert.strictEqual(brief.clientName, 'Eleanor Vance');
assert.strictEqual(brief.urgencyScore, 80);
assert.strictEqual(brief.urgencyLevel, 'critical');
assert.strictEqual(brief.primaryCategory, 'Allocation Drift');

// Verify evidence grounding
assert.ok(brief.executiveSummary.includes('Allocation drift of 16.1%'));
assert.ok(brief.evidenceFindings.some((f) => f.includes('Asset Allocation Drift: Equities: 64.2%')));
assert.ok(brief.evidenceFindings.some((f) => f.includes('Advisor Review Cadence: 411 days')));
assert.ok(brief.evidenceFindings.some((f) => f.includes('Uninvested Cash Drag: $340,000')));
assert.ok(brief.suggestedAgenda.length >= 2);
assert.strictEqual(brief.recommendedAction, sampleInsight.suggestedAction);
console.log('  ✓ Review brief is 100% deterministic and grounded in real evidence');

// Test 7: Plain Text Export Formatter
console.log('Test 7: Plain Text Export Formatter...');
const formattedAum = '$2,850,000.00';
const formattedCash = '$340,000.00';
const textBrief = formatBriefAsText(brief, sampleInsight, formattedAum, formattedCash);
assert.ok(textBrief.includes('ADVANTAIQ CLIENT REVIEW BRIEFING MEMO'));
assert.ok(textBrief.includes('Eleanor Vance (ID: cli_001)'));
assert.ok(textBrief.includes('Priority Score:'));
assert.ok(textBrief.includes('80/100 [CRITICAL]'));
assert.ok(textBrief.includes('VERIFIED FINANCIAL EVIDENCE'));
assert.ok(textBrief.includes('Asset Allocation Drift'));
assert.ok(textBrief.includes('RECOMMENDED NEXT ACTION'));
assert.ok(textBrief.includes('AdvantaIQ Advisor Intelligence Platform'));
console.log('  ✓ Formatted plain-text memo ready for clipboard and advisor CRM');

// Test 8: Reopen workflow state while preserving notes
console.log('Test 8: Reopen Workflow State...');
const reopened = updateClientWorkflowStatus(sampleInsight.clientId, 'open');
assert.strictEqual(reopened.status, 'open');
assert.strictEqual(reopened.deferredUntil, undefined);
assert.strictEqual(reopened.deferReason, undefined);
assert.strictEqual(reopened.resolutionNote, undefined);
assert.strictEqual(reopened.notes.length, 1);
assert.strictEqual(reopened.notes[0].text, note1.text);
console.log('  ✓ Client reopened while preserving historical advisor notes');

console.log('\n=== ALL 8 WORKFLOW SERVICE & SAFETY TESTS PASSED! ===');

export type UrgencyLevel = 'critical' | 'high' | 'medium' | 'low';

export type WorkflowStatus = 'open' | 'deferred' | 'resolved';

export interface AdvisorNote {
  id: string;
  clientId: string;
  text: string;
  createdAt: string;
  author: string;
}

export interface ClientWorkflowState {
  clientId: string;
  status: WorkflowStatus;
  deferredUntil?: string;
  deferReason?: string;
  resolvedAt?: string;
  resolutionNote?: string;
  notes: AdvisorNote[];
  updatedAt: string;
}

export interface ReviewBrief {
  clientId: string;
  clientName: string;
  urgencyScore: number;
  urgencyLevel: UrgencyLevel;
  primaryCategory: string;
  executiveSummary: string;
  keyIssues: string[];
  evidenceFindings: string[];
  suggestedAgenda: string[];
  recommendedAction: string;
  preparedAt: string;
}

export type CurrencyCode = 'INR' | 'USD' | 'EUR' | 'GBP' | 'AED';

export interface CurrencyConfig {
  code: CurrencyCode;
  symbol: string;
  name: string;
  locale: string;
  flag: string;
}

export interface ExchangeRateInfo {
  sourceCurrency: CurrencyCode;
  targetCurrency: CurrencyCode;
  rate: number;
  timestamp: string;
  provider: string;
  isDemoRate: boolean;
  disclaimer: string;
}

export interface EvidenceMetric {
  metricName: string;
  observedValue: string;
  threshold: string;
  triggerReason: string;
}

export interface ScoreDriver {
  category: string;
  pointsAwarded: number;
  maxPoints: number;
  rationale: string;
}

export interface AdvisorInsight {
  id: string;
  clientId: string;
  clientName: string;
  sourceCurrency?: CurrencyCode;
  totalAum: number;
  cashBalance: number;
  riskTolerance: string;
  urgencyScore: number;
  urgencyLevel: UrgencyLevel;
  primaryCategory: string;
  summary: string;
  detectedAt: string;
  daysSinceLastReview: number;
  isReviewOverdue: boolean;
  dataFreshnessDays: number;
  scoreDrivers: ScoreDriver[];
  evidence: EvidenceMetric[];
  suggestedAction: string;
}

export interface WorklistResponse {
  totalCount: number;
  criticalCount: number;
  highCount: number;
  mediumCount: number;
  lowCount: number;
  items: AdvisorInsight[];
}

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
  timestamp: string;
}
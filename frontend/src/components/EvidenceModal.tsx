import React, { useState, useMemo } from 'react';
import { AdvisorInsight, WorkflowStatus } from '../contracts/types';
import { UrgencyBadge } from './UrgencyBadge';
import {
  X,
  AlertCircle,
  ArrowRight,
  ShieldCheck,
  Clock,
  PieChart,
  FileText,
  CheckCircle2,
  MessageSquare,
  Copy,
  Check,
  PauseCircle,
  Info,
} from 'lucide-react';
import { useCurrency } from '../context/CurrencyContext';
import { useWorkflow } from '../context/WorkflowContext';
import {
  generateClientReviewBrief,
  formatBriefAsText,
} from '../services/workflowService';

interface EvidenceModalProps {
  insight: AdvisorInsight | null;
  onClose: () => void;
}

export const EvidenceModal: React.FC<EvidenceModalProps> = ({ insight, onClose }) => {
  if (!insight) return null;

  const { formatMoney } = useCurrency();
  const { getWorkflow, updateStatus, addNote, disclaimer } = useWorkflow();

  const [activeTab, setActiveTab] = useState<'evidence' | 'brief' | 'actions'>('evidence');
  const [newNoteText, setNewNoteText] = useState('');
  const [copiedBrief, setCopiedBrief] = useState(false);

  // Workflow state for this client
  const clientWorkflow = getWorkflow(insight.clientId);
  const [selectedStatus, setSelectedStatus] = useState<WorkflowStatus>(clientWorkflow.status);
  const [deferDate, setDeferDate] = useState<string>(
    clientWorkflow.deferredUntil ||
      new Date(Date.now() + 7 * 86400000).toISOString().split('T')[0]
  );
  const [deferReason, setDeferReason] = useState<string>(
    clientWorkflow.deferReason || 'Client requested follow-up meeting next week'
  );
  const [resolutionNote, setResolutionNote] = useState<string>(
    clientWorkflow.resolutionNote || 'Annual fiduciary review completed and logged'
  );
  const [statusSuccessMessage, setStatusSuccessMessage] = useState<string | null>(null);

  const aumMoney = formatMoney(insight.totalAum, insight.sourceCurrency || 'USD');
  const cashMoney = formatMoney(insight.cashBalance, insight.sourceCurrency || 'USD');

  // Generate review brief
  const reviewBrief = useMemo(
    () => generateClientReviewBrief(insight),
    [insight]
  );

  const briefPlainText = useMemo(
    () => formatBriefAsText(reviewBrief, insight, aumMoney.displayString, cashMoney.displayString),
    [reviewBrief, insight, aumMoney.displayString, cashMoney.displayString]
  );

  const handleCopyBrief = () => {
    navigator.clipboard.writeText(briefPlainText);
    setCopiedBrief(true);
    setTimeout(() => setCopiedBrief(false), 2200);
  };

  const handleSaveStatus = (e: React.FormEvent) => {
    e.preventDefault();
    updateStatus(insight.clientId, selectedStatus, {
      deferredUntil: selectedStatus === 'deferred' ? deferDate : undefined,
      deferReason: selectedStatus === 'deferred' ? deferReason : undefined,
      resolutionNote: selectedStatus === 'resolved' ? resolutionNote : undefined,
    });
    setStatusSuccessMessage(`Status updated to ${selectedStatus.toUpperCase()}`);
    setTimeout(() => setStatusSuccessMessage(null), 3000);
  };

  const handleAddNote = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNoteText.trim()) return;
    addNote(insight.clientId, newNoteText.trim(), 'Advisor (Demo)');
    setNewNoteText('');
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(2, 6, 23, 0.75)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 100,
        padding: '20px',
      }}
      onClick={onClose}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '920px',
          maxHeight: '92vh',
          overflowY: 'auto',
          backgroundColor: '#0f172a',
          borderColor: 'var(--border-highlight)',
          borderRadius: '16px',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.6)',
          padding: '28px',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'space-between',
            borderBottom: '1px solid var(--border-subtle)',
            paddingBottom: '18px',
            marginBottom: '18px',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
              <h2 style={{ fontSize: '1.45rem', fontWeight: 800, color: '#ffffff' }}>
                {insight.clientName}
              </h2>
              <UrgencyBadge level={insight.urgencyLevel} score={insight.urgencyScore} />
              <span
                style={{
                  fontSize: '0.72rem',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  background: 'rgba(148, 163, 184, 0.1)',
                  color: 'var(--text-muted)',
                  textTransform: 'capitalize',
                  fontWeight: 600,
                }}
              >
                {insight.riskTolerance} Risk
              </span>

              {/* Workflow Status Pill */}
              <span
                style={{
                  fontSize: '0.72rem',
                  padding: '3px 9px',
                  borderRadius: '12px',
                  fontWeight: 700,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '5px',
                  background:
                    clientWorkflow.status === 'resolved'
                      ? 'rgba(34, 197, 94, 0.15)'
                      : clientWorkflow.status === 'deferred'
                      ? 'rgba(245, 158, 11, 0.15)'
                      : 'rgba(56, 189, 248, 0.15)',
                  color:
                    clientWorkflow.status === 'resolved'
                      ? '#4ade80'
                      : clientWorkflow.status === 'deferred'
                      ? '#fbbf24'
                      : '#38bdf8',
                  border:
                    clientWorkflow.status === 'resolved'
                      ? '1px solid rgba(34, 197, 94, 0.3)'
                      : clientWorkflow.status === 'deferred'
                      ? '1px solid rgba(245, 158, 11, 0.3)'
                      : '1px solid rgba(56, 189, 248, 0.3)',
                }}
              >
                {clientWorkflow.status === 'resolved' && <CheckCircle2 size={12} />}
                {clientWorkflow.status === 'deferred' && <PauseCircle size={12} />}
                {clientWorkflow.status === 'open' && <AlertCircle size={12} />}
                <span>
                  {clientWorkflow.status === 'deferred'
                    ? `Deferred until ${clientWorkflow.deferredUntil || 'scheduled date'}`
                    : clientWorkflow.status.toUpperCase()}
                </span>
              </span>
            </div>

            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '8px' }}>
              Client ID: <span className="mono" style={{ color: '#cbd5e1' }}>{insight.clientId}</span> &bull; AUM:{' '}
              <span className="mono" style={{ color: '#4ade80', fontWeight: 600 }}>
                {aumMoney.displayString}
              </span>{' '}
              {aumMoney.isConverted && (
                <span style={{ fontSize: '0.74rem', color: 'var(--text-dim)' }}>
                  ({aumMoney.originalString} USD)
                </span>
              )}{' '}
              &bull; Cash Drag:{' '}
              <span className="mono" style={{ color: '#fcd34d', fontWeight: 600 }}>
                {cashMoney.displayString}
              </span>
              {cashMoney.isConverted && (
                <span style={{ fontSize: '0.74rem', color: 'var(--text-dim)', marginLeft: '4px' }}>
                  ({cashMoney.originalString} USD)
                </span>
              )}{' '}
              &bull; Review:{' '}
              <span style={{ color: insight.isReviewOverdue ? '#fca5a5' : '#cbd5e1' }}>
                {insight.daysSinceLastReview}d ago {insight.isReviewOverdue && '(Overdue)'}
              </span>{' '}
              &bull; Custodian Sync:{' '}
              <span style={{ color: insight.dataFreshnessDays > 5 ? '#fcd34d' : '#94a3b8' }}>
                {insight.dataFreshnessDays}d ago
              </span>
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '6px',
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Workspace Navigation Tabs */}
        <div
          style={{
            display: 'flex',
            gap: '8px',
            borderBottom: '1px solid var(--border-subtle)',
            marginBottom: '20px',
            paddingBottom: '2px',
          }}
        >
          <button
            onClick={() => setActiveTab('evidence')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              borderRadius: '8px 8px 0 0',
              border: 'none',
              borderBottom: activeTab === 'evidence' ? '2px solid #38bdf8' : '2px solid transparent',
              background: activeTab === 'evidence' ? 'rgba(56, 189, 248, 0.1)' : 'transparent',
              color: activeTab === 'evidence' ? '#ffffff' : 'var(--text-muted)',
              fontWeight: activeTab === 'evidence' ? 700 : 500,
              fontSize: '0.84rem',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            <PieChart size={15} color={activeTab === 'evidence' ? '#38bdf8' : '#94a3b8'} />
            <span>Evidence & Diagnosis</span>
          </button>

          <button
            onClick={() => setActiveTab('brief')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              borderRadius: '8px 8px 0 0',
              border: 'none',
              borderBottom: activeTab === 'brief' ? '2px solid #38bdf8' : '2px solid transparent',
              background: activeTab === 'brief' ? 'rgba(56, 189, 248, 0.1)' : 'transparent',
              color: activeTab === 'brief' ? '#ffffff' : 'var(--text-muted)',
              fontWeight: activeTab === 'brief' ? 700 : 500,
              fontSize: '0.84rem',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            <FileText size={15} color={activeTab === 'brief' ? '#38bdf8' : '#94a3b8'} />
            <span>Prepare Review Brief</span>
          </button>

          <button
            onClick={() => setActiveTab('actions')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              borderRadius: '8px 8px 0 0',
              border: 'none',
              borderBottom: activeTab === 'actions' ? '2px solid #38bdf8' : '2px solid transparent',
              background: activeTab === 'actions' ? 'rgba(56, 189, 248, 0.1)' : 'transparent',
              color: activeTab === 'actions' ? '#ffffff' : 'var(--text-muted)',
              fontWeight: activeTab === 'actions' ? 700 : 500,
              fontSize: '0.84rem',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            <CheckCircle2 size={15} color={activeTab === 'actions' ? '#4ade80' : '#94a3b8'} />
            <span>Advisor Actions & Notes</span>
            {clientWorkflow.notes.length > 0 && (
              <span
                style={{
                  fontSize: '0.7rem',
                  padding: '1px 6px',
                  borderRadius: '10px',
                  backgroundColor: 'rgba(255, 255, 255, 0.15)',
                  color: '#ffffff',
                }}
              >
                {clientWorkflow.notes.length}
              </span>
            )}
          </button>
        </div>

        {/* TAB 1: Evidence & Diagnosis */}
        {activeTab === 'evidence' && (
          <div>
            {/* Executive Summary Banner */}
            <div
              style={{
                backgroundColor: 'rgba(56, 189, 248, 0.08)',
                border: '1px solid rgba(56, 189, 248, 0.25)',
                borderRadius: '10px',
                padding: '16px',
                marginBottom: '24px',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px',
              }}
            >
              <div style={{ marginTop: '2px' }}>
                <AlertCircle size={18} color="#38bdf8" />
              </div>
              <div>
                <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase' }}>
                  Why This Client Needs Attention: {insight.primaryCategory}
                </div>
                <div style={{ fontSize: '0.92rem', color: '#f1f5f9', marginTop: '2px', fontWeight: 500 }}>
                  {insight.summary}
                </div>
              </div>
            </div>

            {/* Section 1: Itemized Scoring Drivers */}
            <div style={{ marginBottom: '28px' }}>
              <h3
                style={{
                  fontSize: '0.9rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  color: 'var(--text-muted)',
                  marginBottom: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                <PieChart size={15} color="#38bdf8" />
                Deterministic Score Drivers (Urgency: {insight.urgencyScore}/100)
              </h3>
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  backgroundColor: 'var(--bg-card)',
                  borderRadius: '10px',
                  padding: '12px 16px',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                {insight.scoreDrivers.map((driver, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '8px 0',
                      borderBottom:
                        idx < insight.scoreDrivers.length - 1 ? '1px solid var(--border-subtle)' : 'none',
                      fontSize: '0.84rem',
                    }}
                  >
                    <div style={{ flex: 1, paddingRight: '16px' }}>
                      <span style={{ fontWeight: 600, color: '#e2e8f0' }}>{driver.category}</span>
                      <p style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                        {driver.rationale}
                      </p>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div
                        style={{
                          width: '70px',
                          height: '6px',
                          backgroundColor: 'rgba(255, 255, 255, 0.08)',
                          borderRadius: '3px',
                          overflow: 'hidden',
                        }}
                      >
                        <div
                          style={{
                            width: `${(driver.pointsAwarded / driver.maxPoints) * 100}%`,
                            height: '100%',
                            backgroundColor:
                              driver.pointsAwarded > 15
                                ? '#f87171'
                                : driver.pointsAwarded > 0
                                ? '#fbbf24'
                                : '#64748b',
                          }}
                        />
                      </div>
                      <span
                        className="mono"
                        style={{
                          fontWeight: 700,
                          minWidth: '48px',
                          textAlign: 'right',
                          color: driver.pointsAwarded > 0 ? '#ffffff' : 'var(--text-dim)',
                        }}
                      >
                        +{driver.pointsAwarded}
                        <span style={{ color: 'var(--text-dim)', fontSize: '0.72rem' }}>
                          /{driver.maxPoints}
                        </span>
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Section 2: Concrete Evidence Metrics */}
            <div style={{ marginBottom: '28px' }}>
              <h3
                style={{
                  fontSize: '0.9rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  color: 'var(--text-muted)',
                  marginBottom: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                <ShieldCheck size={15} color="#4ade80" />
                Verified Financial Evidence
              </h3>
              {insight.evidence.length === 0 ? (
                <div
                  style={{
                    padding: '16px',
                    textAlign: 'center',
                    backgroundColor: 'var(--bg-card)',
                    borderRadius: '8px',
                    color: 'var(--text-dim)',
                    fontSize: '0.85rem',
                  }}
                >
                  No active threshold breaches or drift alerts detected for this portfolio.
                </div>
              ) : (
                <div
                  style={{
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '10px',
                    overflow: 'hidden',
                  }}
                >
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                    <thead>
                      <tr style={{ background: 'var(--bg-card)', borderBottom: '1px solid var(--border-subtle)' }}>
                        <th style={{ textAlign: 'left', padding: '10px 14px', color: 'var(--text-muted)' }}>
                          Metric
                        </th>
                        <th style={{ textAlign: 'left', padding: '10px 14px', color: 'var(--text-muted)' }}>
                          Observed Value
                        </th>
                        <th style={{ textAlign: 'left', padding: '10px 14px', color: 'var(--text-muted)' }}>
                          Policy Threshold
                        </th>
                        <th style={{ textAlign: 'left', padding: '10px 14px', color: 'var(--text-muted)' }}>
                          Trigger Reason
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {insight.evidence.map((ev, i) => (
                        <tr
                          key={i}
                          style={{
                            borderBottom:
                              i < insight.evidence.length - 1 ? '1px solid var(--border-subtle)' : 'none',
                            backgroundColor: i % 2 === 0 ? 'transparent' : 'rgba(255, 255, 255, 0.015)',
                          }}
                        >
                          <td style={{ padding: '10px 14px', fontWeight: 600, color: '#f8fafc' }}>
                            {ev.metricName}
                          </td>
                          <td style={{ padding: '10px 14px', color: '#fcd34d', fontWeight: 500 }}>
                            {ev.observedValue}
                          </td>
                          <td style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>
                            {ev.threshold}
                          </td>
                          <td style={{ padding: '10px 14px', color: '#cbd5e1' }}>
                            {ev.triggerReason}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Section 3: Recommended Action */}
            <div
              style={{
                backgroundColor: 'rgba(34, 197, 94, 0.08)',
                border: '1px solid rgba(34, 197, 94, 0.25)',
                borderRadius: '12px',
                padding: '18px',
                marginBottom: '20px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <Clock size={16} color="#4ade80" />
                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#4ade80', textTransform: 'uppercase' }}>
                  Act at the Right Time: Recommended Next Step
                </span>
              </div>
              <p style={{ fontSize: '0.92rem', color: '#f8fafc', fontWeight: 500, lineHeight: 1.4 }}>
                {insight.suggestedAction}
              </p>
              <div
                style={{
                  fontSize: '0.74rem',
                  color: 'var(--text-muted)',
                  marginTop: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <ShieldCheck size={13} color="#94a3b8" />
                <span>Human-in-the-Loop review required. No automated trades or client emails are dispatched without advisor sign-off.</span>
              </div>
            </div>

            {/* Navigation buttons to other tabs */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button
                onClick={() => setActiveTab('brief')}
                className="btn-outline"
                style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <FileText size={14} />
                <span>Prepare Review Brief</span>
              </button>
              <button
                onClick={() => setActiveTab('actions')}
                className="btn-primary"
                style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <span>Take Action / Record Notes</span>
                <ArrowRight size={14} />
              </button>
            </div>
          </div>
        )}

        {/* TAB 2: Prepare Review Brief */}
        {activeTab === 'brief' && (
          <div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '16px',
                flexWrap: 'wrap',
                gap: '12px',
              }}
            >
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff' }}>
                  Client Review Briefing Memo
                </h3>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                  Deterministically generated from client portfolio metrics, goals, and fiduciary review schedule.
                </p>
              </div>
              <button
                onClick={handleCopyBrief}
                className="btn-primary"
                style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem' }}
              >
                {copiedBrief ? <Check size={14} color="#ffffff" /> : <Copy size={14} />}
                <span>{copiedBrief ? 'Copied to Clipboard!' : 'Copy Briefing Memo'}</span>
              </button>
            </div>

            {/* Key Findings & Agenda Preview Cards */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
                gap: '14px',
                marginBottom: '20px',
              }}
            >
              {/* Evidence-grounded issues card */}
              <div
                style={{
                  backgroundColor: 'var(--bg-card)',
                  borderRadius: '10px',
                  padding: '16px',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#f87171', textTransform: 'uppercase', marginBottom: '8px' }}>
                  Primary Risk Signals
                </div>
                <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '0.82rem', color: '#cbd5e1', lineHeight: 1.5 }}>
                  {reviewBrief.keyIssues.map((issue, idx) => (
                    <li key={idx} style={{ marginBottom: '6px' }}>{issue}</li>
                  ))}
                </ul>
              </div>

              {/* Discussion agenda card */}
              <div
                style={{
                  backgroundColor: 'var(--bg-card)',
                  borderRadius: '10px',
                  padding: '16px',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#4ade80', textTransform: 'uppercase', marginBottom: '8px' }}>
                  Suggested Advisor Discussion Agenda
                </div>
                <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '0.82rem', color: '#cbd5e1', lineHeight: 1.5 }}>
                  {reviewBrief.suggestedAgenda.map((item, idx) => (
                    <li key={idx} style={{ marginBottom: '6px' }}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Ready-to-copy plaintext preview box */}
            <div style={{ marginBottom: '20px' }}>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginBottom: '6px', fontWeight: 600 }}>
                Plaintext Export (Formatted for CRM Notes or Advisor Pre-Meeting Memo)
              </div>
              <pre
                className="mono"
                style={{
                  background: '#090d16',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '10px',
                  padding: '16px',
                  fontSize: '0.75rem',
                  color: '#94a3b8',
                  lineHeight: 1.45,
                  overflowX: 'auto',
                  maxHeight: '260px',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {briefPlainText}
              </pre>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button onClick={() => setActiveTab('actions')} className="btn-primary">
                Proceed to Advisor Actions
              </button>
            </div>
          </div>
        )}

        {/* TAB 3: Advisor Actions & Notes */}
        {activeTab === 'actions' && (
          <div>
            {/* Status Change Success Notification */}
            {statusSuccessMessage && (
              <div
                style={{
                  padding: '10px 16px',
                  borderRadius: '8px',
                  background: 'rgba(34, 197, 94, 0.15)',
                  border: '1px solid rgba(34, 197, 94, 0.35)',
                  color: '#86efac',
                  fontSize: '0.82rem',
                  marginBottom: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                <Check size={16} />
                <span>{statusSuccessMessage}</span>
              </div>
            )}

            {/* Section 1: Workflow Status & Deferral Management */}
            <div
              style={{
                backgroundColor: 'var(--bg-card)',
                borderRadius: '12px',
                padding: '20px',
                border: '1px solid var(--border-subtle)',
                marginBottom: '24px',
              }}
            >
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#ffffff', marginBottom: '14px' }}>
                Advisor Workflow Status
              </h3>

              <form onSubmit={handleSaveStatus}>
                {/* Status Toggle Buttons */}
                <div style={{ display: 'flex', gap: '10px', marginBottom: '16px', flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    onClick={() => setSelectedStatus('open')}
                    style={{
                      flex: 1,
                      minWidth: '120px',
                      padding: '10px 16px',
                      borderRadius: '8px',
                      border: selectedStatus === 'open' ? '1px solid #38bdf8' : '1px solid var(--border-subtle)',
                      background: selectedStatus === 'open' ? 'rgba(56, 189, 248, 0.15)' : 'rgba(255, 255, 255, 0.02)',
                      color: selectedStatus === 'open' ? '#38bdf8' : 'var(--text-muted)',
                      fontWeight: 700,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '6px',
                      fontSize: '0.82rem',
                    }}
                  >
                    <AlertCircle size={14} />
                    <span>Open (Active)</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setSelectedStatus('deferred')}
                    style={{
                      flex: 1,
                      minWidth: '120px',
                      padding: '10px 16px',
                      borderRadius: '8px',
                      border: selectedStatus === 'deferred' ? '1px solid #fbbf24' : '1px solid var(--border-subtle)',
                      background: selectedStatus === 'deferred' ? 'rgba(245, 158, 11, 0.15)' : 'rgba(255, 255, 255, 0.02)',
                      color: selectedStatus === 'deferred' ? '#fbbf24' : 'var(--text-muted)',
                      fontWeight: 700,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '6px',
                      fontSize: '0.82rem',
                    }}
                  >
                    <PauseCircle size={14} />
                    <span>Defer Follow-Up</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setSelectedStatus('resolved')}
                    style={{
                      flex: 1,
                      minWidth: '120px',
                      padding: '10px 16px',
                      borderRadius: '8px',
                      border: selectedStatus === 'resolved' ? '1px solid #4ade80' : '1px solid var(--border-subtle)',
                      background: selectedStatus === 'resolved' ? 'rgba(34, 197, 94, 0.15)' : 'rgba(255, 255, 255, 0.02)',
                      color: selectedStatus === 'resolved' ? '#4ade80' : 'var(--text-muted)',
                      fontWeight: 700,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '6px',
                      fontSize: '0.82rem',
                    }}
                  >
                    <CheckCircle2 size={14} />
                    <span>Mark Resolved</span>
                  </button>
                </div>

                {/* Conditional Fields based on status */}
                {selectedStatus === 'deferred' && (
                  <div
                    style={{
                      padding: '14px',
                      borderRadius: '8px',
                      background: 'rgba(245, 158, 11, 0.06)',
                      border: '1px solid rgba(245, 158, 11, 0.25)',
                      marginBottom: '16px',
                    }}
                  >
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
                      <div>
                        <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#fcd34d', marginBottom: '4px' }}>
                          Follow-Up Date *
                        </label>
                        <input
                          type="date"
                          value={deferDate}
                          onChange={(e) => setDeferDate(e.target.value)}
                          required
                          style={{
                            width: '100%',
                            background: '#090d16',
                            border: '1px solid var(--border-subtle)',
                            borderRadius: '6px',
                            padding: '6px 10px',
                            color: '#ffffff',
                            fontSize: '0.8rem',
                          }}
                        />
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#fcd34d', marginBottom: '4px' }}>
                          Deferral Reason *
                        </label>
                        <select
                          value={deferReason}
                          onChange={(e) => setDeferReason(e.target.value)}
                          style={{
                            width: '100%',
                            background: '#090d16',
                            border: '1px solid var(--border-subtle)',
                            borderRadius: '6px',
                            padding: '6px 10px',
                            color: '#ffffff',
                            fontSize: '0.8rem',
                          }}
                        >
                          <option value="Client requested follow-up meeting next week">Client requested follow-up meeting next week</option>
                          <option value="Client currently traveling / out of office">Client currently traveling / out of office</option>
                          <option value="Waiting for quarterly custodian statement">Waiting for quarterly custodian statement</option>
                          <option value="Rebalance proposal drafted; pending client schedule">Rebalance proposal drafted; pending client schedule</option>
                          <option value="Tax considerations under CPA review">Tax considerations under CPA review</option>
                        </select>
                      </div>
                    </div>
                  </div>
                )}

                {selectedStatus === 'resolved' && (
                  <div
                    style={{
                      padding: '14px',
                      borderRadius: '8px',
                      background: 'rgba(34, 197, 94, 0.06)',
                      border: '1px solid rgba(34, 197, 94, 0.25)',
                      marginBottom: '16px',
                    }}
                  >
                    <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#86efac', marginBottom: '4px' }}>
                      Resolution Verification Note *
                    </label>
                    <input
                      type="text"
                      value={resolutionNote}
                      onChange={(e) => setResolutionNote(e.target.value)}
                      required
                      placeholder="e.g. Annual fiduciary review completed and logged in CRM"
                      style={{
                        width: '100%',
                        background: '#090d16',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: '6px',
                        padding: '8px 12px',
                        color: '#ffffff',
                        fontSize: '0.8rem',
                      }}
                    />
                  </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                    Priority score ({insight.urgencyScore}) and original evidence are preserved regardless of status.
                  </span>
                  <button type="submit" className="btn-primary" style={{ padding: '6px 16px', fontSize: '0.8rem' }}>
                    Save Workflow Status
                  </button>
                </div>
              </form>
            </div>

            {/* Section 2: Advisor Notes Log */}
            <div
              style={{
                backgroundColor: 'var(--bg-card)',
                borderRadius: '12px',
                padding: '20px',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <MessageSquare size={16} color="#38bdf8" />
                  <span>Advisor Notes Log</span>
                </h3>
                <span
                  style={{
                    fontSize: '0.7rem',
                    color: 'var(--text-dim)',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                  title={disclaimer}
                >
                  <Info size={11} />
                  <span>Session Local Storage (Demo)</span>
                </span>
              </div>

              {/* Add Note Form */}
              <form onSubmit={handleAddNote} style={{ marginBottom: '20px' }}>
                <textarea
                  value={newNoteText}
                  onChange={(e) => setNewNoteText(e.target.value)}
                  placeholder="Record an internal advisor observation, meeting summary, or action item for this client..."
                  rows={3}
                  style={{
                    width: '100%',
                    background: '#090d16',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '8px',
                    padding: '10px 12px',
                    color: '#ffffff',
                    fontSize: '0.82rem',
                    outline: 'none',
                    resize: 'vertical',
                    marginBottom: '8px',
                  }}
                />
                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <button
                    type="submit"
                    disabled={!newNoteText.trim()}
                    className="btn-primary"
                    style={{
                      padding: '6px 14px',
                      fontSize: '0.78rem',
                      opacity: newNoteText.trim() ? 1 : 0.5,
                      cursor: newNoteText.trim() ? 'pointer' : 'not-allowed',
                    }}
                  >
                    Record Note
                  </button>
                </div>
              </form>

              {/* Historical Notes List */}
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '10px' }}>
                  Recorded Notes ({clientWorkflow.notes.length})
                </div>

                {clientWorkflow.notes.length === 0 ? (
                  <div
                    style={{
                      padding: '16px',
                      textAlign: 'center',
                      background: 'rgba(255, 255, 255, 0.02)',
                      borderRadius: '8px',
                      color: 'var(--text-dim)',
                      fontSize: '0.78rem',
                    }}
                  >
                    No notes recorded yet for {insight.clientName}. Use the form above to add an advisor note.
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {clientWorkflow.notes.map((note) => (
                      <div
                        key={note.id}
                        style={{
                          padding: '12px',
                          borderRadius: '8px',
                          background: 'rgba(255, 255, 255, 0.03)',
                          border: '1px solid var(--border-subtle)',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '4px' }}>
                          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8' }}>
                            {note.author}
                          </span>
                          <span className="mono" style={{ fontSize: '0.68rem', color: 'var(--text-dim)' }}>
                            {new Date(note.createdAt).toLocaleString()}
                          </span>
                        </div>
                        <p style={{ margin: 0, fontSize: '0.82rem', color: '#e2e8f0', lineHeight: 1.45, whiteSpace: 'pre-wrap' }}>
                          {note.text}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
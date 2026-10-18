import React, { useState, useMemo } from 'react';
import { AdvisorInsight, WorkflowStatus } from '../contracts/types';
import { UrgencyBadge } from './UrgencyBadge';
import { Search, ArrowUpDown, Eye, Calendar, Database, CheckCircle2, PauseCircle, Clock, Filter, FileText } from 'lucide-react';
import { useCurrency } from '../context/CurrencyContext';
import { useWorkflow } from '../context/WorkflowContext';

interface WorklistTableProps {
  items: AdvisorInsight[];
  onSelectInsight: (insight: AdvisorInsight) => void;
  selectedFilter: string;
  onFilterChange: (filter: string) => void;
  counts: {
    total: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
}

export const WorklistTable: React.FC<WorklistTableProps> = ({
  items,
  onSelectInsight,
  selectedFilter,
  onFilterChange,
  counts,
}) => {
  const { formatMoney, displayCurrency } = useCurrency();
  const { getWorkflow, getCounts } = useWorkflow();
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'score' | 'aum' | 'overdue'>('score');
  const [workflowFilter, setWorkflowFilter] = useState<'all' | WorkflowStatus>('all');

  const wfCounts = useMemo(() => {
    return getCounts(items.map((i) => i.clientId));
  }, [items, getCounts]);

  const filteredAndSorted = useMemo(() => {
    return items
      .filter((item) => {
        const matchesSearch =
          item.clientName.toLowerCase().includes(searchQuery.toLowerCase()) ||
          item.clientId.toLowerCase().includes(searchQuery.toLowerCase()) ||
          item.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
          item.primaryCategory.toLowerCase().includes(searchQuery.toLowerCase());

        if (!matchesSearch) return false;

        if (workflowFilter !== 'all') {
          const wf = getWorkflow(item.clientId);
          if (wf.status !== workflowFilter) return false;
        }

        return true;
      })
      .sort((a, b) => {
        if (sortBy === 'score') return b.urgencyScore - a.urgencyScore;
        if (sortBy === 'aum') return b.totalAum - a.totalAum;
        if (sortBy === 'overdue') return b.daysSinceLastReview - a.daysSinceLastReview;
        return 0;
      });
  }, [items, searchQuery, sortBy, workflowFilter, getWorkflow]);

  const filterTabs = [
    { id: 'all', label: 'All Cases', count: counts.total },
    { id: 'critical', label: 'Critical', count: counts.critical, color: '#f87171' },
    { id: 'high', label: 'High', count: counts.high, color: '#fbbf24' },
    { id: 'medium', label: 'Medium', count: counts.medium, color: '#38bdf8' },
    { id: 'low', label: 'Low', count: counts.low, color: '#4ade80' },
  ];

  return (
    <div className="glass-panel" style={{ overflow: 'hidden' }}>
      {/* Top Filter & Search Toolbar */}
      <div
        style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '14px',
          background: 'rgba(15, 23, 42, 0.6)',
        }}
      >
        {/* Filter Tabs */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
          {filterTabs.map((tab) => {
            const active = selectedFilter.toLowerCase() === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onFilterChange(tab.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 12px',
                  borderRadius: '6px',
                  border: active ? '1px solid var(--border-highlight)' : '1px solid transparent',
                  background: active ? 'var(--bg-card)' : 'transparent',
                  color: active ? '#ffffff' : 'var(--text-muted)',
                  cursor: 'pointer',
                  fontSize: '0.8rem',
                  fontWeight: active ? 700 : 500,
                  transition: 'all 0.15s ease',
                }}
              >
                <span>{tab.label}</span>
                <span
                  className="mono"
                  style={{
                    fontSize: '0.72rem',
                    padding: '1px 6px',
                    borderRadius: '10px',
                    background: active ? 'rgba(255, 255, 255, 0.1)' : 'rgba(255, 255, 255, 0.05)',
                    color: tab.color || '#94a3b8',
                  }}
                >
                  {tab.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Workflow, Search & Sort Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {/* Workflow Status Filter */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.78rem',
            }}
          >
            <Filter size={14} color="var(--text-dim)" />
            <select
              id="workflow-status-filter"
              aria-label="Filter by Workflow Status"
              value={workflowFilter}
              onChange={(e) => setWorkflowFilter(e.target.value as any)}
              style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '5px 8px',
                color:
                  workflowFilter === 'all'
                    ? '#ffffff'
                    : workflowFilter === 'open'
                    ? '#38bdf8'
                    : workflowFilter === 'deferred'
                    ? '#fbbf24'
                    : '#34d399',
                fontSize: '0.78rem',
                outline: 'none',
                cursor: 'pointer',
                fontWeight: 600,
              }}
            >
              <option value="all">Workflow: All Statuses ({wfCounts.total})</option>
              <option value="open">Workflow: Open Action ({wfCounts.open})</option>
              <option value="deferred">Workflow: Deferred ({wfCounts.deferred})</option>
              <option value="resolved">Workflow: Resolved ({wfCounts.resolved})</option>
            </select>
          </div>

          {/* Search box */}
          <div
            style={{
              position: 'relative',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <Search
              size={14}
              color="var(--text-dim)"
              style={{ position: 'absolute', left: '10px' }}
            />
            <input
              type="text"
              placeholder="Filter by client, ID, issue..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '6px 12px 6px 30px',
                color: '#ffffff',
                fontSize: '0.8rem',
                width: '210px',
                outline: 'none',
              }}
            />
          </div>

          {/* Sort Selector */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.78rem',
              color: 'var(--text-muted)',
            }}
          >
            <ArrowUpDown size={14} />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '5px 8px',
                color: '#ffffff',
                fontSize: '0.78rem',
                outline: 'none',
                cursor: 'pointer',
              }}
            >
              <option value="score">Sort: Urgency Score</option>
              <option value="aum">Sort: Total AUM</option>
              <option value="overdue">Sort: Review Days</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Table */}
      {filteredAndSorted.length === 0 ? (
        <div
          style={{
            padding: '48px 24px',
            textAlign: 'center',
            color: 'var(--text-muted)',
          }}
        >
          <p style={{ fontSize: '1rem', fontWeight: 600, color: '#e2e8f0' }}>No matching clients found</p>
          <p style={{ fontSize: '0.82rem', marginTop: '4px' }}>
            Try adjusting your search criteria or urgency filter.
          </p>
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table
            style={{
              width: '100%',
              borderCollapse: 'collapse',
              textAlign: 'left',
              fontSize: '0.84rem',
            }}
          >
            <thead>
              <tr
                style={{
                  borderBottom: '1px solid var(--border-subtle)',
                  background: 'var(--bg-surface)',
                  fontSize: '0.75rem',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  color: 'var(--text-dim)',
                }}
              >
                <th style={{ padding: '12px 18px' }}>Client Profile</th>
                <th style={{ padding: '12px 18px' }}>Urgency & Score</th>
                <th style={{ padding: '12px 18px' }}>Key Issue & Drivers</th>
                <th style={{ padding: '12px 18px' }}>
                  Portfolio AUM / Cash <span className="mono" style={{ fontSize: '0.7rem', color: '#38bdf8' }}>({displayCurrency})</span>
                </th>
                <th style={{ padding: '12px 18px' }}>Workflow & Cadence</th>
                <th style={{ padding: '12px 18px', textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredAndSorted.map((item, idx) => (
                <tr
                  key={item.id}
                  onClick={() => onSelectInsight(item)}
                  style={{
                    borderBottom:
                      idx < filteredAndSorted.length - 1 ? '1px solid var(--border-subtle)' : 'none',
                    backgroundColor:
                      item.urgencyLevel === 'critical'
                        ? 'rgba(239, 68, 68, 0.03)'
                        : idx % 2 === 0
                        ? 'transparent'
                        : 'rgba(255, 255, 255, 0.01)',
                    cursor: 'pointer',
                    transition: 'background-color 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor =
                      item.urgencyLevel === 'critical'
                        ? 'rgba(239, 68, 68, 0.03)'
                        : idx % 2 === 0
                        ? 'transparent'
                        : 'rgba(255, 255, 255, 0.01)';
                  }}
                >
                  {/* Client Profile */}
                  <td style={{ padding: '14px 18px' }}>
                    <div style={{ fontWeight: 700, color: '#ffffff', fontSize: '0.92rem' }}>
                      {item.clientName}
                    </div>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        fontSize: '0.72rem',
                        color: 'var(--text-muted)',
                        marginTop: '3px',
                      }}
                    >
                      <span className="mono">{item.clientId}</span>
                      <span>&bull;</span>
                      <span style={{ textTransform: 'capitalize' }}>{item.riskTolerance}</span>
                    </div>
                  </td>

                  {/* Urgency & Score */}
                  <td style={{ padding: '14px 18px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <UrgencyBadge level={item.urgencyLevel} score={item.urgencyScore} />
                    </div>
                    {/* Visual Progress Bar */}
                    <div
                      style={{
                        width: '110px',
                        height: '4px',
                        backgroundColor: 'rgba(255, 255, 255, 0.08)',
                        borderRadius: '2px',
                        marginTop: '6px',
                        overflow: 'hidden',
                      }}
                    >
                      <div
                        style={{
                          width: `${item.urgencyScore}%`,
                          height: '100%',
                          backgroundColor:
                            item.urgencyLevel === 'critical'
                              ? '#ef4444'
                              : item.urgencyLevel === 'high'
                              ? '#f59e0b'
                              : item.urgencyLevel === 'medium'
                              ? '#38bdf8'
                              : '#22c55e',
                        }}
                      />
                    </div>
                  </td>

                  {/* Issue Summary & Drivers */}
                  <td style={{ padding: '14px 18px', maxWidth: '360px' }}>
                    <div style={{ fontWeight: 600, color: '#f1f5f9', fontSize: '0.84rem' }}>
                      {item.summary}
                    </div>
                    <div
                      style={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: '6px',
                        marginTop: '6px',
                      }}
                    >
                      {item.scoreDrivers
                        .filter((d) => d.pointsAwarded > 0)
                        .slice(0, 2)
                        .map((d, i) => (
                          <span
                            key={i}
                            style={{
                              fontSize: '0.7rem',
                              padding: '2px 6px',
                              borderRadius: '4px',
                              background: 'rgba(255, 255, 255, 0.06)',
                              color: 'var(--text-muted)',
                              border: '1px solid var(--border-subtle)',
                            }}
                          >
                            {d.category} (+{d.pointsAwarded})
                          </span>
                        ))}
                    </div>
                  </td>

                  {/* Portfolio AUM & Cash */}
                  <td style={{ padding: '14px 18px' }}>
                    {(() => {
                      const aumMoney = formatMoney(item.totalAum, item.sourceCurrency || 'USD');
                      const cashMoney = formatMoney(item.cashBalance, item.sourceCurrency || 'USD');
                      return (
                        <>
                          <div
                            className="mono"
                            style={{ fontWeight: 700, color: '#ffffff' }}
                            title={aumMoney.isConverted ? `Source: ${aumMoney.originalString} USD` : undefined}
                          >
                            {aumMoney.displayString}
                          </div>
                          <div
                            style={{
                              fontSize: '0.74rem',
                              color: item.cashBalance > 100000 ? '#fcd34d' : 'var(--text-muted)',
                              marginTop: '3px',
                            }}
                            title={cashMoney.isConverted ? `Source: ${cashMoney.originalString} USD` : undefined}
                          >
                            Cash: {cashMoney.displayString}
                          </div>
                        </>
                      );
                    })()}
                  </td>

                  {/* Workflow, Review Cadence & Freshness */}
                  <td style={{ padding: '14px 18px' }}>
                    {(() => {
                      const wf = getWorkflow(item.clientId);
                      const noteCount = wf.notes.length;
                      return (
                        <div style={{ marginBottom: '6px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                            <span
                              style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '4px',
                                padding: '2px 7px',
                                borderRadius: '4px',
                                fontSize: '0.70rem',
                                fontWeight: 700,
                                textTransform: 'uppercase',
                                letterSpacing: '0.04em',
                                background:
                                  wf.status === 'open'
                                    ? 'rgba(56, 189, 248, 0.15)'
                                    : wf.status === 'deferred'
                                    ? 'rgba(251, 191, 36, 0.15)'
                                    : 'rgba(52, 211, 153, 0.15)',
                                color:
                                  wf.status === 'open'
                                    ? '#38bdf8'
                                    : wf.status === 'deferred'
                                    ? '#fbbf24'
                                    : '#34d399',
                                border: `1px solid ${
                                  wf.status === 'open'
                                    ? 'rgba(56, 189, 248, 0.3)'
                                    : wf.status === 'deferred'
                                    ? 'rgba(251, 191, 36, 0.3)'
                                    : 'rgba(52, 211, 153, 0.3)'
                                }`,
                              }}
                            >
                              {wf.status === 'open' && (
                                <>
                                  <Clock size={10} />
                                  <span>Open Action</span>
                                </>
                              )}
                              {wf.status === 'deferred' && (
                                <>
                                  <PauseCircle size={10} />
                                  <span>Deferred: {wf.deferredUntil || 'Pending'}</span>
                                </>
                              )}
                              {wf.status === 'resolved' && (
                                <>
                                  <CheckCircle2 size={10} />
                                  <span>Resolved</span>
                                </>
                              )}
                            </span>

                            {noteCount > 0 && (
                              <span
                                style={{
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: '3px',
                                  fontSize: '0.68rem',
                                  color: '#cbd5e1',
                                  background: 'rgba(255, 255, 255, 0.08)',
                                  padding: '1px 5px',
                                  borderRadius: '3px',
                                  border: '1px solid rgba(255, 255, 255, 0.1)',
                                }}
                                title={`${noteCount} advisor note${noteCount > 1 ? 's' : ''} saved`}
                              >
                                <FileText size={10} />
                                {noteCount}
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })()}

                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '5px',
                        fontSize: '0.74rem',
                        color: item.isReviewOverdue ? '#fca5a5' : 'var(--text-muted)',
                      }}
                    >
                      <Calendar size={12} />
                      <span>
                        {item.daysSinceLastReview}d since review{' '}
                        {item.isReviewOverdue && '(Overdue)'}
                      </span>
                    </div>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '5px',
                        fontSize: '0.70rem',
                        color:
                          item.dataFreshnessDays > 5 ? '#fcd34d' : 'var(--text-dim)',
                        marginTop: '2px',
                      }}
                    >
                      <Database size={11} />
                      <span>Sync: {item.dataFreshnessDays}d ago</span>
                    </div>
                  </td>

                  {/* Action Button */}
                  <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectInsight(item);
                      }}
                      className="btn-outline"
                      style={{ padding: '5px 10px', fontSize: '0.75rem' }}
                      title="Open Client Review & Advisor Workflow"
                    >
                      <Eye size={13} />
                      <span>Review</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
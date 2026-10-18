import React, { useState, useEffect, useCallback } from 'react';
import { WorklistResponse, AdvisorInsight, HealthResponse } from './contracts/types';
import { fetchWorklist, checkBackendHealth, DEFAULT_USE_MOCKS } from './services/apiClient';
import { Header } from './components/Header';
import { WorklistSummary } from './components/WorklistSummary';
import { WorklistTable } from './components/WorklistTable';
import { EvidenceModal } from './components/EvidenceModal';
import { AlertTriangle, RefreshCw, Database, ShieldAlert } from 'lucide-react';

export const App: React.FC = () => {
  const [useMocks, setUseMocks] = useState<boolean>(DEFAULT_USE_MOCKS);
  const [data, setData] = useState<WorklistResponse | null>(null);
  const [dataSource, setDataSource] = useState<'live' | 'mock'>('mock');
  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedInsight, setSelectedInsight] = useState<AdvisorInsight | null>(null);
  const [backendHealth, setBackendHealth] = useState<HealthResponse | null>(null);

  // Check backend health
  const checkHealth = useCallback(async () => {
    const health = await checkBackendHealth();
    setBackendHealth(health);
  }, []);

  // Fetch worklist data
  const loadData = useCallback(async (filter: string, mocks: boolean) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetchWorklist(filter, mocks);
      setData(res.data);
      setDataSource(res.source);
    } catch (err: any) {
      setError(err?.message || 'Failed to connect to AdvantaIQ API');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    loadData(selectedFilter, useMocks);
  }, [checkHealth, loadData, selectedFilter, useMocks]);

  const handleToggleMocks = () => {
    const nextMode = !useMocks;
    setUseMocks(nextMode);
    loadData(selectedFilter, nextMode);
  };

  const handleRefresh = () => {
    checkHealth();
    loadData(selectedFilter, useMocks);
  };

  const handleFilterChange = (filter: string) => {
    setSelectedFilter(filter);
    loadData(filter, useMocks);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Global Header */}
      <Header
        useMocks={useMocks}
        onToggleMocks={handleToggleMocks}
        onRefresh={handleRefresh}
        isLoading={isLoading}
        health={backendHealth}
        dataSource={dataSource}
      />

      {/* Main Content Area */}
      <main style={{ flex: 1, maxWidth: '1440px', width: '100%', margin: '0 auto', padding: '28px 24px' }}>
        {/* Error Notification Banner */}
        {error && (
          <div
            style={{
              padding: '16px 20px',
              borderRadius: '10px',
              backgroundColor: 'rgba(239, 68, 68, 0.12)',
              border: '1px solid rgba(239, 68, 68, 0.35)',
              marginBottom: '24px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '16px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <AlertTriangle size={20} color="#f87171" />
              <div>
                <p style={{ fontWeight: 600, color: '#fca5a5', fontSize: '0.9rem' }}>
                  Live API Unavailable
                </p>
                <p style={{ fontSize: '0.8rem', color: '#cbd5e1', marginTop: '2px' }}>
                  {error}. You can run in offline Mock Mode or start the FastAPI server at <code>http://127.0.0.1:8000</code>.
                </p>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <button
                onClick={() => {
                  setUseMocks(true);
                  loadData(selectedFilter, true);
                }}
                className="btn-primary"
                style={{ fontSize: '0.78rem', padding: '6px 12px' }}
              >
                <Database size={13} />
                Switch to Mock Mode
              </button>
              <button
                onClick={handleRefresh}
                className="btn-outline"
                style={{ fontSize: '0.78rem', padding: '6px 12px' }}
              >
                <RefreshCw size={13} />
                Retry
              </button>
            </div>
          </div>
        )}

        {/* Loading State Skeleton */}
        {isLoading && !data && (
          <div style={{ padding: '60px 0', textAlign: 'center', color: 'var(--text-muted)' }}>
            <div
              style={{
                width: '40px',
                height: '40px',
                border: '3px solid rgba(56, 189, 248, 0.2)',
                borderTopColor: '#38bdf8',
                borderRadius: '50%',
                margin: '0 auto 16px',
                animation: 'spin 0.8s linear infinite',
              }}
            />
            <p style={{ fontWeight: 600, color: '#f8fafc' }}>
              Evaluating Prioritization Signals & Evidence...
            </p>
            <p style={{ fontSize: '0.82rem', marginTop: '4px' }}>
              Loading deterministic urgency engine scores from {useMocks ? 'Mock JSON' : 'FastAPI'}.
            </p>
          </div>
        )}

        {/* Loaded Dashboard Content */}
        {data && (
          <>
            {/* KPI Summary Cards */}
            <WorklistSummary data={data} />

            {/* Interactive Prioritization Worklist */}
            <div style={{ marginBottom: '16px', display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
              <div>
                <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#ffffff' }}>
                  Advisor Prioritization Worklist
                </h2>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                  Ranked by multi-factor composite urgency score (Goal risk, allocation drift, overdue reviews, cash drag).
                </p>
              </div>
              <span
                style={{
                  fontSize: '0.75rem',
                  color: 'var(--text-dim)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                Source: <span className="mono" style={{ color: '#38bdf8' }}>{dataSource.toUpperCase()}</span>
              </span>
            </div>

            <WorklistTable
              items={data.items}
              onSelectInsight={(item) => setSelectedInsight(item)}
              selectedFilter={selectedFilter}
              onFilterChange={handleFilterChange}
              counts={{
                total: data.totalCount,
                critical: data.criticalCount,
                high: data.highCount,
                medium: data.mediumCount,
                low: data.lowCount,
              }}
            />
          </>
        )}
      </main>

      {/* Evidence & Why Inspector Modal */}
      <EvidenceModal
        insight={selectedInsight}
        onClose={() => setSelectedInsight(null)}
      />

      {/* Footer */}
      <footer
        style={{
          borderTop: '1px solid var(--border-subtle)',
          padding: '18px 24px',
          textAlign: 'center',
          fontSize: '0.75rem',
          color: 'var(--text-dim)',
          backgroundColor: 'rgba(15, 23, 42, 0.4)',
        }}
      >
        <div style={{ maxWidth: '1440px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
          <span>
            AdvantaIQ • FinTech Hackathon Edition • AI-Powered Financial Advisor Intelligence
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <ShieldAlert size={13} color="#94a3b8" />
            <span>100% Synthetic Demo Data • Zero Real PII • Human-in-the-Loop Required</span>
          </span>
        </div>
      </footer>
    </div>
  );
};
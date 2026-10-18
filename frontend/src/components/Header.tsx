import React from 'react';
import { ShieldCheck, Database, RefreshCw, Cpu, Activity } from 'lucide-react';
import { HealthResponse } from '../contracts/types';
import { CurrencySelector } from './CurrencySelector';

interface HeaderProps {
  useMocks: boolean;
  onToggleMocks: () => void;
  onRefresh: () => void;
  isLoading: boolean;
  health: HealthResponse | null;
  dataSource: 'live' | 'mock';
}

export const Header: React.FC<HeaderProps> = ({
  useMocks,
  onToggleMocks,
  onRefresh,
  isLoading,
  health,
  dataSource,
}) => {
  return (
    <header
      style={{
        borderBottom: '1px solid var(--border-subtle)',
        background: 'rgba(15, 23, 42, 0.85)',
        backdropFilter: 'blur(12px)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        padding: '16px 28px',
      }}
    >
      <div
        style={{
          maxWidth: '1440px',
          margin: '0 auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        {/* Brand & Value Promise */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #0284c7 0%, #38bdf8 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 12px rgba(56, 189, 248, 0.3)',
              }}
            >
              <Cpu size={20} color="#ffffff" strokeWidth={2.5} />
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
              <h1 style={{ fontSize: '1.4rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#ffffff' }}>
                Advanta<span style={{ color: '#38bdf8' }}>IQ</span>
              </h1>
              <span
                style={{
                  fontSize: '0.68rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  background: 'rgba(56, 189, 248, 0.1)',
                  color: '#38bdf8',
                  border: '1px solid rgba(56, 189, 248, 0.3)',
                }}
              >
                Advisor Intelligence v1.0
              </span>
            </div>
          </div>
          <p
            style={{
              fontSize: '0.82rem',
              color: 'var(--text-muted)',
              marginTop: '4px',
              fontWeight: 500,
            }}
          >
            <strong style={{ color: '#e2e8f0' }}>Know Who Needs Attention.</strong>{' '}
            <strong style={{ color: '#38bdf8' }}>Understand Why.</strong>{' '}
            <strong style={{ color: '#86efac' }}>Act at the Right Time.</strong>
          </p>
        </div>

        {/* Controls: Currency, Mode Switch, Health, Refresh */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          {/* Global Display Currency Selector */}
          <CurrencySelector />

          {/* Backend Status indicator */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '8px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              fontSize: '0.78rem',
            }}
          >
            <Activity
              size={14}
              color={health ? '#4ade80' : useMocks ? '#38bdf8' : '#f87171'}
            />
            <span style={{ color: 'var(--text-muted)' }}>Engine:</span>
            <span style={{ fontWeight: 600, color: health ? '#4ade80' : useMocks ? '#7dd3fc' : '#f87171' }}>
              {health ? 'Live API (FastAPI)' : useMocks ? 'Mock Engine (' + dataSource + ')' : 'Offline'}
            </span>
          </div>

          {/* Data Source Toggle */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              background: 'var(--bg-card)',
              borderRadius: '8px',
              padding: '3px',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <button
              onClick={onToggleMocks}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '5px 12px',
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.75rem',
                fontWeight: 600,
                background: useMocks ? '#0284c7' : 'transparent',
                color: useMocks ? '#ffffff' : 'var(--text-muted)',
                transition: 'all 0.2s ease',
              }}
              title="Runs entirely in the browser using static fixture data without requiring a backend server"
            >
              <Database size={13} />
              Mock JSON
            </button>
            <button
              onClick={onToggleMocks}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '5px 12px',
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.75rem',
                fontWeight: 600,
                background: !useMocks ? '#0284c7' : 'transparent',
                color: !useMocks ? '#ffffff' : 'var(--text-muted)',
                transition: 'all 0.2s ease',
              }}
              title="Connects to FastAPI running on 127.0.0.1:8000"
            >
              <ShieldCheck size={13} />
              Live API
            </button>
          </div>

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="btn-outline"
            style={{ padding: '6px 12px', fontSize: '0.78rem' }}
          >
            <RefreshCw size={14} className={isLoading ? 'spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>
    </header>
  );
};
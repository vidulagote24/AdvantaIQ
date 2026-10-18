import React from 'react';
import { WorklistResponse } from '../contracts/types';
import { Users, AlertCircle, AlertTriangle, DollarSign } from 'lucide-react';
import { useCurrency } from '../context/CurrencyContext';

interface WorklistSummaryProps {
  data: WorklistResponse;
}

export const WorklistSummary: React.FC<WorklistSummaryProps> = ({ data }) => {
  const { formatMoney } = useCurrency();
  const totalAum = data.items.reduce((acc, curr) => acc + curr.totalAum, 0);
  const aumFormatted = formatMoney(totalAum, 'USD');

  const cards = [
    {
      title: 'Monitored Clients',
      value: data.totalCount,
      subtext: 'Assigned advisor book',
      icon: Users,
      color: '#38bdf8',
      bgGlow: 'rgba(56, 189, 248, 0.08)',
    },
    {
      title: 'Critical Attention',
      value: data.criticalCount,
      subtext: 'Score ≥ 80 / Severe breach',
      icon: AlertCircle,
      color: '#f87171',
      bgGlow: 'rgba(239, 68, 68, 0.1)',
      highlight: data.criticalCount > 0,
    },
    {
      title: 'High Priority',
      value: data.highCount,
      subtext: 'Score 65–79 / Action required',
      icon: AlertTriangle,
      color: '#fbbf24',
      bgGlow: 'rgba(245, 158, 11, 0.08)',
    },
    {
      title: 'Total Book AUM',
      value: aumFormatted.displayString,
      subtext: aumFormatted.isConverted
        ? `Orig: ${aumFormatted.originalString} USD`
        : 'Under advisor supervision (USD)',
      icon: DollarSign,
      color: '#4ade80',
      bgGlow: 'rgba(34, 197, 94, 0.08)',
    },
  ];

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '16px',
        marginBottom: '28px',
      }}
    >
      {cards.map((c, i) => {
        const Icon = c.icon;
        return (
          <div
            key={i}
            className="glass-panel"
            style={{
              padding: '20px',
              position: 'relative',
              overflow: 'hidden',
              boxShadow: c.highlight ? '0 0 20px rgba(239, 68, 68, 0.15)' : 'none',
              borderColor: c.highlight ? 'rgba(239, 68, 68, 0.3)' : 'var(--border-subtle)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '12px',
              }}
            >
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                {c.title}
              </span>
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: c.bgGlow,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Icon size={16} color={c.color} />
              </div>
            </div>
            <div
              className="mono"
              style={{
                fontSize: typeof c.value === 'string' ? '1.5rem' : '1.85rem',
                fontWeight: 800,
                color: c.highlight ? '#fca5a5' : '#ffffff',
                letterSpacing: '-0.02em',
                lineHeight: 1.1,
              }}
            >
              {c.value}
            </div>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-dim)', marginTop: '8px' }}>
              {c.subtext}
            </div>
          </div>
        );
      })}
    </div>
  );
};
import React from 'react';
import { UrgencyLevel } from '../contracts/types';
import { AlertCircle, AlertTriangle, Info, CheckCircle2 } from 'lucide-react';

interface UrgencyBadgeProps {
  level: UrgencyLevel;
  score?: number;
  showIcon?: boolean;
}

export const UrgencyBadge: React.FC<UrgencyBadgeProps> = ({ level, score, showIcon = true }) => {
  const configs = {
    critical: {
      bg: 'var(--urgency-critical-bg)',
      border: 'var(--urgency-critical-border)',
      color: 'var(--urgency-critical-text)',
      label: 'CRITICAL',
      icon: AlertCircle,
    },
    high: {
      bg: 'var(--urgency-high-bg)',
      border: 'var(--urgency-high-border)',
      color: 'var(--urgency-high-text)',
      label: 'HIGH',
      icon: AlertTriangle,
    },
    medium: {
      bg: 'var(--urgency-medium-bg)',
      border: 'var(--urgency-medium-border)',
      color: 'var(--urgency-medium-text)',
      label: 'MEDIUM',
      icon: Info,
    },
    low: {
      bg: 'var(--urgency-low-bg)',
      border: 'var(--urgency-low-border)',
      color: 'var(--urgency-low-text)',
      label: 'LOW',
      icon: CheckCircle2,
    },
  };

  const c = configs[level] || configs.low;
  const IconComponent = c.icon;

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding: '3px 8px',
        borderRadius: '6px',
        fontSize: '0.72rem',
        fontWeight: 700,
        letterSpacing: '0.04em',
        backgroundColor: c.bg,
        border: `1px solid ${c.border}`,
        color: c.color,
      }}
    >
      {showIcon && <IconComponent size={13} strokeWidth={2.5} />}
      <span>{c.label}</span>
      {score !== undefined && (
        <span
          className="mono"
          style={{
            marginLeft: '4px',
            paddingLeft: '6px',
            borderLeft: `1px solid ${c.border}`,
            fontSize: '0.72rem',
          }}
        >
          {score}/100
        </span>
      )}
    </span>
  );
};
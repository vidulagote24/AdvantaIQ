import React, { useState, useRef, useEffect } from 'react';
import { useCurrency } from '../context/CurrencyContext';
import { Globe, ChevronDown, Check, Info } from 'lucide-react';

export const CurrencySelector: React.FC = () => {
  const { displayCurrency, setDisplayCurrency, currencies, activeConfig, rateInfo } =
    useCurrency();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const isConverted = displayCurrency !== 'USD';

  return (
    <div ref={dropdownRef} style={{ position: 'relative', display: 'inline-flex', alignItems: 'center' }}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '7px',
          padding: '6px 12px',
          borderRadius: '8px',
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          color: '#ffffff',
          cursor: 'pointer',
          fontSize: '0.78rem',
          fontWeight: 600,
          transition: 'all 0.15s ease',
        }}
        title={`Display Currency: ${activeConfig.name} (${activeConfig.code}) - Click to change`}
      >
        <span style={{ fontSize: '0.9rem' }}>{activeConfig.flag}</span>
        <span className="mono" style={{ color: '#38bdf8' }}>{activeConfig.symbol}</span>
        <span style={{ color: '#f1f5f9' }}>{activeConfig.code}</span>
        <ChevronDown size={13} color="var(--text-muted)" style={{ transform: isOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.15s' }} />
      </button>

      {/* Conversion Rate Indicator Pill (When display currency != source USD) */}
      {isConverted && (
        <span
          style={{
            marginLeft: '8px',
            fontSize: '0.7rem',
            padding: '3px 8px',
            borderRadius: '12px',
            background: 'rgba(56, 189, 248, 0.08)',
            border: '1px solid rgba(56, 189, 248, 0.25)',
            color: '#7dd3fc',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
            cursor: 'help',
          }}
          title={`${rateInfo.disclaimer} Benchmark Rate: 1 USD = ${rateInfo.rate.toLocaleString()} ${displayCurrency} (${rateInfo.provider})`}
        >
          <Info size={11} />
          <span className="mono">1 USD = {activeConfig.symbol}{rateInfo.rate.toFixed(2)}</span>
        </span>
      )}

      {/* Popover Menu */}
      {isOpen && (
        <div
          style={{
            position: 'absolute',
            top: 'calc(100% + 6px)',
            right: 0,
            zIndex: 100,
            minWidth: '220px',
            borderRadius: '10px',
            backgroundColor: '#0f172a',
            border: '1px solid var(--border-highlight)',
            boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.6)',
            padding: '6px',
            display: 'flex',
            flexDirection: 'column',
            gap: '2px',
          }}
        >
          <div
            style={{
              padding: '6px 10px',
              fontSize: '0.68rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              color: 'var(--text-dim)',
              borderBottom: '1px solid var(--border-subtle)',
              marginBottom: '4px',
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
            }}
          >
            <Globe size={11} />
            <span>Select Display Currency</span>
          </div>

          {currencies.map((curr) => {
            const isSelected = curr.code === displayCurrency;
            return (
              <button
                key={curr.code}
                onClick={() => {
                  setDisplayCurrency(curr.code);
                  setIsOpen(false);
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '7px 10px',
                  borderRadius: '6px',
                  border: 'none',
                  background: isSelected ? 'rgba(56, 189, 248, 0.12)' : 'transparent',
                  color: isSelected ? '#38bdf8' : '#e2e8f0',
                  cursor: 'pointer',
                  fontSize: '0.78rem',
                  fontWeight: isSelected ? 700 : 500,
                  textAlign: 'left',
                  transition: 'background-color 0.12s ease',
                }}
                onMouseEnter={(e) => {
                  if (!isSelected) e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                }}
                onMouseLeave={(e) => {
                  if (!isSelected) e.currentTarget.style.backgroundColor = 'transparent';
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '1rem' }}>{curr.flag}</span>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                      <span className="mono" style={{ fontWeight: 700 }}>{curr.code}</span>
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>({curr.symbol})</span>
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>{curr.name}</div>
                  </div>
                </div>
                {isSelected && <Check size={14} color="#38bdf8" />}
              </button>
            );
          })}

          <div
            style={{
              padding: '8px 10px 4px',
              marginTop: '4px',
              borderTop: '1px solid var(--border-subtle)',
              fontSize: '0.66rem',
              color: 'var(--text-dim)',
              lineHeight: 1.3,
            }}
          >
            Source records: <strong style={{ color: '#cbd5e1' }}>USD</strong>. Rates are benchmark demo rates for presentation only.
          </div>
        </div>
      )}
    </div>
  );
};

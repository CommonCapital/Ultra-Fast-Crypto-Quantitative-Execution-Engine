import React, { useState } from 'react';

const fmt = (n, decimals = 2) => {
  if (n === undefined || n === null || isNaN(n)) return '—';
  const abs = Math.abs(n);
  if (abs >= 1000000) return `$${(n / 1000000).toFixed(2)}M`;
  if (abs >= 1000) return `$${(n / 1000).toFixed(2)}K`;
  return `$${n.toFixed(decimals)}`;
};

const pnlColor = (v) => {
  if (!v && v !== 0) return 'var(--text-muted)';
  if (v > 0) return 'var(--success)';
  if (v < 0) return 'var(--danger)';
  return 'var(--text-muted)';
};

export function PortfolioStats({ portfolio, onCapitalChange }) {
  const [editingCapital, setEditingCapital] = useState(false);
  const [capitalInput, setCapitalInput] = useState('');

  if (!portfolio || Object.keys(portfolio).length === 0) return null;

  const {
    total_deployed_usdt = 0,
    unrealized_pnl_usdt = 0,
    realized_pnl_usdt = 0,
    total_pnl_usdt = 0,
    trade_count = 0,
    win_rate = 0,
    capital_per_unit = 1000,
    open_positions = 0,
  } = portfolio;

  const handleCapitalSubmit = () => {
    const val = parseFloat(capitalInput);
    if (!isNaN(val) && val > 0) {
      onCapitalChange(val);
    }
    setEditingCapital(false);
    setCapitalInput('');
  };

  const statBox = (label, value, color, sub) => (
    <div style={{
      background: 'rgba(255,255,255,0.04)',
      border: `1px solid ${color || 'rgba(255,255,255,0.1)'}`,
      borderRadius: '10px',
      padding: '0.75rem 1.1rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.15rem',
      minWidth: '130px',
      flex: 1,
    }}>
      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</div>
      <div style={{ fontSize: '1.15rem', fontWeight: '700', color: color || 'var(--text-main)' }}>{value}</div>
      {sub && <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{sub}</div>}
    </div>
  );

  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(16,24,39,0.9) 0%, rgba(30,41,59,0.9) 100%)',
      border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: '14px',
      padding: '1rem 1.4rem',
      marginBottom: '1.2rem',
      backdropFilter: 'blur(10px)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.8rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <span style={{ fontSize: '1rem', fontWeight: '700', color: 'var(--text-main)' }}>📊 Portfolio Overview</span>
          <span style={{
            fontSize: '0.7rem', padding: '2px 8px', borderRadius: '20px',
            background: open_positions > 0 ? 'rgba(16,185,129,0.15)' : 'rgba(255,255,255,0.05)',
            color: open_positions > 0 ? 'var(--success)' : 'var(--text-muted)',
            border: `1px solid ${open_positions > 0 ? 'var(--success)' : 'rgba(255,255,255,0.1)'}`,
            fontWeight: 'bold',
          }}>
            {open_positions} OPEN {open_positions === 1 ? 'POSITION' : 'POSITIONS'}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          <span>💼 Capital/Unit:</span>
          {editingCapital ? (
            <div style={{ display: 'flex', gap: '0.3rem' }}>
              <input
                type="number"
                value={capitalInput}
                onChange={e => setCapitalInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') handleCapitalSubmit(); if (e.key === 'Escape') setEditingCapital(false); }}
                autoFocus
                style={{
                  background: 'rgba(255,255,255,0.1)', border: '1px solid var(--accent-primary)',
                  color: 'white', borderRadius: '6px', padding: '2px 8px', width: '90px', fontSize: '0.8rem'
                }}
                placeholder={`$${capital_per_unit}`}
              />
              <button onClick={handleCapitalSubmit} style={{ background: 'var(--accent-primary)', border: 'none', color: 'white', borderRadius: '6px', padding: '2px 10px', cursor: 'pointer', fontSize: '0.75rem' }}>✓</button>
              <button onClick={() => setEditingCapital(false)} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: 'white', borderRadius: '6px', padding: '2px 8px', cursor: 'pointer', fontSize: '0.75rem' }}>✕</button>
            </div>
          ) : (
            <button
              onClick={() => { setEditingCapital(true); setCapitalInput(String(capital_per_unit)); }}
              style={{
                background: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.15)',
                color: 'var(--accent-glow)', borderRadius: '6px', padding: '2px 10px', cursor: 'pointer',
                fontSize: '0.8rem', fontWeight: 'bold'
              }}
            >
              {fmt(capital_per_unit)} <span style={{ opacity: 0.6, fontSize: '0.65rem' }}>✏️</span>
            </button>
          )}
        </div>
      </div>

      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
        {statBox(
          '💰 Capital Deployed',
          fmt(total_deployed_usdt),
          total_deployed_usdt > 0 ? 'rgba(59,130,246,0.8)' : null,
          `${open_positions} position${open_positions !== 1 ? 's' : ''} × ${fmt(capital_per_unit)}/unit`
        )}
        {statBox(
          '📈 Unrealized P&L',
          `${unrealized_pnl_usdt >= 0 ? '+' : ''}${fmt(unrealized_pnl_usdt)}`,
          pnlColor(unrealized_pnl_usdt),
          'Live open positions'
        )}
        {statBox(
          '✅ Realized P&L',
          `${realized_pnl_usdt >= 0 ? '+' : ''}${fmt(realized_pnl_usdt)}`,
          pnlColor(realized_pnl_usdt),
          `${trade_count} closed trade${trade_count !== 1 ? 's' : ''}`
        )}
        {statBox(
          '💎 Total P&L',
          `${total_pnl_usdt >= 0 ? '+' : ''}${fmt(total_pnl_usdt)}`,
          pnlColor(total_pnl_usdt),
          'Realized + Unrealized'
        )}
        {statBox(
          '🏆 Win Rate',
          trade_count > 0 ? `${win_rate}%` : '—',
          win_rate >= 60 ? 'var(--success)' : win_rate >= 40 ? 'var(--accent-glow)' : trade_count > 0 ? 'var(--danger)' : null,
          `${trade_count} total trades`
        )}
      </div>
    </div>
  );
}

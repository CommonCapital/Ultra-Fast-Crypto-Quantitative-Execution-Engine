import React from 'react';

export function ArbAlert({ opportunity }) {
  if (!opportunity) return null;

  return (
    <div className="alert-card" style={{ marginBottom: '1rem', borderLeft: '4px solid var(--danger)' }}>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem' }}>
        <span className="pulse" style={{ backgroundColor: 'var(--danger)' }}></span>
        <strong style={{ color: 'var(--danger)', letterSpacing: '2px' }}>ACTION REQUIRED</strong>
      </div>
      <div className="alert-message" style={{ 
        fontFamily: 'monospace', 
        whiteSpace: 'pre-wrap',
        backgroundColor: '#111',
        padding: '1rem',
        borderRadius: '8px',
        color: '#0f0',
        lineHeight: '1.5'
      }}>
        {opportunity.alert_message || (
          `========================================\n` +
          `🚨 LOCAL ALERT: ${opportunity.pair}\n` +
          `📈 Net Spread (Post-Fees): ${opportunity.spread_pct}%\n` +
          `🛒 Buy on ${opportunity.buy_exchange} at $${opportunity.buy_price}\n` +
          `💰 Sell on ${opportunity.sell_exchange} at $${opportunity.sell_price}\n` +
          `📊 Momentum: Buy Vol ${opportunity.buy_vol?.toFixed(2) || 0} | Sell Vol ${opportunity.sell_vol?.toFixed(2) || 0}\n` +
          `💧 Coinbase Liq Pool: Sell ${opportunity.cb_short_liq?.toFixed(2) || 0} - Buy ${opportunity.cb_long_liq?.toFixed(2) || 0} (Diff: +${((opportunity.cb_short_liq || 0) - (opportunity.cb_long_liq || 0)).toFixed(2)})\n` +
          `🌍 Global Metrics: F&G (See Terminal) | CMC Vol (See Terminal)\n` +
          `========================================`
        )}
      </div>
    </div>
  );
}

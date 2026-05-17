import React from 'react';

export function AlertLog({ alerts }) {
  if (!alerts || alerts.length === 0) return <div className="text-muted" style={{ padding: '1rem 0' }}>No recent alerts.</div>;

  return (
    <div className="alerts-list">
      {alerts.map((alert, idx) => (
        <div key={idx} className="alert-card" style={{ background: 'rgba(255,255,255,0.02)', borderColor: 'var(--glass-border)' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
            {alert.time} | {alert.pair}
          </div>
          <div className="alert-message" style={{ whiteSpace: 'pre-line', fontSize: '0.85rem', lineHeight: '1.4', marginTop: '0.4rem' }}>{alert.message}</div>
        </div>
      ))}
    </div>
  );
}

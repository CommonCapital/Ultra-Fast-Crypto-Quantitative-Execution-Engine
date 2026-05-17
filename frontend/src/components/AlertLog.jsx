import React from 'react';

export function AlertLog({ alerts }) {
  if (!alerts || alerts.length === 0) return <div className="text-muted" style={{ padding: '1rem 0' }}>No recent alerts.</div>;

  return (
    <div className="alerts-list" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: '600px', overflowY: 'auto', paddingRight: '0.5rem' }}>
      {alerts.map((alert, idx) => {
        const isExit = alert.message.includes('TAKE-PROFIT');
        const isDca = alert.message.includes('DCA EXECUTED');
        const borderColor = isExit ? 'var(--success)' : (isDca ? 'var(--accent-glow)' : 'var(--danger)');
        const colorTitle = isExit ? 'var(--success)' : (isDca ? 'var(--accent-glow)' : 'var(--danger)');

        return (
          <div key={idx} className="alert-card" style={{ 
            flexShrink: 0,
            background: 'rgba(10, 10, 10, 0.8)', 
            borderLeft: `4px solid ${borderColor}`,
            borderRadius: '0 8px 8px 0',
            padding: '1rem',
            boxShadow: '0 4px 6px rgba(0,0,0,0.3)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.5rem' }}>
              <div style={{ fontSize: '0.9rem', fontWeight: 'bold', color: colorTitle, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span className="pulse" style={{ backgroundColor: colorTitle, width: '8px', height: '8px' }}></span>
                {alert.pair}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                🕒 {alert.time}
              </div>
            </div>
            <div className="alert-message" style={{ 
              fontFamily: 'monospace', 
              whiteSpace: 'pre-wrap', 
              wordBreak: 'break-word',
              overflowWrap: 'break-word',
              fontSize: '0.8rem', 
              lineHeight: '1.5', 
              color: isExit ? '#4ade80' : (isDca ? '#facc15' : '#10b981'),
              marginTop: '0.5rem',
              backgroundColor: '#050505',
              padding: '0.8rem',
              borderRadius: '4px',
              border: '1px solid rgba(255,255,255,0.05)'
            }}>
              {alert.message}
            </div>
          </div>
        );
      })}
    </div>
  );
}

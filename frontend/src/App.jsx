import React, { useState, useEffect } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { PriceMatrix } from './components/PriceMatrix';
import { ArbAlert } from './components/ArbAlert';
import { AlertLog } from './components/AlertLog';

function App() {
  const { data, globalData, status } = useWebSocket('ws://localhost:8000/ws');
  const [alerts, setAlerts] = useState([]);
  const [activePair, setActivePair] = useState('BTC/USDT');

  // Find the selected pair data
  const primaryPairData = data.find(p => p.pair === activePair) || (data.length > 0 ? data[0] : null);

  // Listen for new alerts in all data streams
  useEffect(() => {
    if (data && data.length > 0) {
      data.forEach(pairData => {
        if (pairData?.opportunity?.alert_message) {
          setAlerts(prev => {
            const newAlert = {
              time: new Date().toLocaleTimeString(),
              pair: pairData.pair,
              message: pairData.opportunity.alert_message
            };
            // Avoid duplicates if same message
            if (prev.length > 0 && prev[0].message === newAlert.message) return prev;
            return [newAlert, ...prev].slice(0, 50); // keep last 50
          });
        }
      });
    }
  }, [data]);

  // Unique list of pairs
  const availablePairs = data.map(p => p.pair);

  return (
    <div className="dashboard-container">
      <header>
        <h1>Ultra-Fast Crypto Quantitative Execution Engine</h1>
        <div className="status-bar">
          <div className="pulse" style={{ backgroundColor: status === 'Connected' ? 'var(--success)' : 'var(--danger)' }}></div>
          Status: {status}
        </div>
      </header>

      <main className="main-content">
        <section className="panel">
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', borderBottom: '1px solid #333', paddingBottom: '1rem' }}>
            {availablePairs.map(pair => {
              const pairHasAlert = data.find(p => p.pair === pair)?.opportunity != null;
              return (
                <button
                  key={pair}
                  onClick={() => setActivePair(pair)}
                  style={{
                    background: activePair === pair ? 'var(--accent-primary)' : (pairHasAlert ? 'rgba(239, 68, 68, 0.2)' : 'transparent'),
                    color: pairHasAlert && activePair !== pair ? '#ff6b6b' : 'white',
                    border: pairHasAlert ? '1px solid var(--danger)' : '1px solid var(--accent-primary)',
                    boxShadow: pairHasAlert ? '0 0 15px rgba(239, 68, 68, 0.6)' : (activePair === pair ? '0 0 10px var(--accent-glow)' : 'none'),
                    padding: '0.5rem 1rem',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    transition: 'all 0.3s ease',
                    fontWeight: pairHasAlert ? 'bold' : 'normal'
                  }}
                >
                  {pair} {pairHasAlert && '🚨'}
                </button>
              )
            })}
          </div>
          <h2>Live Exchange Matrix — {primaryPairData?.pair || 'Loading...'}</h2>
          <PriceMatrix prices={primaryPairData?.prices || {}} />
        </section>

        <section className="panel">
          <h2>Market Signals & Liquidity — {primaryPairData?.pair || 'Loading...'}</h2>
          <div className="signals-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
            <div className="signal-item">
              <div className="signal-label">Fear & Greed Index</div>
              <div className="signal-value" style={{ fontSize: '1rem', display: 'flex', flexDirection: 'column', gap: '0.4rem', marginTop: '0.5rem' }}>
                {globalData?.fng ? (
                  <>
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--success)' }}>
                      <span>Greed:</span>
                      <span>{globalData.fng.value}%</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--danger)' }}>
                      <span>Fear:</span>
                      <span>{100 - parseInt(globalData.fng.value)}%</span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem', textAlign: 'left' }}>
                      Status: {globalData.fng.class}
                    </div>
                  </>
                ) : (
                  <span style={{ color: 'var(--text-muted)' }}>Loading...</span>
                )}
              </div>
            </div>

            <div className="signal-item">
              <div className="signal-label">Coinbase Orderbook Liq (L2)</div>
              <div className="signal-value" style={{ fontSize: '1rem', display: 'flex', flexDirection: 'column', gap: '0.4rem', marginTop: '0.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--success)' }}>
                  <span>Buy (Longs):</span>
                  <span>{primaryPairData?.prices?.Coinbase?.long_liq?.toFixed(2) || '0.00'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--danger)' }}>
                  <span>Sell (Shorts):</span>
                  <span>{primaryPairData?.prices?.Coinbase?.short_liq?.toFixed(2) || '0.00'}</span>
                </div>
              </div>
            </div>

            <div className="signal-item">
              <div className="signal-label">Binance Volume Momentum</div>
              <div className="signal-value" style={{ fontSize: '1rem', display: 'flex', flexDirection: 'column', gap: '0.4rem', marginTop: '0.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--success)' }}>
                  <span>Buy Vol:</span>
                  <span>{primaryPairData?.prices?.Binance?.buy_vol?.toFixed(2) || '0.00'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--danger)' }}>
                  <span>Sell Vol:</span>
                  <span>{primaryPairData?.prices?.Binance?.sell_vol?.toFixed(2) || '0.00'}</span>
                </div>
              </div>
            </div>

            <div className="signal-item" style={{ border: '1px solid var(--accent-primary)', background: 'rgba(59, 130, 246, 0.05)' }}>
              <div className="signal-label">AI Action Recommendation</div>
              <div className="signal-value" style={{ fontSize: '1rem', display: 'flex', flexDirection: 'column', gap: '0.4rem', marginTop: '0.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: primaryPairData?.signals?.confidence >= 55 ? 'var(--success)' : (primaryPairData?.signals?.confidence <= 45 ? 'var(--danger)' : 'var(--text-main)') }}>
                  <span>Signal:</span>
                  <span style={{ fontWeight: 'bold' }}>{primaryPairData?.signals?.recommendation || 'NEUTRAL'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Confidence:</span>
                  <span>{primaryPairData?.signals?.confidence || 50}%</span>
                </div>
                {primaryPairData?.signals?.lagging_exchange && primaryPairData.signals.recommendation.includes('BUY') && (
                  <div style={{ fontSize: '0.75rem', color: 'var(--success)', marginTop: '0.2rem', textAlign: 'left', lineHeight: '1.4' }}>
                    💡 Target: Buy on {primaryPairData.signals.lagging_exchange} (Lagging by {primaryPairData.signals.lagging_diff}%)
                  </div>
                )}
              </div>
            </div>

            <div className="signal-item" style={{ border: '1px solid rgba(255,255,255,0.1)' }}>
              <div className="signal-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Geopolitics & Macro Sentiment</span>
                <span style={{ 
                  fontSize: '0.7rem', 
                  padding: '2px 6px', 
                  borderRadius: '4px', 
                  fontWeight: 'bold',
                  background: globalData?.macro?.score >= 20 ? 'rgba(16, 185, 129, 0.2)' : (globalData?.macro?.score <= -20 ? 'rgba(239, 68, 68, 0.2)' : 'rgba(255,255,255,0.1)'),
                  color: globalData?.macro?.score >= 20 ? 'var(--success)' : (globalData?.macro?.score <= -20 ? 'var(--danger)' : 'var(--text-muted)')
                }}>
                  {globalData?.macro?.status || 'Neutral'}
                </span>
              </div>
              <div className="signal-value" style={{ fontSize: '1rem', display: 'flex', flexDirection: 'column', gap: '0.4rem', marginTop: '0.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Sentiment Score:</span>
                  <span style={{ 
                    fontWeight: 'bold', 
                    color: globalData?.macro?.score > 0 ? 'var(--success)' : (globalData?.macro?.score < 0 ? 'var(--danger)' : 'inherit') 
                  }}>
                    {globalData?.macro ? `${globalData.macro.score > 0 ? '+' : ''}${globalData.macro.score}` : '0'}
                  </span>
                </div>
                {globalData?.macro?.keyword_hits && globalData.macro.keyword_hits.length > 0 && (
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.3rem', textAlign: 'left', display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                    {globalData.macro.keyword_hits.map((hit, idx) => (
                      <span key={idx} style={{ background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.1)' }}>{hit}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        {primaryPairData?.opportunity && (
          <section className="panel" style={{ padding: 0, background: 'transparent', border: 'none', boxShadow: 'none' }}>
            <ArbAlert opportunity={primaryPairData.opportunity} />
          </section>
        )}

        <section className="panel" style={{ marginTop: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #333', paddingBottom: '0.8rem', marginBottom: '1rem' }}>
            <h2 style={{ margin: 0 }}>📰 Live Market & Geopolitical Newsletter Feed</h2>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Real-time NLP situational awareness</span>
          </div>
          {globalData?.macro?.top_headlines && globalData.macro.top_headlines.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
              {globalData.macro.top_headlines.map((article, idx) => {
                const title = typeof article === 'string' ? article : article.title;
                const link = typeof article === 'string' ? '#' : article.link;
                const summary = typeof article === 'string' ? 'AI News Radar: Scanned for high-impact liquidity and macro risk catalysts.' : article.summary;
                
                return (
                  <a key={idx} href={link} target="_blank" rel="noreferrer" style={{ 
                    padding: '1rem', 
                    background: 'rgba(255,255,255,0.03)', 
                    border: '1px solid rgba(255,255,255,0.08)', 
                    borderRadius: '8px',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '1rem',
                    transition: 'all 0.2s ease',
                    textDecoration: 'none',
                    color: 'inherit'
                  }}
                  onMouseOver={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.08)'; e.currentTarget.style.borderColor = 'var(--accent-primary)'; }}
                  onMouseOut={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.03)'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'; }}
                  >
                    <span style={{ fontSize: '1.5rem', marginTop: '2px' }}>🗞️</span>
                    <div style={{ flex: 1, textAlign: 'left' }}>
                      <div style={{ fontWeight: '600', color: 'var(--text-main)', fontSize: '1rem', marginBottom: '0.3rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span>{title}</span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--accent-primary)' }}>Read Article ↗</span>
                      </div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>{summary}</div>
                    </div>
                  </a>
                );
              })}
            </div>
          ) : (
            <div style={{ padding: '2rem', color: 'var(--text-muted)', textAlign: 'center' }}>Connecting to live news aggregators...</div>
          )}
        </section>
      </main>

      <aside>
        <div className="panel" style={{ height: '100%' }}>
          <h2>Alert History</h2>
          <AlertLog alerts={alerts} />
        </div>
      </aside>
    </div>
  );
}

export default App;


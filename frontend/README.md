# 🖥️ Ultra-Fast Crypto Arbitrage & Quantitative Dashboard

The frontend interface for the Ultra-Fast Crypto Quantitative Execution Platform. Engineered with React, Vite, and Vanilla CSS to deliver sub-millisecond visual tick rendering, real-time Level-2 liquidity monitoring, and live geopolitical sentiment awareness.

## ✨ Premium UI & Architecture Highlights

* **Sub-Millisecond Data Ingestion:** Connects directly via WebSockets (`ws://localhost:8000/ws`) to receive 500ms multi-exchange orderbook updates.
* **Multi-Venue Price Matrix:** Instant visual comparison across 7 top global exchanges (Binance, Bybit, OKX, Coinbase, MEXC, BitMEX, BingX).
* **Situational Awareness Ticker:** Dedicated interactive newsletter stream pulling live articles from Google News RSS aggregators with AI keyword tagging and clickable source references.
* **Lagging Exchange Alpha Radar:** Live tactical alert log capturing sub-millisecond execution opportunities whenever an exchange lags >= 5% behind global top liquidity.

## 🚀 Running Locally

```bash
# Install dependencies
npm install

# Start Vite dev server (runs on port 5173 by default)
npm run dev
```

## 🎨 Design System

Built strictly using modern Vanilla CSS (`index.css`) featuring deep dark modes (`#0B0E14`), glassmorphism panels, and HSL tailored color palettes for institutional aesthetic excellence.

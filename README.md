# 📈 Ultra-Fast Crypto Quantitative Execution Engine

A high-performance, in-memory cryptocurrency quantitative analysis and high-frequency execution platform. 

Unlike traditional polling bots, AI wrappers, or heavy database-bound applications, this platform is optimized strictly for **sub-millisecond velocity** and **deterministic mathematical execution**. It opens persistent WebSocket connections to major exchanges, slurps live tick data and Order Book Level-2 depth directly into a Redis hot-cache, and evaluates multi-venue momentum in 50ms cycles. 

When high-conviction dislocations are detected that pass strict fee-adjusted profitability thresholds, the Quantitative Execution Algorithm dispatches tactical signals directly to your Terminal and a sleek React Dashboard, and manages fully automated execution through advanced risk mechanics.

---

## ✨ Core Features

* **RAM-Only Architecture**: Zero database overhead. Data is streamed via WebSockets directly into a local Redis cache for blazing-fast read/write cycles.
* **100% Real-Time Data**: Live feeds from Binance, Bybit, MEXC, BingX, Coinbase, OKX, HTX, and Bitunix. *(BitMEX was intentionally removed due to low liquidity).*
* **Strict Mathematical Execution**:
  * **Compound Net Profit**: Calculates exact capital returns by deducting both the *Taker Buy Fee* and *Taker Sell Fee* specifically for the exchange involved in the trade (e.g., 0.10% for Binance/Bitunix vs. 0.20% for HTX). Guarantees a rigid minimum net profit equal to your dynamic **Target Net Profit** after all slippage and commissions.
  * **Clear Growth Momentum**: Evaluates live trade streams to ensure `Recent Buy Volume > Recent Sell Volume` before firing an alert.
  * **Real-Time L2 Liquidity Squeeze**: Evaluates the live Coinbase Level-2 order book dynamically, comparing the total dollar value of the Sell Liquidity pool against the Buy Liquidity pool to ensure upward price pressure. Guarantees trades never trigger at local market resistance by enforcing short liquidity overhang.
* **Global Macro Context**: Enriches alerts by fetching the real-time **Fear & Greed Index** (via Alternative.me) and **Global 24h Volume** (via CoinMarketCap API). *Note: CMC is queried exactly once every 5 minutes to guarantee it stays 100% free under their 10,000 credit/month limit.*
* **Geopolitical & Macro News Sentiment**: Asynchronously parses public RSS feeds (CoinTelegraph, CoinDesk) every 60 seconds. Evaluates institutional NLP keyword weights to maintain a real-time macro risk rating (-100 to +100).
* **Premium Dashboard**: A beautifully designed, glassmorphic React/Vite dashboard running on vanilla CSS to monitor the live Exchange Matrix, isolated asset positions, and portfolio mark-to-market USDT analytics.

---

## 🧠 Quantitative Algorithmic Strategy & Execution

This engine relies strictly on hard-coded mathematical logic, order book physics, and statistical probability. There are no unpredictable generative wrappers or sentiment hallucinations involved in execution.

### 🛡️ Asymmetric Risk Diamond-Hand Execution Mechanics
The bot manages live positions with an institutional asymmetric risk model designed for pure positive compounding. All stop-loss and loss-cutting mechanisms have been intentionally purged. Inventory is diamond-handed indefinitely until net positive mean reversion succeeds or the asset goes bankrupt:

1. **Permanent Inventory Lock**: Active open positions are locked into Redis without expiration TTLs. Whether a trade takes 5 minutes, 5 days, or 5 months, the inventory is held securely in RAM across server restarts.
2. **Dynamic Trailing Take-Profit**: Once a position crosses the minimum net profit threshold (after fees), the bot tracks the `highest_price_seen`. It will not exit until the price pulls back by a configurable threshold (e.g., `0.2%`), capturing maximum upside on explosive runners rather than exiting early.
3. **Hard Floor Preservation (With Early Fee Cushion)**: Once a sniped position clears your Net Profit Hurdle, an unbreakable concrete floor locks into place at exactly `Target Net Profit + Fee Cushion`. The engine executes a market sell before tick slippage can breach the fee barrier, guaranteeing commissions never eat into principal.
4. **📉 Smart DCA (Dollar-Cost Averaging) Rescue**: If an active position suffers a steep drop (e.g., `-5.0%`), the engine does not panic sell. Instead, it checks the global order book for "Strong Momentum." If safe, it automatically doubles down, drastically lowering the average entry price so that even a minor bounce results in a highly profitable exit.
5. **Isolated Asset Silos**: Every coin operates in its own isolated execution thread (`agent:position:BTC/USDT`). P&L is tracked independently per asset, ensuring winners are liquidated at peak profit while consolidating assets remain untouched.
6. **Scratch Trade Accounting**: In portfolio win rate calculations, micro-exits between `-0.05%` and `0.00%` resulting from fee slippage on Hard Floor exits are classified as neutral break-even scratches rather than strategy losses.

### 🎯 The Action Recommendation Engine
The engine generates a live `Confidence Score (0-100%)` based on a confluence of rigid triggers:
1. **The Flow Gate (60% Weight):** Evaluates live trade streams to ensure `Buyer Taker Volume > Seller Taker Volume` (indicating strong retail buying pressure).
2. **The Liquidity Squeeze (40% Weight):** Evaluates Coinbase's Level-2 order book. Heavy Short Liquidity (Sell walls) compared to Long Liquidity (Buy walls) increases the probability of a violent short-squeeze.
3. **The Lagging Exchange Alpha (Bonus Confidence):** Scans all 8 exchanges simultaneously. If it spots a single exchange lagging behind the global market fair value median by `> 0.1%`, it flags that exchange as a tactical **Target Buy**.

---

## 🛠 Technology Stack

| Layer | Technology |
|---|---|
| **Backend API & WebSockets** | Python 3.12, FastAPI, `websockets`, `asyncio` |
| **Hot Cache (sub-ms state)** | Redis (via local Homebrew/Docker) |
| **Frontend UI** | React (Vite), Vanilla CSS (Dark Mode/Glassmorphism) |

*(Note: PostgreSQL and disk-bound SQL databases were intentionally removed to eliminate sector write latency and maximize HFT throughput).*

---

## 🚀 Getting Started

### Prerequisites
* Python 3.11+
* Node.js 18+
* Redis (`brew install redis` or via Docker)

### 1. Installation & Setup

Clone the repository and install the backend dependencies:
```bash
git clone https://github.com/CommonCapital/Ultra-Fast-Crypto-Quantitative-Execution-Engine.git
cd Ultra-Fast-Crypto-Quantitative-Execution-Engine

# Install Python dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Install Frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Environment Variables
Copy the example environment file:
```bash
cp .env.example .env
```
Ensure your `.env` contains:
```env
# Required for 24h Volume Metrics (Free Basic Tier)
CMC_API_KEY=your_coinmarketcap_api_key_here
```
*(Binance, Bybit, MEXC, BingX, Coinbase, OKX, HTX, and Bitunix public websockets do not require API keys).*

### 3. Run the Platform

**Start Redis:**
```bash
redis-server --daemonize yes
# or if using docker: docker run -d -p 6379:6379 redis
```

**Start the Backend Engine:**
```bash
# From the root project directory
source .venv/bin/activate
uvicorn backend.main:app --reload
```

**Start the Frontend Dashboard:**
```bash
cd frontend
npm run dev
```
Navigate to `http://localhost:5173` to view the live exchange matrix and real-time portfolio P&L banner!

---

## 🗺 Strategic Commercialization & Roadmap

### Phase 1: Proprietary Trading Desk (Current)
Deploy the platform with proprietary capital to leverage the exponential power of continuous high-frequency compounding. Establish an undeniable public track record showing verified win rates and net compounding P&L over thousands of live trades.

### Phase 2: Enterprise SaaS Pivot & AI Sandbox
Package the verified execution engine into a premium B2B / B2C financial technology SaaS:
- [ ] **"Quant in a Box" B2C SaaS**: Allow retail traders to plug in their CEX API keys, configure custom Net Profit Targets and DCA rescue rules, and execute automated mean-reversion trading via monthly subscription tiers.
- [ ] **Marco Polo / Machine Learning Sandbox**: Integrate custom rule builders, XGBoost / LightGBM sentiment scoring pipelines, and ultra-fast historical order book simulation/backtesting environments for institutional quants.
- [ ] **Dynamic VIP Fee API**: Transition from static exchange fee tables to live account-specific API queries, accounting for VIP trading volume tiers and token-holding fee discounts (e.g., holding BNB or KCS).
- [ ] **On-Chain DEX Expansion**: Expand WebSocket collectors to include decentralized liquidity pools (Uniswap v3, Raydium CLMM) to capture cross-chain CEX/DEX arbitrage spreads.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! 
1. Fork the project.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

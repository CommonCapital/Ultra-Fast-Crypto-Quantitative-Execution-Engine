# 📈 Ultra-Fast Crypto Quantitative Execution Engine

A high-performance, in-memory cryptocurrency quantitative analysis and high-frequency execution platform. 

Unlike traditional polling bots, AI wrappers, or heavy database-bound applications, this platform is optimized strictly for **sub-millisecond velocity** and **deterministic mathematical execution**. It opens persistent WebSocket connections to major exchanges, slurps live tick data and Order Book Level-2 depth directly into a Redis hot-cache, and evaluates multi-venue momentum in 500-microsecond cycles. 

When high-conviction dislocations are detected that pass strict fee-adjusted profitability thresholds, the Quantitative Execution Algorithm dispatches tactical signals directly to your Terminal and a sleek React Dashboard, ready for automated millisecond execution.

---

## ✨ Core Features

* **RAM-Only Architecture**: Zero database overhead. Data is streamed via WebSockets directly into a local Redis cache for blazing-fast read/write cycles.
* **100% Real-Time Data**: Live feeds from Binance, Bybit, MEXC, BingX, Coinbase, OKX, and BitMEX.
* **Strict Mathematical Execution**:
  * **Compound Net Profit**: Calculates exact capital returns by deducting both the *Taker Buy Fee* and *Taker Sell Fee* specifically for the two exchanges involved in the spread. Guarantees a rigid minimum net profit (e.g., `0.5%`) after all slippage and commissions.
  * **Clear Growth Momentum**: Evaluates live Binance trade streams to ensure `Recent Buy Volume > Recent Sell Volume` before firing an alert.
  * **Real-Time L2 Liquidity Squeeze**: Evaluates the live Coinbase Level-2 order book dynamically, comparing the total dollar value of the Sell Liquidity pool against the Buy Liquidity pool to ensure upward price pressure.
* **Global Macro Context**: Enriches alerts by fetching the real-time **Fear & Greed Index** (via Alternative.me) and **Global 24h Volume** (via CoinMarketCap API). *Note: CMC is queried exactly once every 5 minutes to guarantee it stays 100% free under their 10,000 credit/month limit.*
* **Premium Dashboard**: A beautifully designed, glassmorphic React/Vite dashboard running on vanilla CSS to monitor the live Exchange Matrix and Terminal-style alert logs.

---

## 🧠 Quantitative Algorithmic Strategy (No LLMs)

While the engine detects pure arbitrage (buying on Exchange A and selling on Exchange B), it is strategically engineered for **Multi-Venue Signal Aggregation for Single-Venue Execution**. 

This is strictly a **Deterministic Quantitative Algorithm**. It operates entirely on hard-coded mathematical logic, order book physics, and statistical probability. There are no black-box LLMs, unpredictable generative wrappers, or sentiment hallucinations involved in execution.

The **Action Recommendation Engine** generates a live `Confidence Score (0-100%)` based on a confluence of rigid triggers:
1. **The Flow Gate (60% Weight):** Evaluates Binance's live trade streams to ensure `Buyer Taker Volume > Seller Taker Volume` (indicating strong retail buying pressure).
2. **The Liquidity Squeeze (40% Weight):** Evaluates Coinbase's Level-2 order book. Heavy Short Liquidity (Sell walls) compared to Long Liquidity (Buy walls) increases the probability of a violent short-squeeze.
3. **The Lagging Exchange Alpha (Bonus Confidence):** Scans all 7 exchanges simultaneously. If it spots a single exchange lagging behind the global market maximum price by `> 0.1%`, it flags that exchange as a tactical **Target Buy**, anticipating a rapid price-snap to catch up to the aggregate market.

### ⚡ Automated Millisecond Execution Mandate

When transitioned to automated execution mode via authenticated `ccxt` API connectors, the algorithm strictly adheres to the following high-frequency execution protocol:
* **Sub-Millisecond Entry**: Execute a Market Buy on a specific exchange within ~5 to 15 milliseconds *only* when the aggregate Recommendation is `BUY` or `STRONG BUY` **and** that exchange is trading at a lagging price discount of **>= 5%** compared to the global market top price.
* **The Spot No-Loss Mandate**: All executions occur strictly on Spot markets (zero leverage, zero liquidation risk). Once an asset is acquired at a lagging discount, the algorithm calculates the exact break-even price (Execution Price + Taker Fees). The algorithm is mathematically hard-coded to never panic-sell or close at a loss during short-term volatility.
* **Cost-Basis Laddering (DCA)**: If an acquired position enters temporary drawdown (`<= -5%`) while the global multi-venue radar remains heavily bullish, the algorithm deploys secondary laddered buy orders to average down the cost basis, enabling profitable exits on minor mean-reversion bounces.
* **Macro Circuit Breakers**: The algorithm overrides the no-loss rule *only* under extreme black-swan conditions: if a coin experiences an isolated flash-crash `> 15%` or if the Global Fear & Greed Index violently collapses below 20 ("Extreme Fear"), the algorithm instantly cuts positions to preserve capital.
* **Algorithmic Take-Profit**: The algorithm deploys a dynamic trailing Take-Profit, waiting until the lagging exchange order book re-aligns with the global market to exit the position strictly in net profit.

---

## 🛠 Technology Stack

| Layer | Technology |
|---|---|
| **Backend API & WebSockets** | Python 3.12, FastAPI, `websockets`, `asyncio` |
| **Hot Cache (sub-ms state)** | Redis (via local Homebrew/Docker) |
| **Frontend UI** | React (Vite), Vanilla CSS (Dark Mode/Glassmorphism) |

*(Note: PostgreSQL was intentionally removed to minimize latency and infrastructure costs.)*

---

## 🚀 Getting Started

### Prerequisites
* Python 3.11+
* Node.js 18+
* Redis (`brew install redis` or via Docker)

### 1. Installation & Setup

Clone the repository and install the backend dependencies:
```bash
git clone https://github.com/yourusername/crypto-arbitrage-platform.git
cd crypto-arbitrage-platform

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
*(Binance, Bybit, MEXC, BingX, Coinbase, OKX, and BitMEX public websockets do not require API keys).*

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
Navigate to `http://localhost:5173` to view the live exchange matrix!

---

## 🗺 Future Plans & Roadmap

This MVP is currently optimized as a high-speed alerting system for manual discretionary trading. The architecture is explicitly designed to scale into a fully automated, quantitative fund-grade system:

- [ ] **Automated Single-Venue Execution**: Transition from alerting to automated execution using `ccxt`. The algorithm will place a Market Buy on the "Lagging Exchange" within milliseconds when Confidence is > 85%, and automatically deploy a dynamic trailing Take-Profit to sell once in profit (accounting for maker/taker fees).
- [ ] **Machine Learning Re-Integration**: Re-introduce XGBoost and LightGBM models as the final "AI Gate" to predict false-breakout probabilities using historical order-book imbalance data before any automated execution is permitted.
- [ ] **Telegram & DeepSeek Integration**: Re-connect API hooks to broadcast alerts dynamically to private Telegram channels using LLM-generated market narratives.
- [ ] **Dynamic Fee API**: Transition from hardcoded exchange fee structures (`0.1%`) to dynamic API queries, accounting for VIP tiers and token-holding fee discounts (e.g., holding BNB on Binance).
- [ ] **DEX Expansion**: Expand websocket collectors to include on-chain decentralized exchanges (Uniswap, Raydium) to catch CEX/DEX arbitrage gaps.

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
# Ultra-Fast-Crypto-Arbitrage-Engine
# Ultra-Fast-Crypto-Engine-with-Autonomous-Agent-Architecture
# Ultra-Fast-Crypto-Engine-with-Autonomous-Agent-Architecture

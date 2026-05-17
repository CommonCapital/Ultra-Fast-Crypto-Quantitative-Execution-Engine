# 📈 Ultra-Fast Crypto Quantitative Execution Engine

A high-performance, in-memory cryptocurrency quantitative analysis and high-frequency execution platform. 

Unlike traditional polling bots, AI wrappers, or heavy database-bound applications, this platform is optimized strictly for **sub-millisecond velocity** and **deterministic mathematical execution**. It opens persistent WebSocket connections to major exchanges, slurps live tick data and Order Book Level-2 depth directly into a Redis hot-cache, and evaluates multi-venue momentum in 500-microsecond cycles. 

When high-conviction dislocations are detected that pass strict fee-adjusted profitability thresholds, the Quantitative Execution Algorithm dispatches tactical signals directly to your Terminal and a sleek React Dashboard, and manages fully automated execution through advanced risk mechanics.

---

## ✨ Core Features

* **RAM-Only Architecture**: Zero database overhead. Data is streamed via WebSockets directly into a local Redis cache for blazing-fast read/write cycles.
* **100% Real-Time Data**: Live feeds from Binance, Bybit, MEXC, BingX, Coinbase, OKX, and BitMEX.
* **Strict Mathematical Execution**:
  * **Compound Net Profit**: Calculates exact capital returns by deducting both the *Taker Buy Fee* and *Taker Sell Fee* specifically for the two exchanges involved in the spread. Guarantees a rigid minimum net profit equal to your dynamic **Target Net Profit** after all slippage and commissions.
  * **Clear Growth Momentum**: Evaluates live Binance trade streams to ensure `Recent Buy Volume > Recent Sell Volume` before firing an alert.
  * **Real-Time L2 Liquidity Squeeze**: Evaluates the live Coinbase Level-2 order book dynamically, comparing the total dollar value of the Sell Liquidity pool against the Buy Liquidity pool to ensure upward price pressure.
* **Global Macro Context**: Enriches alerts by fetching the real-time **Fear & Greed Index** (via Alternative.me) and **Global 24h Volume** (via CoinMarketCap API). *Note: CMC is queried exactly once every 5 minutes to guarantee it stays 100% free under their 10,000 credit/month limit.*
* **Geopolitical & Macro News Sentiment**: Asynchronously parses public RSS feeds (CoinTelegraph, CoinDesk) every 60 seconds. Evaluates institutional NLP keyword weights (e.g. `war`, `sec lawsuit`, `etf approval`, `rate cut`) to maintain a real-time macro risk rating (-100 to +100).
* **Premium Dashboard**: A beautifully designed, glassmorphic React/Vite dashboard running on vanilla CSS to monitor the live Exchange Matrix and Terminal-style alert logs.

---

## 🧠 Quantitative Algorithmic Strategy & Execution

This engine relies strictly on hard-coded mathematical logic, order book physics, and statistical probability. There are no unpredictable generative wrappers or sentiment hallucinations involved in execution.

### 🛡️ Advanced Risk Management & Execution Mechanics
The bot manages live positions with institutional-grade risk models to ensure no-loss execution and capital preservation:
1. **Dynamic Trailing Take-Profit**: Once a position crosses the minimum net profit threshold (after fees), the bot tracks the `highest_price_seen`. It will not exit until the price pulls back by a configurable threshold (e.g., `0.2%`), capturing maximum upside on explosive pumps rather than hard-exiting early.
2. **📉 Smart DCA (Dollar-Cost Averaging) Rescue**: If an active position suffers a steep drop (e.g., `-5.0%`), the engine does not panic sell. Instead, it checks the global order book for "Strong Momentum." If it is safe, it automatically doubles down, drastically lowering the average entry price so that even a minor bounce results in a profitable exit.
3. **Algorithmic Position Sizing**: Positions scale automatically by volume multipliers (`1x`, `2x`, `3x`) based on the magnitude of the price dislocation and the global confidence score.
4. **Dynamic Configuration API**: Tweak all risk parameters—Net Profit Target, Trailing Pullback Threshold, and Smart DCA Drop Threshold—live from the frontend dashboard via FastAPI/Redis without ever restarting the backend.

### 🎯 The Action Recommendation Engine
The engine generates a live `Confidence Score (0-100%)` based on a confluence of rigid triggers:
1. **The Flow Gate (60% Weight):** Evaluates Binance's live trade streams to ensure `Buyer Taker Volume > Seller Taker Volume` (indicating strong retail buying pressure).
2. **The Liquidity Squeeze (40% Weight):** Evaluates Coinbase's Level-2 order book. Heavy Short Liquidity (Sell walls) compared to Long Liquidity (Buy walls) increases the probability of a violent short-squeeze.
3. **The Lagging Exchange Alpha (Bonus Confidence):** Scans all 7 exchanges simultaneously. If it spots a single exchange lagging behind the global market maximum price by `> 0.1%`, it flags that exchange as a tactical **Target Buy**.

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

- [x] **Advanced Automated Execution**: Trailing take-profits, algorithmic position sizing, and Smart DCA.
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

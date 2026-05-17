import asyncio
import json
import logging
from datetime import datetime, timezone
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import redis

# Internal modules
from .collectors.binance import start_binance_collector
from .collectors.bybit import start_bybit_collector
from .collectors.mexc import start_mexc_collector
from .collectors.bingx import start_bingx_collector
from .collectors.coinbase import start_coinbase_collector
from .collectors.okx import start_okx_collector
from .collectors.bitmex import start_bitmex_collector
from .collectors.news_sentiment import start_news_sentiment_collector
from .collectors.global_metrics import start_global_metrics_collector
from .engine.arbitrage import ArbitrageDetector
from .integrations.deepseek import generate_narrative
from .integrations.telegram import send_telegram_alert
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Shared state
active_connections = []
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
arb_detector = ArbitrageDetector()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def broadcast_loop():
    """Background task to broadcast state to WS clients and detect arbitrage."""
    cycle_counter = 0
    while True:
        cycle_counter += 1
        try:
            if True: # HFT engine runs continuously 24/7 in background
                # Fetch latest prices for pairs from Redis
                dashboard_data = []
                for pair in settings.PAIRS:
                    symbol = pair.replace('/', '')
                    prices = {}
                    for ex in ['Binance', 'Bybit', 'MEXC', 'BingX', 'Coinbase', 'OKX', 'BitMEX']:
                        raw_tick = redis_client.get(f"tick:{ex}:{symbol}")
                        if raw_tick:
                            prices[ex] = json.loads(raw_tick)
                    
                    if prices:
                        # --- Momentum & Lagging Engine ---
                        binance_data = prices.get('Binance', {})
                        buy_vol = binance_data.get('buy_vol', 0)
                        sell_vol = binance_data.get('sell_vol', 0)
                        vol_score = 50
                        if buy_vol + sell_vol > 0:
                            vol_score = (buy_vol / (buy_vol + sell_vol)) * 100
                            
                        coinbase_data = prices.get('Coinbase', {})
                        short_liq = coinbase_data.get('short_liq', 0)
                        long_liq = coinbase_data.get('long_liq', 0)
                        liq_score = 50
                        if short_liq + long_liq > 0:
                            # Higher short liq = higher probability of short squeeze = bullish
                            liq_score = (short_liq / (short_liq + long_liq)) * 100
                            
                        valid_prices = []
                        valid_exchanges_map = {}
                        for ex, d in prices.items():
                            p = d.get('price', 0)
                            b = d.get('bid', 0)
                            a = d.get('ask', 0)
                            if p > 0 and b > 0 and a > 0:
                                # Filter out illiquid venues where internal bid-ask spread is > 2%
                                internal_spread = (a - b) / b
                                if internal_spread <= 0.02:
                                    valid_prices.append(p)
                                    valid_exchanges_map[ex] = d
                                    
                        lagging_exchange = None
                        lagging_diff_pct = 0
                        cheapest_exchange = "N/A"
                        dearest_exchange = "N/A"
                        gross_spread_pct = 0.0
                        cheapest_status = "Fair Value"
                        dearest_status = "Fair Value"
                        
                        if len(valid_prices) >= 2:
                            max_p = max(valid_prices)
                            min_p = min(valid_prices)
                            sorted_p = sorted(valid_prices)
                            median_p = sorted_p[len(sorted_p)//2]
                            
                            gross_spread_pct = ((max_p - min_p) / min_p) * 100
                            
                            for ex, d in valid_exchanges_map.items():
                                if d.get('price') == min_p:
                                    lagging_exchange = ex
                                    cheapest_exchange = ex
                                    lagging_diff_pct = ((max_p - min_p) / min_p) * 100
                                elif d.get('price') == max_p:
                                    dearest_exchange = ex
                                    
                            if median_p > 0:
                                cheapest_diff = ((min_p - median_p) / median_p) * 100
                                dearest_diff = ((max_p - median_p) / median_p) * 100
                                
                                if cheapest_diff <= -0.7:
                                    cheapest_status = f"Underpriced (-{abs(round(cheapest_diff, 2))}%)"
                                else:
                                    cheapest_status = "Fair Value"
                                    
                                if dearest_diff >= 0.7:
                                    dearest_status = f"Overpriced (+{round(dearest_diff, 2)}%)"
                                else:
                                    dearest_status = "Fair Value"
                                    
                            # Tracking Underpriced Mean Reversion (Alpha Snap)
                            snap_growth_pct = 0.0
                            if cheapest_exchange and cheapest_exchange != "N/A":
                                track_key = f"track:underpriced:{pair}:{cheapest_exchange}"
                                cached_track = redis_client.get(track_key)
                                current_min_p = min_p
                                
                                if cached_track:
                                    track_data = json.loads(cached_track)
                                    start_p = track_data["start_price"]
                                    
                                    if current_min_p > start_p:
                                        snap_growth_pct = ((current_min_p - start_p) / start_p) * 100
                                        
                                    if current_min_p >= median_p:
                                        redis_client.delete(track_key)
                                elif cheapest_diff < -0.1: # Underpriced by > 0.1% vs median
                                    redis_client.set(track_key, json.dumps({
                                        "ts": datetime.now(timezone.utc).isoformat(),
                                        "start_price": current_min_p,
                                        "start_median": median_p
                                    }), ex=300)
                                    
                        confidence = (vol_score * 0.6) + (liq_score * 0.4)
                        if lagging_diff_pct > 0.1:
                            confidence += min(15, lagging_diff_pct * 10)
                            
                        confidence = min(100, max(0, confidence))
                        
                        recommendation = "NEUTRAL"
                        if confidence >= 65:
                            recommendation = "STRONG BUY"
                        elif confidence >= 55:
                            recommendation = "BUY"
                        elif confidence <= 35:
                            recommendation = "STRONG SELL"
                        elif confidence <= 45:
                            recommendation = "SELL"
                            
                        signal_data = {
                            "confidence": round(confidence, 1),
                            "recommendation": recommendation,
                            "lagging_exchange": lagging_exchange if lagging_diff_pct > 0.1 else None,
                            "lagging_diff": round(lagging_diff_pct, 2),
                            "gross_spread_pct": round(gross_spread_pct, 2),
                            "cheapest_exchange": cheapest_exchange,
                            "cheapest_status": cheapest_status,
                            "dearest_exchange": dearest_exchange,
                            "dearest_status": dearest_status,
                            "mean_reversion_growth": round(snap_growth_pct, 2)
                        }

                        dashboard_data.append({
                            "pair": pair,
                            "prices": prices,
                            "signals": signal_data
                        })
                        
                        # Arbitrage check
                        opp = arb_detector.check_opportunity(pair, prices)
                        if opp:
                            # Cooldown check logic (Redis-based)
                            cooldown_key = f"cooldown:{pair}"
                            if not redis_client.get(cooldown_key):
                                logger.info(f"Arbitrage detected: {opp}")
                                
                                # Local MVP Alert Narrative (No DeepSeek/Telegram)
                                short_liq = opp.get('cb_short_liq', 0)
                                long_liq = opp.get('cb_long_liq', 0)
                                liq_diff = short_liq - long_liq
                                
                                # Pull Global Metrics
                                fng_data_str = redis_client.get("global:fng")
                                fng_str = "N/A"
                                if fng_data_str:
                                    fng = json.loads(fng_data_str)
                                    fng_str = f"{fng.get('value')} ({fng.get('class')})"
                                    
                                base_sym = symbol.replace('USDT', '')
                                cmc_vol_str = redis_client.get(f"global:cmc_vol:{base_sym}")
                                cmc_vol = "N/A"
                                if cmc_vol_str:
                                    cmc_data = json.loads(cmc_vol_str)
                                    cmc_vol = f"${cmc_data.get('volume_24h', 0):,.0f}"
                                
                                narrative = (
                                    f"🚨 LOCAL ALERT: {pair}\n"
                                    f"📈 Net Spread (Post-Fees): {opp['spread_pct']}%\n"
                                    f"🛒 Buy on {opp['buy_exchange']} at ${opp['buy_price']}\n"
                                    f"💰 Sell on {opp['sell_exchange']} at ${opp['sell_price']}\n"
                                    f"📊 Momentum: Buy Vol {round(opp.get('buy_vol', 0), 2)} | Sell Vol {round(opp.get('sell_vol', 0), 2)}\n"
                                    f"💧 Coinbase Liq Pool: Sell {round(short_liq, 2)} - Buy {round(long_liq, 2)} (Diff: +{round(liq_diff, 2)})\n"
                                    f"🌍 Global Metrics: F&G {fng_str} | CMC 24h Vol: {cmc_vol}"
                                )
                                print("\n" + "="*40)
                                print(narrative)
                                print("="*40 + "\n")
                                
                                redis_client.setex(cooldown_key, 300, "1") # 5 min cooldown
                                opp["alert_message"] = narrative
                                dashboard_data[-1]["opportunity"] = opp
                        
                        # Dynamic Exchange Taker Fee & Net Profit Calculation for Single-Venue Alpha Sniper
                        exchange_taker_fee_pct = settings.EXCHANGE_FEES.get(cheapest_exchange, 0.001) * 100
                        round_trip_fee_pct = exchange_taker_fee_pct * 2
                        required_gross_discount = settings.MIN_NET_SPREAD + round_trip_fee_pct
                        
                        if not opp and recommendation in ["BUY", "STRONG BUY"] and lagging_diff_pct >= required_gross_discount and cheapest_status.startswith("Underpriced"):
                            cooldown_key = f"cooldown_lag:{pair}"
                            if not redis_client.get(cooldown_key):
                                narrative = (
                                    f"🚀 AUTONOMOUS SNIPER ALERT (Single-Venue Mean Reversion): {pair}\n"
                                    f"⚡ Execution Signal: {recommendation} ({round(confidence)}% Orderbook Confidence)\n"
                                    f"🎯 Target Entry Venue: {cheapest_exchange} at {cheapest_status} discount\n"
                                    f"📊 Fee Structure: {round(exchange_taker_fee_pct, 2)}% taker fee per trade ({round(round_trip_fee_pct, 2)}% round-trip drag)\n"
                                    f"📈 Execution Gate: -{round(required_gross_discount, 2)}% minimum gross discount required to guarantee >= {settings.MIN_NET_SPREAD}% net bottom-line profit.\n"
                                    f"💰 Status: Dislocation (-{round(lagging_diff_pct, 2)}%) successfully passed net profit gate! Immediate sniper entry triggered."
                                )
                                logger.info(f"Lagging Execution Signal: {narrative}")
                                print("\n" + "="*40)
                                print(narrative)
                                print("="*40 + "\n")
                                
                                tactical_opp = {
                                    "spread_pct": round(lagging_diff_pct, 2),
                                    "buy_exchange": lagging_exchange,
                                    "buy_price": min_p,
                                    "sell_exchange": "Global Top",
                                    "sell_price": max_p,
                                    "alert_message": narrative
                                }
                                redis_client.setex(cooldown_key, 60, "1") # 60 sec cooldown for lagging alerts
                                dashboard_data[-1]["opportunity"] = tactical_opp
                
                # Broadcast
                fng_data_str = redis_client.get("global:fng")
                fng = json.loads(fng_data_str) if fng_data_str else None
                
                macro_data_str = redis_client.get("global:macro_sentiment")
                macro_data = json.loads(macro_data_str) if macro_data_str else None
                
                now_utc = datetime.now(timezone.utc)
                utc_hour = now_utc.hour
                utc_day = now_utc.weekday()
                
                if utc_day >= 5:
                    session_name = "🔴 Weekend / Pre-Asia Twilight"
                    session_status = "Low Volume & Liquidity Regime"
                elif 0 <= utc_hour < 8:
                    session_name = "🟡 Tokyo / Hong Kong Session"
                    session_status = "Active Asian Liquidity"
                elif 8 <= utc_hour < 13:
                    session_name = "🟢 London / European Session"
                    session_status = "Peak Core Liquidity"
                elif 13 <= utc_hour < 17:
                    session_name = "🔵 NY / London Overlap (The Golden Window)"
                    session_status = "Maximum Global Volatility & Volume"
                elif 17 <= utc_hour < 21:
                    session_name = "🟣 New York Afternoon Session"
                    session_status = "US Institutional Flow"
                else:
                    session_name = "⚪ Post-NY Twilight"
                    session_status = "Algorithmic Rebalancing Window"
                    
                session_data = {
                    "name": session_name,
                    "status": session_status,
                    "utc_time": now_utc.strftime("%H:%M UTC")
                }
                
                if active_connections and cycle_counter % 5 == 0:
                    for conn in active_connections:
                        await conn.send_json({
                            "type": "update", 
                            "data": dashboard_data,
                            "global": {"fng": fng, "macro": macro_data, "market_session": session_data}
                        })
                    
        except Exception as e:
            logger.error(f"Broadcast loop error: {e}")
            
        await asyncio.sleep(0.05) # 50ms HFT execution cycle (20 checks per second!)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Crypto Arbitrage Platform MVP...")
    
    # Start background tasks
    asyncio.create_task(broadcast_loop())
    
    # Start collectors
    asyncio.create_task(start_binance_collector(redis_client, settings.PAIRS))
    asyncio.create_task(start_bybit_collector(redis_client, settings.PAIRS))
    asyncio.create_task(start_mexc_collector(redis_client, settings.PAIRS))
    asyncio.create_task(start_bingx_collector(redis_client, settings.PAIRS))
    asyncio.create_task(start_coinbase_collector(redis_client, settings.PAIRS))
    asyncio.create_task(start_okx_collector(redis_client, settings.PAIRS))
    asyncio.create_task(start_bitmex_collector(redis_client, settings.PAIRS))
    asyncio.create_task(start_news_sentiment_collector(redis_client, settings.PAIRS))
    asyncio.create_task(start_global_metrics_collector(redis_client, settings.PAIRS))

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")
    redis_client.close()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

@app.get("/health")
def health_check():
    return {"status": "ok"}

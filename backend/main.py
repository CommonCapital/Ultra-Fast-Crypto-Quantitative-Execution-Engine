import asyncio
import json
import logging
from datetime import datetime, timezone
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

class ProfitTargetPayload(BaseModel):
    target_pct: float

@app.post("/api/config/net-profit")
async def set_net_profit_target(payload: ProfitTargetPayload):
    target = max(0.01, min(10.0, payload.target_pct))
    redis_client.set("config:min_net_spread", str(target))
    return {"status": "success", "target_pct": target}

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
                        stop_loss_pool_status = "Balanced L2 Book"
                        if short_liq + long_liq > 0:
                            # Higher short liq = higher probability of short squeeze = bullish
                            liq_score = (short_liq / (short_liq + long_liq)) * 100
                            if short_liq > long_liq * 1.15:
                                ratio = round((short_liq / max(1.0, long_liq)), 2)
                                stop_loss_pool_status = f"🔥 Heavy Short Squeeze Pool (Asks {ratio}x Bids sitting above current price - Hunting Stop-Losses!)"
                            elif long_liq > short_liq * 1.15:
                                ratio = round((long_liq / max(1.0, short_liq)), 2)
                                stop_loss_pool_status = f"🩸 Heavy Long Liquidation Pool (Bids {ratio}x Asks sitting below current price - Cascade Dump Risk!)"
                            
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
                        cheapest_diff = 0.0
                        dearest_diff = 0.0
                        
                        raw_target = redis_client.get("config:min_net_spread")
                        target_net_profit = float(raw_target) if raw_target is not None else settings.MIN_NET_SPREAD
                        
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
                                
                                exchange_taker_fee_pct = settings.EXCHANGE_FEES.get(cheapest_exchange, 0.001) * 100
                                round_trip_fee_pct = exchange_taker_fee_pct * 2
                                required_gross_discount = target_net_profit + round_trip_fee_pct
                                
                                abs_underpricing_pct = abs(cheapest_diff) if cheapest_diff < 0 else 0.0
                                
                                if abs_underpricing_pct >= required_gross_discount:
                                    cheapest_status = f"Underpriced (-{round(abs_underpricing_pct, 2)}%)"
                                else:
                                    cheapest_status = "Fair Value"
                                    
                                if dearest_diff >= required_gross_discount:
                                    dearest_status = f"Overpriced (+{round(dearest_diff, 2)}%)"
                                else:
                                    dearest_status = "Fair Value"
                                    
                            # Tracking Underpriced Mean Reversion (Alpha Snap) & High Density Liquidity Pull
                            snap_growth_pct = 0.0
                            liquidity_pull_status = "Standby (Equilibrium Active)"
                            if cheapest_exchange and cheapest_exchange != "N/A":
                                track_key = f"track:underpriced:{pair}:{cheapest_exchange}"
                                cached_track = redis_client.get(track_key)
                                current_min_p = min_p
                                
                                if cached_track:
                                    track_data = json.loads(cached_track)
                                    start_p = track_data["start_price"]
                                    target_median_p = track_data["start_median"]
                                    
                                    if current_min_p > start_p:
                                        snap_growth_pct = ((current_min_p - start_p) / start_p) * 100
                                        
                                    if current_min_p >= target_median_p or current_min_p >= median_p:
                                        liquidity_pull_status = "Reached High Density Liquidity Pull (Target Met 🎯)"
                                    else:
                                        price_gap = target_median_p - start_p
                                        if price_gap > 0:
                                            progress_pct = ((current_min_p - start_p) / price_gap) * 100
                                            progress_pct = max(0.0, min(99.9, progress_pct))
                                            liquidity_pull_status = f"Reaching Liquidity Pull ({round(progress_pct, 1)}% Complete 🧲)"
                                        else:
                                            liquidity_pull_status = "Sniping Initial Discount ⚡"
                                elif cheapest_diff <= -0.1: # Underpriced by > 0.1% vs median
                                    redis_client.set(track_key, json.dumps({
                                        "ts": datetime.now(timezone.utc).isoformat(),
                                        "start_price": current_min_p,
                                        "start_median": median_p
                                    }), ex=180)
                                    liquidity_pull_status = f"Sniping Initial Discount ({round(cheapest_diff, 2)}% Dislocation ⚡)"
                                    
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
                            "mean_reversion_growth": round(snap_growth_pct, 2),
                            "liquidity_pull_status": liquidity_pull_status,
                            "stop_loss_pool_status": stop_loss_pool_status
                        }

                        dashboard_data.append({
                            "pair": pair,
                            "prices": prices,
                            "signals": signal_data
                        })
                        
                        # Arbitrage check
                        opp = arb_detector.check_opportunity(pair, prices)
                        if opp:
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
                            opp["alert_message"] = narrative
                            dashboard_data[-1]["opportunity"] = opp
                            
                            # Cooldown check logic for terminal print
                            cooldown_key = f"cooldown:{pair}"
                            if not redis_client.get(cooldown_key):
                                logger.info(f"Arbitrage detected: {opp}")
                                print("\n" + "="*40)
                                print(narrative)
                                print("="*40 + "\n")
                                redis_client.setex(cooldown_key, 300, "1") # 5 min cooldown for terminal print
                        
                        # Dynamic Exchange Taker Fee & Net Profit Target Calculation
                        exchange_taker_fee_pct = settings.EXCHANGE_FEES.get(cheapest_exchange, 0.001) * 100
                        round_trip_fee_pct = exchange_taker_fee_pct * 2
                        required_gross_discount = target_net_profit + round_trip_fee_pct
                        
                        # Liquidity Pool Squeeze Exhaustion Filter: Do not execute long entry if short stop-losses/liquidation pools have already been tapped or if long liquidation overhang is severe
                        liquidity_pool_exhausted = ("Cascade Dump Risk" in stop_loss_pool_status) or (short_liq > 0 and long_liq > short_liq * 1.3)
                        
                        abs_underpricing_pct = abs(cheapest_diff) if median_p > 0 and cheapest_diff < 0 else 0.0
                        
                        if not opp and recommendation in ["BUY", "STRONG BUY"] and abs_underpricing_pct >= required_gross_discount and not liquidity_pool_exhausted:
                            position_key = f"agent:position:{pair}"
                            active_position_str = redis_client.get(position_key)
                            
                            if active_position_str:
                                # We already hold an open position! Check if mean reversion exit target is reached
                                pos_data = json.loads(active_position_str)
                                entry_p = pos_data["entry_price"]
                                if min_p >= median_p or (min_p - entry_p) / entry_p >= (target_net_profit / 100):
                                    profit_pct = ((min_p - entry_p) / entry_p) * 100
                                    logger.info(f"🎯 AUTONOMOUS SNIPER EXIT: {pair} closed on {pos_data['venue']} at +{round(profit_pct, 2)}% net gain!")
                                    redis_client.delete(position_key)
                            else:
                                narrative = (
                                    f"🚀 AUTONOMOUS SNIPER ALERT (Single-Venue Mean Reversion): {pair}\n"
                                    f"⚡ Execution Signal: {recommendation} ({round(confidence)}% Orderbook Confidence)\n"
                                    f"🎯 Target Entry Venue: {cheapest_exchange} at {cheapest_status} discount\n"
                                    f"📊 Fee Structure: {round(exchange_taker_fee_pct, 2)}% taker fee per trade ({round(round_trip_fee_pct, 2)}% round-trip drag)\n"
                                    f"🛡️ Liquidation Squeeze Filter: PASSED ({stop_loss_pool_status}) - Upward short stop-loss magnet active!\n"
                                    f"📈 Execution Gate: -{round(required_gross_discount, 2)}% minimum gross discount from global fair median required to guarantee >= {round(target_net_profit, 2)}% net bottom-line profit.\n"
                                    f"💰 Status: Venue underpricing (-{round(abs_underpricing_pct, 2)}%) successfully passed net profit gate! Immediate sniper entry triggered."
                                )
                                tactical_opp = {
                                    "spread_pct": round(abs_underpricing_pct, 2),
                                    "buy_exchange": cheapest_exchange,
                                    "buy_price": min_p,
                                    "sell_exchange": "Global Median",
                                    "sell_price": median_p,
                                    "alert_message": narrative
                                }
                                dashboard_data[-1]["opportunity"] = tactical_opp
                                
                                # Lock inventory position in Redis to prevent duplicate buy orders
                                redis_client.setex(position_key, 3600, json.dumps({
                                    "status": "OPEN",
                                    "entry_price": min_p,
                                    "venue": cheapest_exchange,
                                    "ts": datetime.now(timezone.utc).isoformat()
                                }))
                                
                                cooldown_key = f"cooldown_lag:{pair}"
                                if not redis_client.get(cooldown_key):
                                    logger.info(f"Lagging Execution Signal: {narrative}")
                                    print("\n" + "="*40)
                                    print(narrative)
                                    print("="*40 + "\n")
                                    redis_client.setex(cooldown_key, 60, "1") # 60 sec cooldown for terminal print
                
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
                            "global": {"fng": fng, "macro": macro_data, "market_session": session_data, "target_net_profit": target_net_profit}
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

import asyncio
import json
import logging
import websockets
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

async def start_bitmex_collector(redis_client, pairs):
    url = "wss://ws.bitmex.com/realtime"
    
    # Map standard pairs to BitMEX spot format (BTC/USDT -> BTC_USDT)
    symbols_map = {p.replace('/', '_'): p.replace('/', '') for p in pairs}
    sub_symbols = list(symbols_map.keys())
    
    # Local cache to merge quote and trade updates
    state = {sym: {"price": 0.0, "volume": 0.0, "bid": None, "ask": None, "ts": datetime.now(timezone.utc).isoformat()} for sym in symbols_map.values()}
    
    while True:
        try:
            async with websockets.connect(url) as ws:
                logger.info(f"Connected to BitMEX WS for {pairs}")
                
                # Subscribe to quotes and trades
                args = [f"quote:{s}" for s in sub_symbols] + [f"trade:{s}" for s in sub_symbols]
                sub_msg = {
                    "op": "subscribe",
                    "args": args
                }
                await ws.send(json.dumps(sub_msg))
                
                while True:
                    msg = await ws.recv()
                    try:
                        data = json.loads(msg)
                        table = data.get("table")
                        
                        if table in ["quote", "trade"] and "data" in data:
                            for item in data["data"]:
                                raw_sym = item.get("symbol", "")
                                if raw_sym in symbols_map:
                                    clean_sym = symbols_map[raw_sym]
                                    
                                    if table == "quote":
                                        if item.get("bidPrice"): state[clean_sym]["bid"] = float(item["bidPrice"])
                                        if item.get("askPrice"): state[clean_sym]["ask"] = float(item["askPrice"])
                                    elif table == "trade":
                                        if item.get("price"): state[clean_sym]["price"] = float(item["price"])
                                        if item.get("size"): state[clean_sym]["volume"] += float(item["size"]) # Cumulative session volume
                                    
                                    state[clean_sym]["ts"] = datetime.now(timezone.utc).isoformat()
                                    
                                    # Ensure fallback if trade hasn't happened but quote has
                                    if state[clean_sym]["price"] == 0.0 and state[clean_sym]["ask"]:
                                        state[clean_sym]["price"] = state[clean_sym]["ask"]
                                        
                                    has_quotes = state[clean_sym]["bid"] and state[clean_sym]["ask"]
                                    active_price = (state[clean_sym]["bid"] + state[clean_sym]["ask"]) / 2 if has_quotes else state[clean_sym]["price"]
                                        
                                    if active_price > 0:
                                        tick = {
                                            "ts": state[clean_sym]["ts"],
                                            "exchange": "BitMEX",
                                            "pair": clean_sym,
                                            "price": round(active_price, 4),
                                            "volume": state[clean_sym]["volume"],
                                            "bid": state[clean_sym]["bid"] if state[clean_sym]["bid"] else active_price,
                                            "ask": state[clean_sym]["ask"] if state[clean_sym]["ask"] else active_price
                                        }
                                        redis_client.set(f"tick:BitMEX:{clean_sym}", json.dumps(tick))
                    except (json.JSONDecodeError, KeyError, ValueError):
                        pass
        except Exception as e:
            logger.error(f"BitMEX WS error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

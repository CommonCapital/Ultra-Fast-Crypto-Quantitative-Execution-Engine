import asyncio
import json
import logging
import websockets
import re
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

async def start_mexc_collector(redis_client, pairs):
    url = "wss://wbs-api.mexc.com/ws"

    while True:
        try:
            async with websockets.connect(url) as ws:
                logger.info(f"Connected to MEXC WS for {pairs}")
                
                symbols = [p.replace('/', '') for p in pairs]
                sub_msg = {
                    "method": "SUBSCRIPTION",
                    "params": [f"spot@public.aggre.bookTicker.v3.api.pb@100ms@{s}" for s in symbols]
                }
                await ws.send(json.dumps(sub_msg))

                while True:
                    msg = await ws.recv()
                    
                    if isinstance(msg, bytes):
                        s = msg.decode('ascii', errors='ignore')
                        if "bookTicker" in s:
                            symbol = next((sym for sym in symbols if sym in s), None)
                            if symbol:
                                matches = re.findall(r'\d+\.\d+', s)
                                if len(matches) >= 4:
                                    bid_price = float(matches[0])
                                    ask_price = float(matches[2])
                                    tick = {
                                        "ts": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
                                        "exchange": "MEXC",
                                        "pair": symbol,
                                        "price": ask_price, # approximate last via ask
                                        "volume": 0, 
                                        "bid": bid_price,
                                        "ask": ask_price
                                    }
                                    redis_client.set(f"tick:MEXC:{symbol}", json.dumps(tick))
                    else:
                        # Handle json ping/pong if any
                        try:
                            data = json.loads(msg)
                            if data.get("ping"):
                                await ws.send(json.dumps({"pong": data["ping"]}))
                        except:
                            pass
                        
        except Exception as e:
            logger.error(f"MEXC WS error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

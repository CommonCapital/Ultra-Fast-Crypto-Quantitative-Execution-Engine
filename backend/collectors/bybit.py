import asyncio
import json
import logging
import websockets
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

async def start_bybit_collector(redis_client, pairs):
    url = "wss://stream.bybit.com/v5/public/spot"

    while True:
        try:
            async with websockets.connect(url) as ws:
                logger.info(f"Connected to Bybit WS for {pairs}")
                
                # Subscribe to tickers
                symbols = [p.replace('/', '') for p in pairs]
                sub_msg = {
                    "op": "subscribe",
                    "args": [f"tickers.{s}" for s in symbols]
                }
                await ws.send(json.dumps(sub_msg))

                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    
                    if 'topic' in data and data['topic'].startswith('tickers'):
                        symbol = data['data']['symbol']
                        tick = {
                            "ts": datetime.fromtimestamp(data['ts']/1000, tz=timezone.utc).isoformat(),
                            "exchange": "Bybit",
                            "pair": symbol,
                            "price": float(data['data'].get('lastPrice', 0)),
                            "volume": float(data['data'].get('volume24h', 0)),
                            "bid": float(data['data'].get('bid1Price', 0)),
                            "ask": float(data['data'].get('ask1Price', 0))
                        }
                        redis_client.set(f"tick:Bybit:{symbol}", json.dumps(tick))
                        
        except Exception as e:
            logger.error(f"Bybit WS error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

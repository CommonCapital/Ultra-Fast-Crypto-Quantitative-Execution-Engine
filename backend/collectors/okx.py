import asyncio
import json
import logging
import websockets
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

async def start_okx_collector(redis_client, pairs):
    url = "wss://ws.okx.com:8443/ws/v5/public"
    
    # Map standard pairs to OKX format (BTC/USDT -> BTC-USDT)
    inst_ids = [p.replace('/', '-') for p in pairs]
    
    while True:
        try:
            async with websockets.connect(url) as ws:
                logger.info(f"Connected to OKX WS for {pairs}")
                
                # Subscribe
                sub_args = [{"channel": "tickers", "instId": inst_id} for inst_id in inst_ids]
                sub_msg = {
                    "op": "subscribe",
                    "args": sub_args
                }
                await ws.send(json.dumps(sub_msg))
                
                while True:
                    msg = await ws.recv()
                    try:
                        data = json.loads(msg)
                        
                        if 'data' in data and 'arg' in data and data['arg'].get('channel') == 'tickers':
                            for tick_item in data['data']:
                                # OKX instId BTC-USDT -> BTCUSDT
                                symbol = tick_item['instId'].replace('-', '')
                                
                                tick = {
                                    "ts": datetime.fromtimestamp(int(tick_item['ts'])/1000, tz=timezone.utc).isoformat(),
                                    "exchange": "OKX",
                                    "pair": symbol,
                                    "price": float(tick_item['last']),
                                    "volume": float(tick_item['vol24h']),
                                    "bid": float(tick_item['bidPx']) if tick_item.get('bidPx') else float(tick_item['last']),
                                    "ask": float(tick_item['askPx']) if tick_item.get('askPx') else float(tick_item['last'])
                                }
                                redis_client.set(f"tick:OKX:{symbol}", json.dumps(tick))
                    except (json.JSONDecodeError, KeyError, ValueError):
                        pass
        except Exception as e:
            logger.error(f"OKX WS error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

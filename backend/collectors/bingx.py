import asyncio
import json
import logging
import websockets
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

async def start_bingx_collector(redis_client, pairs):
    # BingX open-api-ws
    url = "wss://open-api-ws.bingx.com/market"

    while True:
        try:
            async with websockets.connect(url) as ws:
                logger.info(f"Connected to BingX WS for {pairs}")
                
                symbols = [p.replace('/', '-') for p in pairs]
                for s in symbols:
                    sub_msg = {
                        "id": f"sub_{s}",
                        "reqType": "sub",
                        "dataType": f"{s}@ticker"
                    }
                    await ws.send(json.dumps(sub_msg))

                while True:
                    msg = await ws.recv()
                    
                    # BingX returns compressed gzip binary data over WebSockets
                    if isinstance(msg, bytes):
                        import gzip
                        try:
                            msg = gzip.decompress(msg).decode('utf-8')
                        except Exception:
                            continue
                            
                    try:
                        data = json.loads(msg)
                        
                        # Respond to ping to keep connection alive
                        if data.get("ping"):
                            await ws.send(json.dumps({"pong": data["ping"]}))
                            continue
                            
                        if 'dataType' in data and 'ticker' in data['dataType']:
                            symbol = data['dataType'].split('@')[0].replace('-', '')
                            tick_data = data['data']
                            tick = {
                                "ts": datetime.fromtimestamp(tick_data['E']/1000, tz=timezone.utc).isoformat(),
                                "exchange": "BingX",
                                "pair": symbol,
                                "price": float(tick_data['c']),
                                "volume": float(tick_data['v']),
                                "bid": float(tick_data['B']),
                                "ask": float(tick_data['A'])
                            }
                            redis_client.set(f"tick:BingX:{symbol}", json.dumps(tick))
                    except json.JSONDecodeError:
                        pass
                        
        except Exception as e:
            logger.error(f"BingX WS error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

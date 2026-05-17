import asyncio
import json
import logging
import websockets
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

async def start_binance_collector(redis_client, pairs):
    url = "wss://stream.binance.com:9443/ws"
    # Create stream names for trade and ticker
    streams = []
    for p in pairs:
        symbol = p.replace('/', '').lower()
        streams.extend([f"{symbol}@trade", f"{symbol}@ticker"])
    
    stream_url = f"{url}/{'/'.join(streams)}"

    # Track recent volume for MVP momentum logic
    recent_volumes = {p.replace('/', '').replace('-', '').upper(): {'buy': 0.0, 'sell': 0.0} for p in pairs}

    while True:
        try:
            async with websockets.connect(stream_url) as ws:
                logger.info(f"Connected to Binance WS for {pairs}")
                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    
                    if 'e' in data:
                        event_type = data['e']
                        symbol = data['s']
                        
                        if event_type == 'trade':
                            vol = float(data['q'])
                            is_buyer_maker = data['m']
                            
                            if is_buyer_maker:
                                recent_volumes[symbol]['sell'] += vol
                            else:
                                recent_volumes[symbol]['buy'] += vol
                                
                            # Simple decay mechanism to approximate a rolling window
                            recent_volumes[symbol]['sell'] *= 0.999
                            recent_volumes[symbol]['buy'] *= 0.999
                            
                            tick = {
                                "ts": datetime.fromtimestamp(data['E']/1000, tz=timezone.utc).isoformat(),
                                "exchange": "Binance",
                                "pair": symbol,
                                "price": float(data['p']),
                                "volume": vol,
                                "buy_vol": recent_volumes[symbol]['buy'],
                                "sell_vol": recent_volumes[symbol]['sell'],
                                "bid": None,
                                "ask": None
                            }
                            # Send to Redis
                            redis_client.set(f"tick:Binance:{symbol}", json.dumps(tick))
                            
                        elif event_type == '24hrTicker':
                            tick = {
                                "ts": datetime.fromtimestamp(data['E']/1000, tz=timezone.utc).isoformat(),
                                "exchange": "Binance",
                                "pair": symbol,
                                "price": float(data['c']),
                                "volume": float(data['v']),
                                "buy_vol": recent_volumes[symbol]['buy'],
                                "sell_vol": recent_volumes[symbol]['sell'],
                                "bid": float(data['b']),
                                "ask": float(data['a'])
                            }
                            redis_client.set(f"tick:Binance:{symbol}", json.dumps(tick))
                            
        except Exception as e:
            logger.error(f"Binance WS error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

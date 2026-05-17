import asyncio
import json
import logging
import websockets
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

async def start_coinbase_collector(redis_client, pairs):
    # Coinbase liquidity reference only
    url = "wss://advanced-trade-ws.coinbase.com"

    # Maintain local order book state for liquidity calculations
    orderbooks = {p.replace('/', ''): {'bids': {}, 'asks': {}} for p in pairs}

    while True:
        try:
            async with websockets.connect(url) as ws:
                logger.info(f"Connected to Coinbase WS for {pairs}")
                
                symbols = [p.replace('/', '-') for p in pairs]
                sub_msg = {
                    "type": "subscribe",
                    "product_ids": symbols,
                    "channel": "level2"
                }
                await ws.send(json.dumps(sub_msg))

                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    
                    if data.get('channel') == 'l2_data':
                        for event in data.get('events', []):
                            symbol = event['product_id'].replace('-', '')
                            updates = event.get('updates', [])
                            
                            # Apply updates to local orderbook
                            for update in updates:
                                side_key = 'bids' if update['side'] == 'bid' else 'asks'
                                price = float(update['price_level'])
                                new_quantity = float(update['new_quantity'])
                                
                                if new_quantity == 0:
                                    if price in orderbooks[symbol][side_key]:
                                        del orderbooks[symbol][side_key][price]
                                else:
                                    orderbooks[symbol][side_key][price] = new_quantity
                            
                            if updates:
                                # Calculate Long Liquidity (bids) and Short Liquidity (asks)
                                long_liq = sum(p * q for p, q in orderbooks[symbol]['bids'].items())
                                short_liq = sum(p * q for p, q in orderbooks[symbol]['asks'].items())
                                
                                top_bid = max(orderbooks[symbol]['bids'].keys(), default=0)
                                top_ask = min(orderbooks[symbol]['asks'].keys(), default=0)
                                mid_price = (top_bid + top_ask) / 2 if (top_bid > 0 and top_ask > 0) else float(updates[0]['price_level'])
                                
                                tick = {
                                    "ts": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
                                    "exchange": "Coinbase",
                                    "pair": symbol,
                                    "price": mid_price,
                                    "volume": 0,
                                    "bid": top_bid,
                                    "ask": top_ask,
                                    "long_liq": long_liq,
                                    "short_liq": short_liq
                                }
                                redis_client.set(f"tick:Coinbase:{symbol}", json.dumps(tick))
                        
        except Exception as e:
            logger.error(f"Coinbase WS error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

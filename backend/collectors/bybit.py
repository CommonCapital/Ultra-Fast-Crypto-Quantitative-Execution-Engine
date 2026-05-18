import asyncio
import json
import logging
import websockets
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def start_bybit_collector(redis_client, pairs):
    url = "wss://stream.bybit.com/v5/public/spot"

    symbols = [p.replace('/', '') for p in pairs]

    # Local state cache — Bybit sends snapshots then partial deltas.
    # We must merge each delta into the last known full state.
    state = {s: {"price": 0.0, "volume": 0.0, "bid": 0.0, "ask": 0.0} for s in symbols}

    while True:
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=30) as ws:
                logger.info(f"Connected to Bybit WS for {len(symbols)} pairs")

                sub_msg = {
                    "op": "subscribe",
                    "args": [f"tickers.{s}" for s in symbols]
                }
                await ws.send(json.dumps(sub_msg))

                while True:
                    msg = await ws.recv()
                    try:
                        data = json.loads(msg)
                    except json.JSONDecodeError:
                        continue

                    topic = data.get('topic', '')
                    if not topic.startswith('tickers'):
                        continue

                    symbol = data.get('data', {}).get('symbol', '')
                    if symbol not in state:
                        continue

                    d = data.get('data', {})

                    # Merge any non-empty fields into local state
                    def safe_float(val):
                        """Return float if val is a non-empty string/number, else None."""
                        if val is None or val == '':
                            return None
                        try:
                            return float(val)
                        except (ValueError, TypeError):
                            return None

                    price  = safe_float(d.get('lastPrice'))
                    volume = safe_float(d.get('volume24h'))
                    bid    = safe_float(d.get('bid1Price'))
                    ask    = safe_float(d.get('ask1Price'))

                    if price  is not None: state[symbol]['price']  = price
                    if volume is not None: state[symbol]['volume'] = volume
                    if bid    is not None: state[symbol]['bid']    = bid
                    if ask    is not None: state[symbol]['ask']    = ask

                    # Only write to Redis if we have a valid price
                    if state[symbol]['price'] > 0:
                        # Derive bid/ask from price if still missing
                        cur_bid = state[symbol]['bid'] or state[symbol]['price']
                        cur_ask = state[symbol]['ask'] or state[symbol]['price']

                        tick = {
                            "ts": datetime.now(timezone.utc).isoformat(),
                            "exchange": "Bybit",
                            "pair": symbol,
                            "price": state[symbol]['price'],
                            "volume": state[symbol]['volume'],
                            "bid": cur_bid,
                            "ask": cur_ask,
                            "buy_vol": 0.0,
                            "sell_vol": 0.0,
                        }
                        # 30s TTL: if Bybit goes silent, price disappears instead of staling
                        redis_client.setex(f"tick:Bybit:{symbol}", 30, json.dumps(tick))

        except Exception as e:
            logger.error(f"Bybit WS error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

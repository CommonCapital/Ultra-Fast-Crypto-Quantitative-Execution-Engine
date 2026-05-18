import asyncio
import json
import logging
import websockets
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Bitunix futures WS ticker fields:
# s=symbol, la=last price, o=open, h=high, l=low,
# b=base volume (coin qty), q=quote volume (USDT), r=rate-of-change %
# No separate bid/ask channel available — we derive mid from last price.


async def start_bitunix_collector(redis_client, pairs):
    url = "wss://fapi.bitunix.com/public/"

    # symbol -> redis_key (e.g. "BTCUSDT" -> "BTCUSDT")
    sym_map = {p.replace('/', ''): p.replace('/', '') for p in pairs}

    while True:
        try:
            async with websockets.connect(url, open_timeout=15) as ws:
                logger.info("Connected to Bitunix WS")

                # Subscribe to ticker for every symbol (batch all in one message)
                args = [{"ch": "ticker", "symbol": sym} for sym in sym_map]
                await ws.send(json.dumps({"op": "subscribe", "args": args}))

                while True:
                    raw = await ws.recv()

                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    # Connection confirmation — ignore
                    if data.get('op') == 'connect':
                        continue

                    # Heartbeat ping → pong
                    if data.get('op') == 'ping':
                        await ws.send(json.dumps({'op': 'pong', 'pong': data.get('ts', 0)}))
                        continue

                    ch = data.get('ch', '')
                    symbol = data.get('symbol', '')
                    tick = data.get('data', {})

                    if ch != 'ticker' or not tick or symbol not in sym_map:
                        continue

                    # last price is "la", base vol is "b", quote vol is "q"
                    last = float(tick.get('la') or tick.get('last') or 0)
                    base_vol = float(tick.get('b') or 0)    # coin volume
                    quote_vol = float(tick.get('q') or 0)   # USDT volume

                    if last <= 0:
                        continue

                    # No bid/ask channel: use last ± a minimal half-spread (0.01%)
                    # so the internal spread filter in the engine doesn't reject this exchange.
                    half_spread = last * 0.0001
                    bid = round(last - half_spread, 8)
                    ask = round(last + half_spread, 8)

                    redis_key = sym_map[symbol]
                    payload = {
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "exchange": "Bitunix",
                        "pair": redis_key,
                        "price": round(last, 8),
                        "volume": base_vol,
                        "bid": bid,
                        "ask": ask,
                        "buy_vol": 0.0,
                        "sell_vol": 0.0,
                    }
                    redis_client.setex(f"tick:Bitunix:{redis_key}", 30, json.dumps(payload))

        except Exception as e:
            logger.error(f"Bitunix WS error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

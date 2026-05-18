import asyncio
import gzip
import json
import logging
import websockets
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def to_htx_symbol(pair: str) -> str:
    """BTC/USDT -> btcusdt"""
    return pair.replace('/', '').lower()


async def start_htx_collector(redis_client, pairs):
    url = "wss://api.huobi.pro/ws"

    # htx_sym -> redis_key (e.g. "btcusdt" -> "BTCUSDT")
    sym_map = {to_htx_symbol(p): p.replace('/', '') for p in pairs}

    # Local state: merge bbo + detail updates
    state = {s: {"bid": 0.0, "ask": 0.0, "buy_vol": 0.0, "sell_vol": 0.0} for s in sym_map}

    while True:
        try:
            async with websockets.connect(url) as ws:
                logger.info("Connected to HTX WS")

                # Subscribe to BBO (best bid/offer) for every symbol
                for htx_sym in sym_map:
                    await ws.send(json.dumps({
                        "sub": f"market.{htx_sym}.bbo",
                        "id": f"bbo_{htx_sym}"
                    }))

                while True:
                    raw = await ws.recv()

                    # HTX sends gzip-compressed binary frames
                    try:
                        msg_str = gzip.decompress(raw).decode('utf-8')
                    except Exception:
                        msg_str = raw if isinstance(raw, str) else raw.decode('utf-8', errors='ignore')

                    try:
                        data = json.loads(msg_str)
                    except json.JSONDecodeError:
                        continue

                    # Heartbeat — must pong immediately or HTX disconnects
                    if 'ping' in data:
                        await ws.send(json.dumps({'pong': data['ping']}))
                        continue

                    ch = data.get('ch', '')
                    tick = data.get('tick')
                    if not tick or not ch:
                        continue

                    # BBO update: market.btcusdt.bbo
                    if '.bbo' in ch:
                        parts = ch.split('.')
                        htx_sym = parts[1] if len(parts) >= 2 else ''
                        if htx_sym not in sym_map:
                            continue

                        bid = float(tick.get('bid') or 0)
                        ask = float(tick.get('ask') or 0)

                        if bid > 0:
                            state[htx_sym]['bid'] = bid
                        if ask > 0:
                            state[htx_sym]['ask'] = ask

                        bid = state[htx_sym]['bid']
                        ask = state[htx_sym]['ask']
                        price = (bid + ask) / 2 if bid > 0 and ask > 0 else (ask or bid)

                        if price > 0:
                            redis_key = sym_map[htx_sym]
                            payload = {
                                "ts": datetime.now(timezone.utc).isoformat(),
                                "exchange": "HTX",
                                "pair": redis_key,
                                "price": round(price, 8),
                                "volume": 0.0,
                                "bid": bid,
                                "ask": ask,
                                "buy_vol": float(state[htx_sym]['buy_vol'] or 0),
                                "sell_vol": float(state[htx_sym]['sell_vol'] or 0),
                            }
                            redis_client.setex(f"tick:HTX:{redis_key}", 30, json.dumps(payload))

        except Exception as e:
            logger.error(f"HTX WS error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

import asyncio
import json
import logging
import websockets
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# BitMEX uses XBT instead of BTC, and no slashes/underscores.
# e.g. BTC/USDT -> XBTUSDT, ETH/USDT -> ETHUSDT
def to_bitmex_symbol(pair: str) -> str:
    base, quote = pair.split('/')
    if base.upper() == 'BTC':
        base = 'XBT'
    return f"{base}{quote}"

async def start_bitmex_collector(redis_client, pairs):
    url = "wss://ws.bitmex.com/realtime"

    # Build two-way maps: bitmex_symbol <-> standard pair and standard redis key
    bitmex_to_std = {}   # e.g. "XBTUSDT" -> "BTC/USDT"
    bitmex_to_key = {}   # e.g. "XBTUSDT" -> "BTCUSDT"
    for p in pairs:
        bsym = to_bitmex_symbol(p)
        redis_key = p.replace('/', '')           # e.g. "BTCUSDT"
        bitmex_to_std[bsym] = p
        bitmex_to_key[bsym] = redis_key

    sub_symbols = list(bitmex_to_std.keys())

    # Local state cache (keyed by bitmex symbol)
    state = {
        bsym: {"price": 0.0, "volume": 0.0, "bid": None, "ask": None,
               "ts": datetime.now(timezone.utc).isoformat()}
        for bsym in sub_symbols
    }

    while True:
        try:
            async with websockets.connect(url) as ws:
                logger.info(f"Connected to BitMEX WS. Subscribing to {sub_symbols}")

                # Subscribe to quote (bid/ask) and trade (last price) topics
                args = (
                    [f"quote:{s}" for s in sub_symbols] +
                    [f"trade:{s}" for s in sub_symbols]
                )
                await ws.send(json.dumps({"op": "subscribe", "args": args}))

                while True:
                    msg = await ws.recv()
                    try:
                        data = json.loads(msg)
                        table = data.get("table")

                        if table in ["quote", "trade"] and "data" in data:
                            for item in data["data"]:
                                bsym = item.get("symbol", "")
                                if bsym not in bitmex_to_std:
                                    continue

                                redis_key = bitmex_to_key[bsym]

                                if table == "quote":
                                    if item.get("bidPrice"):
                                        state[bsym]["bid"] = float(item["bidPrice"])
                                    if item.get("askPrice"):
                                        state[bsym]["ask"] = float(item["askPrice"])
                                elif table == "trade":
                                    if item.get("price"):
                                        state[bsym]["price"] = float(item["price"])
                                    if item.get("size"):
                                        state[bsym]["volume"] += float(item["size"])

                                state[bsym]["ts"] = datetime.now(timezone.utc).isoformat()

                                # Fallback: derive price from mid-quote if no trade yet
                                if state[bsym]["price"] == 0.0 and state[bsym]["ask"]:
                                    state[bsym]["price"] = state[bsym]["ask"]

                                has_quotes = state[bsym]["bid"] and state[bsym]["ask"]
                                active_price = (
                                    (state[bsym]["bid"] + state[bsym]["ask"]) / 2
                                    if has_quotes else state[bsym]["price"]
                                )

                                if active_price > 0:
                                    tick = {
                                        "ts": state[bsym]["ts"],
                                        "exchange": "BitMEX",
                                        "pair": redis_key,
                                        "price": round(active_price, 4),
                                        "volume": state[bsym]["volume"],
                                        "bid": state[bsym]["bid"] if state[bsym]["bid"] else active_price,
                                        "ask": state[bsym]["ask"] if state[bsym]["ask"] else active_price,
                                    }
                                    # Expire after 30s: if BitMEX goes silent, price disappears
                                    # from the matrix instead of showing a stale frozen value
                                    redis_client.setex(
                                        f"tick:BitMEX:{redis_key}", 30, json.dumps(tick)
                                    )

                    except (json.JSONDecodeError, KeyError, ValueError):
                        pass

        except Exception as e:
            logger.error(f"BitMEX WS error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

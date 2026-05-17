import asyncio
import websockets
import json

async def test():
    url = "wss://wbs.mexc.com/ws"
    async with websockets.connect(url) as ws:
        msg = {
            "method": "SUBSCRIPTION",
            "params": ["spot@public.bookTicker.v3.api@BTCUSDT"]
        }
        await ws.send(json.dumps(msg))
        for _ in range(3):
            res = await ws.recv()
            print(res)

asyncio.run(test())

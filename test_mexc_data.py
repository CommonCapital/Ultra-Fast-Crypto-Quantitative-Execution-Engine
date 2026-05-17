import asyncio
import websockets
import json

async def test():
    url = "wss://wbs-api.mexc.com/ws"
    async with websockets.connect(url, ping_interval=None) as ws:
        msg = {
            "method": "SUBSCRIPTION",
            "params": ["spot@public.miniTicker.v3.api@BTCUSDT@UTC+0"]
        }
        await ws.send(json.dumps(msg))
        try:
            res = await asyncio.wait_for(ws.recv(), timeout=2.0)
            print(f"Response (miniTicker): {res}")
            res = await asyncio.wait_for(ws.recv(), timeout=2.0)
            print(f"Response (miniTicker): {res}")
        except Exception as e:
            print(f"Error (miniTicker): {e}")

asyncio.run(test())

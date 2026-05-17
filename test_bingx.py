import asyncio
import websockets
import json
import gzip

async def test():
    url = "wss://open-api-ws.bingx.com/market"
    async with websockets.connect(url) as ws:
        msg = {
            "id": "sub_BTC-USDT",
            "reqType": "sub",
            "dataType": "BTC-USDT@ticker"
        }
        await ws.send(json.dumps(msg))
        for _ in range(3):
            res = await ws.recv()
            if isinstance(res, bytes):
                res = gzip.decompress(res).decode('utf-8')
            print(res)

asyncio.run(test())

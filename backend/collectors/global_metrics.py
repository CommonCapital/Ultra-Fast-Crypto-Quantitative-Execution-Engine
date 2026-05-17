import asyncio
import json
import logging
import httpx
from datetime import datetime, timezone
from ..config import settings

logger = logging.getLogger(__name__)

async def start_global_metrics_collector(redis_client, pairs):
    """Fetches Fear & Greed Index and CMC Volume Data"""
    
    # Extract raw symbols for CMC (e.g., BTC, ETH, SOL)
    symbols = [p.split('/')[0] for p in pairs]
    symbols_str = ",".join(symbols)
    
    cmc_url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol={symbols_str}"
    fng_url = "https://api.alternative.me/fng/"
    
    while True:
        try:
            async with httpx.AsyncClient() as client:
                # 1. Fetch Fear and Greed Index (Free Alternative.me API)
                fng_resp = await client.get(fng_url)
                fng_data = fng_resp.json()
                if fng_data and fng_data.get('data'):
                    fng_value = fng_data['data'][0]['value']
                    fng_class = fng_data['data'][0]['value_classification']
                    redis_client.set("global:fng", json.dumps({"value": fng_value, "class": fng_class}))
                
                # 2. Fetch CoinMarketCap 24h Volume Data (if API key provided)
                if settings.CMC_API_KEY:
                    headers = {
                        'Accepts': 'application/json',
                        'X-CMC_PRO_API_KEY': settings.CMC_API_KEY,
                    }
                    cmc_resp = await client.get(cmc_url, headers=headers)
                    if cmc_resp.status_code == 200:
                        cmc_data = cmc_resp.json()
                        for sym in symbols:
                            if sym in cmc_data.get('data', {}):
                                coin_data = cmc_data['data'][sym]
                                vol_24h = coin_data['quote']['USD']['volume_24h']
                                redis_client.set(f"global:cmc_vol:{sym}", json.dumps({"volume_24h": vol_24h}))
                    else:
                        logger.warning(f"CMC API Error: {cmc_resp.status_code} - {cmc_resp.text}")

        except Exception as e:
            logger.error(f"Global metrics collector error: {e}")
            
        # Update every 5 minutes (300s) to perfectly fit inside CMC's Free Tier 
        # (10,000 credits/month limit. 5 mins = 8,640 calls/month)
        await asyncio.sleep(300)

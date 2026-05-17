import httpx
import logging
from ..config import settings

logger = logging.getLogger(__name__)

async def generate_narrative(arb_data: dict) -> str:
    """
    Calls DeepSeek API to wrap raw arb_data into a human-readable narrative.
    """
    if not settings.DEEPSEEK_API_KEY:
        logger.warning("DeepSeek API key not set. Using raw data fallback.")
        return f"🚨 Arb Alert: {arb_data['pair']} | Buy {arb_data['buy_exchange']} @ {arb_data['buy_price']} | Sell {arb_data['sell_exchange']} @ {arb_data['sell_price']} | Spread {arb_data['spread_pct']}%"
        
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    You are an expert crypto quantitative analyst. Write a concise, 100-150 word Telegram alert 
    for the following arbitrage opportunity. Make it sound professional and urgent but grounded in data.
    
    Data:
    Pair: {arb_data['pair']}
    Buy Exchange: {arb_data['buy_exchange']} at ${arb_data['buy_price']}
    Sell Exchange: {arb_data['sell_exchange']} at ${arb_data['sell_price']}
    Spread: {arb_data['spread_pct']}%
    Recent Buy Volume: {arb_data['buy_vol']}
    Recent Sell Volume: {arb_data['sell_vol']}
    
    Format nicely with emojis. Do not invent any numbers.
    """
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a helpful crypto analysis bot."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,
        "max_tokens": 200
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content'].strip()
        except Exception as e:
            logger.error(f"Failed to generate DeepSeek narrative: {e}")
            return f"🚨 Arb Alert: {arb_data['pair']} (LLM generation failed, spread: {arb_data['spread_pct']}%)"

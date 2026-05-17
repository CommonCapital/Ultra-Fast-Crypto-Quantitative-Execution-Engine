import logging
from ..config import settings

logger = logging.getLogger(__name__)

class ArbitrageDetector:
    def __init__(self):
        pass

    def check_opportunity(self, pair: str, prices: dict) -> dict:
        if len(prices) < 2:
            return None
            
        # Find min ask (buy) and max bid (sell)
        valid_exchanges = {k: v for k, v in prices.items() if v.get('ask') and v.get('bid')}
        if len(valid_exchanges) < 2:
            return None

        buy_exchange = min(valid_exchanges.items(), key=lambda x: x[1]['ask'])
        sell_exchange = max(valid_exchanges.items(), key=lambda x: x[1]['bid'])
        
        buy_price = buy_exchange[1]['ask']
        sell_price = sell_exchange[1]['bid']
        
        # Condition 1: Spread & Exact Compound Fees
        buy_fee = settings.EXCHANGE_FEES.get(buy_exchange[0], 0.001)
        sell_fee = settings.EXCHANGE_FEES.get(sell_exchange[0], 0.001)
        
        # Calculate exactly how much capital remains after buying (deducting buy fee),
        # riding the price difference, and selling (deducting sell fee).
        profit_multiplier = (sell_price / buy_price) * (1 - buy_fee) * (1 - sell_fee)
        net_spread = (profit_multiplier - 1) * 100
        
        if net_spread < settings.MIN_NET_SPREAD:
            return None
            
        # Condition 3: Liquidity (Optional)
        coinbase_data = prices.get('Coinbase', {})
        cb_short_liq = coinbase_data.get('short_liq', 0)
        cb_long_liq = coinbase_data.get('long_liq', 0)
        
        if settings.REQUIRE_SHORT_DOMINANCE:
            # Require Coinbase short liquidity to be explicitly greater than long liquidity
            if cb_short_liq <= cb_long_liq or cb_short_liq == 0:
                return None
                
        # Condition 2 (MVP): Recent Buys > Recent Sells (Clear Growth)
        binance_data = prices.get('Binance', {})
        buy_vol = binance_data.get('buy_vol', 0)
        sell_vol = binance_data.get('sell_vol', 0)
        
        # Enforce momentum: buyer volume must be exceeding seller volume
        if buy_vol <= sell_vol or buy_vol == 0:
            return None
            
        return {
            "pair": pair,
            "buy_exchange": buy_exchange[0],
            "sell_exchange": sell_exchange[0],
            "buy_price": buy_price,
            "sell_price": sell_price,
            "spread_pct": round(net_spread, 3),
            "buy_vol": buy_vol,
            "sell_vol": sell_vol,
            "cb_short_liq": cb_short_liq,
            "cb_long_liq": cb_long_liq
        }

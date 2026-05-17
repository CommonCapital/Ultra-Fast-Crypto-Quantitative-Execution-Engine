import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # API Keys & URLs
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    CMC_API_KEY = os.getenv("CMC_API_KEY", "")
    NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL", "")
    
    # Autonomous Trading Credentials (CCXT)
    EXCHANGE_CREDENTIALS = {
        "Binance": {
            "apiKey": os.getenv("BINANCE_API_KEY", ""),
            "secret": os.getenv("BINANCE_SECRET_KEY", "")
        },
        "Bybit": {
            "apiKey": os.getenv("BYBIT_API_KEY", ""),
            "secret": os.getenv("BYBIT_SECRET_KEY", "")
        },
        "MEXC": {
            "apiKey": os.getenv("MEXC_API_KEY", ""),
            "secret": os.getenv("MEXC_SECRET_KEY", "")
        },
        "BingX": {
            "apiKey": os.getenv("BINGX_API_KEY", ""),
            "secret": os.getenv("BINGX_SECRET_KEY", "")
        },
        "Coinbase": {
            "apiKey": os.getenv("COINBASE_API_KEY", ""),
            "secret": os.getenv("COINBASE_SECRET_KEY", "")
        },
        "OKX": {
            "apiKey": os.getenv("OKX_API_KEY", ""),
            "secret": os.getenv("OKX_SECRET_KEY", ""),
            "password": os.getenv("OKX_PASSPHRASE", "")
        },
        "BitMEX": {
            "apiKey": os.getenv("BITMEX_API_KEY", ""),
            "secret": os.getenv("BITMEX_SECRET_KEY", "")
        }
    }
    
    # Engine Thresholds
    MIN_NET_SPREAD = 0.5 # 0.5% minimum profit AFTER all exchange fees are deducted
    REQUIRE_SHORT_DOMINANCE = True
    
    # Standard Taker Trading Fees per exchange (e.g. 0.001 = 0.1%)
    EXCHANGE_FEES = {
        "Binance": 0.001,
        "Bybit": 0.001,
        "MEXC": 0.001,    # often 0 for makers, but 0.1% for takers
        "BingX": 0.001,
        "Coinbase": 0.004, # Advanced trade standard taker fee
        "OKX": 0.001,
        "BitMEX": 0.001
    }
    
    # Pairs to track (24 High-Volume Assets across L1s, Memes, AI, DeFi, and Majors)
    PAIRS = [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT", "DOGE/USDT", 
        "LINK/USDT", "AVAX/USDT", "SHIB/USDT", "PEPE/USDT", "NEAR/USDT", "SUI/USDT", 
        "APT/USDT", "FET/USDT", "RENDER/USDT", "WLD/USDT", "INJ/USDT", "TIA/USDT", 
        "FTM/USDT", "DOT/USDT", "MATIC/USDT", "LTC/USDT", "BCH/USDT", "ATOM/USDT"
    ]

settings = Settings()

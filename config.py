import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # QuickNode Configuration
    QUICKNODE_ENDPOINT = os.getenv("QUICKNODE_ENDPOINT")
    QUICKNODE_API_KEY = os.getenv("QUICKNODE_API_KEY")
    
    # Wallet Configuration
    TRADING_WALLET_PRIVATE_KEY = os.getenv("TRADING_WALLET_PRIVATE_KEY")
    PROFIT_WALLET_ADDRESS = os.getenv("PROFIT_WALLET_ADDRESS")
    
    # Solana Network
    SOLANA_RPC_ENDPOINT = "https://api.mainnet-beta.solana.com"
    
    # Trading Parameters
    MIN_MARKET_CAP = float(os.getenv("MIN_MARKET_CAP", 10000))
    MIN_DAILY_VOLUME = float(os.getenv("MIN_DAILY_VOLUME", 5000))
    MIN_HOLDERS = int(os.getenv("MIN_HOLDERS", 100))
    INVESTMENT_AMOUNT = float(os.getenv("INVESTMENT_AMOUNT", 0.1))
    MAX_POSITIONS = int(os.getenv("MAX_POSITIONS", 10))
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    # Security Configuration
    BOT_PASSWORD = os.getenv("BOT_PASSWORD")
    MAX_PASSWORD_ATTEMPTS = int(os.getenv("MAX_PASSWORD_ATTEMPTS", 3))
    SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", 43200))

    # Monitoring
    CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 300))  # 5 minutes default
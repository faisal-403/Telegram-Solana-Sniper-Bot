import asyncio
import logging
import os
from config import Config
from monitor import MemecoinMonitor
from dotenv import load_dotenv
load_dotenv()

#print(os.getenv("TRADING_WALLET_PRIVATE_KEY"))

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bot.log'),
            logging.StreamHandler()
        ]
    )

async def main():
    setup_logging()
    config = Config()
    monitor = MemecoinMonitor(config)
    
    try:
        await monitor.initialize()
        await monitor.run()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
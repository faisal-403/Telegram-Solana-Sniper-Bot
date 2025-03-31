import asyncio
import time
import logging
from typing import Dict
from config import Config
from analyzer import MemecoinAnalyzer
from trader import MemecoinTrader
from telegram_manager import TelegramManager

class MemecoinMonitor:
    def __init__(self, config: Config):
        self.config = config
        self.analyzer = MemecoinAnalyzer(config)
        self.trader = MemecoinTrader(config)
        self.telegram = TelegramManager(config, self)
        self.active_positions: Dict[str, Dict] = {}
        self.hold_hours = 24
        self.running = False
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        await self.telegram.initialize()
        peak_data = self.analyzer.analyze_peak_times()
        self.hold_hours = peak_data.get("1 month", {}).get("median", 24)
        self.logger.info(f"Initialized with hold time: {self.hold_hours} hours")

    async def run(self):
        self.running = True
        await self.telegram.send_notification("🤖 Trading Bot Started")
        
        while self.running:
            try:
                await self._check_new_tokens()
                await self._check_active_positions()
                await asyncio.sleep(self.config.CHECK_INTERVAL)
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(60)

    async def _check_new_tokens(self):
        if len(self.active_positions) >= self.config.MAX_POSITIONS:
            return
            
        new_tokens = self.analyzer.get_recent_tokens(hours=1)
        if not new_tokens:
            return
            
        for token in new_tokens:
            token_address = token['address']
            if token_address not in self.active_positions:
                is_valid, _ = self.analyzer.verify_token(token_address)
                if is_valid:
                    success, tx_hash = self.trader.buy_token(
                        token_address,
                        self.config.INVESTMENT_AMOUNT
                    )
                    if success:
                        self.active_positions[token_address] = {
                            'buy_time': time.time(),
                            'amount': self.config.INVESTMENT_AMOUNT,
                            'buy_tx': tx_hash
                        }

    async def _check_active_positions(self):
        current_time = time.time()
        to_remove = []
        
        for token_address, position in self.active_positions.items():
            if (current_time - position['buy_time']) >= (self.hold_hours * 3600):
                success, tx_hash = self.trader.sell_token(token_address, "ALL")
                if success:
                    to_remove.append(token_address)
                    profit = position['amount'] * 1.5  # Example profit calculation
                    await self.trader.transfer_profits(profit)
        
        for token in to_remove:
            self.active_positions.pop(token, None)

    async def shutdown(self):
        self.running = False
        await self.telegram.shutdown()
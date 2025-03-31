import base64
import requests
import time
import logging
from typing import Optional, Tuple
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed
from solana.transaction import Transaction
from solders.system_program import TransferParams, transfer

class MemecoinTrader:
    def __init__(self, config):
        self.config = config
        self.client = Client(config.SOLANA_RPC_ENDPOINT)
        self.trading_keypair = Keypair.from_base58_string(config.TRADING_WALLET_PRIVATE_KEY)
        self.jupiter_url = "https://quote-api.jup.ag/v6"
        self.logger = logging.getLogger(__name__)
        self.last_trade_time = 0

    def get_swap_quote(self, input_mint: str, output_mint: str, amount: int) -> Optional[dict]:
        try:
            url = f"{self.jupiter_url}/quote?inputMint={input_mint}&outputMint={output_mint}&amount={amount}&slippageBps=100"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get swap quote: {e}")
            return None

    def get_swap_transaction(self, quote: dict) -> Optional[Transaction]:
        try:
            payload = {
                "quoteResponse": quote,
                "userPublicKey": str(self.trading_keypair.pubkey()),
                "wrapAndUnwrapSol": True
            }
            response = requests.post(
                f"{self.jupiter_url}/swap",
                json=payload,
                timeout=15
            )
            response.raise_for_status()
            swap_data = response.json()
            return Transaction.deserialize(base64.b64decode(swap_data['swapTransaction']))
        except Exception as e:
            self.logger.error(f"Error creating swap transaction: {e}")
            return None

    def execute_swap(self, input_mint: str, output_mint: str, amount: int) -> Tuple[bool, Optional[str]]:
        if time.time() - self.last_trade_time < 10:  # Rate limiting
            return False, None
            
        quote = self.get_swap_quote(input_mint, output_mint, amount)
        if not quote:
            return False, None
            
        txn = self.get_swap_transaction(quote)
        if not txn:
            return False, None
            
        try:
            response = self.client.send_transaction(txn, self.trading_keypair)
            if response.value:
                self.last_trade_time = time.time()
                return True, str(response.value)
            return False, None
        except Exception as e:
            self.logger.error(f"Failed to send transaction: {e}")
            return False, None

    def buy_token(self, token_address: str, amount_sol: float) -> Tuple[bool, Optional[str]]:
        amount_lamports = int(amount_sol * 10**9)
        sol_mint = "So11111111111111111111111111111111111111112"
        return self.execute_swap(sol_mint, token_address, amount_lamports)

    def sell_token(self, token_address: str, token_amount: int) -> Tuple[bool, Optional[str]]:
        sol_mint = "So11111111111111111111111111111111111111112"
        return self.execute_swap(token_address, sol_mint, token_amount)

    def get_balance(self) -> float:
        try:
            balance = self.client.get_balance(self.trading_keypair.pubkey()).value
            return balance / 10**9
        except Exception as e:
            self.logger.error(f"Failed to get balance: {e}")
            return 0.0

    def transfer_profits(self, amount_sol: float) -> Tuple[bool, Optional[str]]:
        try:
            txn = transfer(
                TransferParams(
                    from_pubkey=self.trading_keypair.pubkey(),
                    to_pubkey=Pubkey.from_string(self.config.PROFIT_WALLET_ADDRESS),
                    lamports=int(amount_sol * 10**9)
                )
            )
            response = self.client.send_transaction(txn, self.trading_keypair)
            return (True, str(response.value)) if response.value else (False, None)
        except Exception as e:
            self.logger.error(f"Failed to transfer profits: {e}")
            return False, None
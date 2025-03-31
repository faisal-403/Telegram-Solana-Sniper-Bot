import requests
import statistics
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from solders.pubkey import Pubkey
from solana.rpc.api import Client

class MemecoinAnalyzer:
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.QUICKNODE_API_KEY}"
        })
        self.client = Client(self.config.SOLANA_RPC_ENDPOINT)
        self.logger = logging.getLogger(__name__)

    def _make_request(self, method: str, params: list) -> Optional[dict]:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        try:
            response = self.session.post(
                self.config.QUICKNODE_ENDPOINT,
                json=payload,
                timeout=15
            )
            response.raise_for_status()
            return response.json().get("result")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            return None

    def get_recent_tokens(self, hours: int = 24) -> Optional[List[dict]]:
        now = int(time.time())
        params = [{
            "type": "spl-token",
            "filters": {
                "createdAfter": now - (hours * 3600),
                "isMemecoin": True
            },
            "page": 1,
            "perPage": 50
        }]
        result = self._make_request("qn_getAssetsByTime", params)
        return result.get("items") if result else None

    def get_token_metrics(self, token_address: str) -> Optional[dict]:
        params = [{
            "tokenAddress": token_address,
            "metrics": ["marketCap", "dailyVolume", "holdersCount", "priceHistory"]
        }]
        return self._make_request("qn_getTokenMetrics", params)

    def analyze_peak_times(self) -> Dict[str, dict]:
        time_periods = {"1mo": "1 month", "1w": "1 week"}
        results = {}
        
        for period, label in time_periods.items():
            tokens = self.get_recent_tokens(hours=self._period_to_hours(period))
            if not tokens:
                continue
                
            peak_times = []
            for token in tokens[:20]:  # Limit to 20 samples
                metrics = self.get_token_metrics(token['address'])
                if metrics and metrics.get('priceHistory'):
                    creation_time = token['createdAt']
                    peak_price = max(p['price'] for p in metrics['priceHistory'])
                    peak_point = next(p for p in metrics['priceHistory'] if p['price'] == peak_price)
                    peak_times.append((peak_point['timestamp'] - creation_time) / 3600)
            
            if peak_times:
                results[label] = {
                    "median": statistics.median(peak_times),
                    "mean": statistics.mean(peak_times),
                    "max": max(peak_times),
                    "min": min(peak_times),
                    "sample_size": len(peak_times)
                }
        return results
        #print (results)

    def _period_to_hours(self, period: str) -> int:
        return {"1mo": 720, "1w": 168}.get(period, 24)

    def verify_token(self, token_address: str) -> Tuple[bool, str]:
        metrics = self.get_token_metrics(token_address)
        if not metrics:
            return False, "Failed to fetch metrics"
            
        reasons = []
        if metrics.get('marketCap', 0) < self.config.MIN_MARKET_CAP:
            reasons.append("Market cap too low")
        if metrics.get('dailyVolume', 0) < self.config.MIN_DAILY_VOLUME:
            reasons.append("Volume too low")
        if metrics.get('holdersCount', 0) < self.config.MIN_HOLDERS:
            reasons.append("Holders too low")
            
        return (len(reasons) == 0, ", ".join(reasons) if reasons else "Valid token")
        #print ((len(reasons) == 0, ", ".join(reasons) if reasons else "Valid token"))

import time
from datetime import datetime
import requests
import config
from src.utils.helper import logger

class OnChainAnalyzer:
    def __init__(self):
        self.whale_transactions = []  # List of strings: "🐋 [14:30] BUY BTC/USDT worth $1,500,000"
        self.stablecoin_inflow = "Neutral"  # Neutral, Positive, Negative
        
        # De-duplication state
        self._last_whale_key: str | None = None
        self._last_whale_time: float = 0
        self._dedup_window_seconds: int = 5  # Skip transaksi identik dalam 5 detik

    def detect_whale(self, symbol: str, size_usdt: float, side: str) -> None:
        """
        Called by WebSocket AggTrade or OrderUpdate to record big trades.
        Includes de-duplication to prevent logging identical transactions.
        """
        if size_usdt >= config.WHALE_THRESHOLD_USDT:
            current_time = time.time()
            
            # De-duplication: Skip jika transaksi identik dalam window waktu
            whale_key = f"{side}_{symbol}_{int(size_usdt)}"
            if whale_key == self._last_whale_key and (current_time - self._last_whale_time) < self._dedup_window_seconds:
                logger.debug(f"🐋 Skipped duplicate whale: {whale_key}")
                return  # Skip duplicate
            
            # Update de-duplication state
            self._last_whale_key = whale_key
            self._last_whale_time = current_time
            
            # Format message dengan timestamp untuk clarity
            timestamp = datetime.now().strftime("%H:%M")
            msg = f"🐋 [{timestamp}] {side} {symbol} worth ${size_usdt:,.0f}"
            self.whale_transactions.append(msg)
            
            # Keep only last N transactions
            if len(self.whale_transactions) > config.WHALE_HISTORY_LIMIT:
                self.whale_transactions.pop(0)
            


    def fetch_stablecoin_inflows(self):
        try:
            url = config.DEFILLAMA_STABLECOIN_URL
            resp = requests.get(url, timeout=config.API_REQUEST_TIMEOUT)
            data = resp.json()
            
            if data and len(data) > 2:
                # Structure: [{'date': 1600..., 'totalCirculating': {'peggedUSD': 100...}}, ...]
                # Note: "totalCirculatingUSD" key represents aggregated mcap
                
                # Get last two records
                curr = data[-1]
                prev = data[-2]
                
                # Check for 'totalCirculatingUSD' key directly
                # It is a dict: {'peggedUSD': ..., 'peggedEUR': ...}
                curr_dict = curr.get('totalCirculatingUSD', {})
                prev_dict = prev.get('totalCirculatingUSD', {})
                
                curr_val = curr_dict.get('peggedUSD', 0)
                prev_val = prev_dict.get('peggedUSD', 0)
                
                if curr_val and prev_val:
                    change_pct = ((curr_val - prev_val) / prev_val) * 100
                    
                    if change_pct > config.STABLECOIN_INFLOW_THRESHOLD_PERCENT:
                        self.stablecoin_inflow = "Positive"
                    elif change_pct < -config.STABLECOIN_INFLOW_THRESHOLD_PERCENT:
                        self.stablecoin_inflow = "Negative"
                    else:
                        self.stablecoin_inflow = "Neutral"
                        
                    logger.info(f"🪙 Stablecoin Inflow: {self.stablecoin_inflow} ({change_pct:.2f}%)")
                else:
                    self.stablecoin_inflow = "Neutral"
            else:
                 logger.warning("CoinLlama Data Insufficient")
                 
        except Exception as e:
            logger.error(f"❌ Failed fetch Stablecoin Inflow: {e}")
            self.stablecoin_inflow = "Neutral" # Fallback

    def get_latest(self):
        return {
            "whale_activity": self.whale_transactions,
            "stablecoin_inflow": self.stablecoin_inflow
        }

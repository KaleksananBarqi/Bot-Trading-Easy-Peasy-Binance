
import asyncio
import time
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add root and src to path to simulate app environment
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_root)
sys.path.append(os.path.join(repo_root, 'src'))

# Mock config before importing modules that might use it
import src.config as config

# Override config for benchmark
config.DAFTAR_KOIN = [{'symbol': f'COIN{i}/USDT'} for i in range(20)]
config.CONCURRENCY_LIMIT = 20
config.PAKAI_DEMO = False # Avoid creating public exchange in __init__

from src.modules.market_data import MarketDataManager

# Mock Exchange
class MockExchange:
    def __init__(self):
        self.options = {}

    async def fetch_funding_rate(self, symbol):
        await asyncio.sleep(0.05) # Simulate latency
        return {'fundingRate': 0.0001}

    async def fetch_open_interest(self, symbol):
        await asyncio.sleep(0.05)
        return {'openInterestAmount': 1000}

    async def fapiDataGetTopLongShortAccountRatio(self, params):
        await asyncio.sleep(0.05)
        return [{'longShortRatio': 1.5}]

    async def close(self):
        pass

async def benchmark_baseline(mgr):
    """
    Replicates the current sequential logic in _maintain_slow_data
    """
    start_time = time.time()

    # Logic from current src/modules/market_data.py
    for coin in config.DAFTAR_KOIN:
        symbol = coin['symbol']
        try:
            # 1. Update Funding Rate
            fr = await mgr.exchange.fetch_funding_rate(symbol)

            # 2. Update Open Interest
            oi = await mgr.exchange.fetch_open_interest(symbol)

            # 3. Update Long/Short Ratio
            # replicating _fetch_lsr logic inline or calling it if we didn't mock it away
            # We will call the mock exchange directly to simulate the sequential nature exactly as in the loop
            lsr_val = await mgr._fetch_lsr(symbol)

            async with mgr.data_lock:
                mgr.funding_rates[symbol] = fr.get('fundingRate', 0)
                mgr.open_interest[symbol] = float(oi.get('openInterestAmount', 0))
                if lsr_val:
                    mgr.lsr_data[symbol] = lsr_val

        except Exception as e:
            pass

    duration = time.time() - start_time
    return duration

async def benchmark_optimized(mgr):
    """
    Uses the actual implemented logic in MarketDataManager
    """
    start_time = time.time()

    # We call the helper method directly for all coins, mimicking the loop in _maintain_slow_data
    # We don't call _maintain_slow_data because it has an infinite loop and sleep.

    tasks = [mgr._update_single_coin_slow_data(coin) for coin in config.DAFTAR_KOIN]
    await asyncio.gather(*tasks)

    duration = time.time() - start_time
    return duration

async def run_benchmark():
    print(f"Starting Benchmark with {len(config.DAFTAR_KOIN)} coins...")
    print(f"Simulated Latency per call: 0.05s")
    print(f"Concurrency Limit: {config.CONCURRENCY_LIMIT}")

    mock_exchange = MockExchange()
    mgr = MarketDataManager(mock_exchange)

    # Mock _fetch_lsr to use our mock exchange because the original checks self.exchange_public
    # But since we set PAKAI_DEMO=False, it uses self.exchange which is our mock.
    # However, let's verify _fetch_lsr calls fapiDataGetTopLongShortAccountRatio

    print("\n--- Running Baseline (Sequential) ---")
    baseline_time = await benchmark_baseline(mgr)
    print(f"Baseline Time: {baseline_time:.4f} seconds")

    print("\n--- Running Optimized (Concurrent) ---")
    optimized_time = await benchmark_optimized(mgr)
    print(f"Optimized Time: {optimized_time:.4f} seconds")

    improvement = baseline_time / optimized_time if optimized_time > 0 else 0
    print(f"\nSpeedup: {improvement:.2f}x")

if __name__ == "__main__":
    asyncio.run(run_benchmark())

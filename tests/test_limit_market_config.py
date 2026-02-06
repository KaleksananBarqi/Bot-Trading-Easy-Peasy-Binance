
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os
import asyncio

# Fix Path: Add 'src' to sys.path so 'import config' works as expected in the modules
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '../src'))
sys.path.insert(0, SRC_DIR)

# Now we can import the project modules
try:
    import config
    from src.modules.executor import OrderExecutor
    from src.utils.prompt_builder import build_market_prompt
except ImportError as e:
    # Fallback if src is not strictly a package, direct import might be needed 
    # But usually adding to path fixes it.
    raise e

class TestLimitMarketConfig(unittest.TestCase):
    

    def setUp(self):
        # Setup mock exchange for executor
        self.mock_exchange = MagicMock()
        # Use AsyncMock directly, avoiding early Future creation
        self.mock_exchange.fetch_balance = AsyncMock(return_value={'USDT': {'free': 1000.0}})
        
        # We need to ensure we can instantiate Executor without side effects
        # Executor loads tracker on init, which is fine (file op), but we handle it.
        self.executor = OrderExecutor(self.mock_exchange)

    def test_dynamic_size_disabled(self):
        """
        Test that when USE_DYNAMIC_SIZE is False, 
        calculate_dynamic_amount_usdt returns None (forcing use of default amount).
        """
        # Patch the config variable in the imported module 'config'
        with patch('config.USE_DYNAMIC_SIZE', False):
            # Run async test
            result = asyncio.run(self.executor.calculate_dynamic_amount_usdt('BTC/USDT', 10))
            
            # Expect None because logic is: if not config.USE_DYNAMIC_SIZE: return None
            self.assertIsNone(result, "Should return None when Dynamic Size is DISABLED")
            print("\n[TEST] Dynamic Size OFF -> Result: None (PASSED)")

    def test_strategy_protocol_present(self):
        """
        Verify that the new prompt always contains the Strategy Selection Protocol.
        """
        tech_data = {'price': 50000, 'atr': 100}
        sentiment_data = {}
        onchain_data = {}
        
        # No patch needed, strategy protocol is always standard now
        prompt = build_market_prompt("BTC/USDT", tech_data, sentiment_data, onchain_data)
        
        self.assertIn("FINAL INSTRUCTIONS (STRATEGY SELECTION PROTOCOL)", prompt, "Prompt should contain standard Strategy Selection Protocol")
        print("[TEST] Strategy Selection Protocol Present (PASSED)")

if __name__ == '__main__':
    unittest.main()

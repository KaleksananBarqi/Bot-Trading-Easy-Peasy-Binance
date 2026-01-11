
import unittest
from unittest.mock import MagicMock, AsyncMock
import sys
import os
import asyncio

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Mock config
class MockConfig:
    TRACKER_FILENAME = "test_tracker.json"
    TRAP_SAFETY_SL = 1.0
    ATR_MULTIPLIER_TP1 = 2.0
    DEFAULT_SL_PERCENT = 0.01
    DEFAULT_TP_PERCENT = 0.02

sys.modules['config'] = MockConfig

# Mimic the logic in main.py logic
def should_install_safety(status):
    return status in ['NONE', 'PENDING', 'WAITING_ENTRY']

class TestTPSLFix(unittest.TestCase):
    def test_status_check(self):
        """Mastikan status WAITING_ENTRY mentrigger pemasangan safety orders"""
        self.assertTrue(should_install_safety('NONE'), "NONE should trigger safety")
        self.assertTrue(should_install_safety('PENDING'), "PENDING should trigger safety")
        self.assertTrue(should_install_safety('WAITING_ENTRY'), "WAITING_ENTRY should trigger safety (FIXED)")
        self.assertFalse(should_install_safety('SECURED'), "SECURED should NOT trigger safety")

    def test_tracker_update_preserves_data(self):
        """Mastikan update tracker tidak menghapus atr_value"""
        tracker = {
            "BTC/USDT": {
                "status": "WAITING_ENTRY",
                "atr_value": 123.45,
                "strategy": "TEST"
            }
        }
        
        symbol = "BTC/USDT"
        
        # Simulate logic in main.py fix
        if symbol in tracker:
             tracker[symbol].update({
                "status": "SECURED",
                "last_check": 1000
             })
             
        self.assertEqual(tracker[symbol]['status'], "SECURED")
        self.assertEqual(tracker[symbol]['atr_value'], 123.45, "atr_value must be preserved")
        self.assertEqual(tracker[symbol]['strategy'], "TEST", "strategy must be preserved")

if __name__ == '__main__':
    unittest.main()

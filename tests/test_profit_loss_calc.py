"""
Unit Test untuk fungsi calculate_profit_loss_estimation
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.utils.calc import calculate_profit_loss_estimation


def test_long_position_profit_loss():
    """Test kalkulasi untuk posisi LONG (BUY)"""
    result = calculate_profit_loss_estimation(
        entry_price=100.0,
        tp_price=110.0,    # +10%
        sl_price=95.0,     # -5%
        side='buy',
        amount_usdt=10.0,  # $10 margin
        leverage=10        # 10x leverage
    )
    
    # Position size = 10 * 10 = $100
    # Qty = 100 / 100 = 1 unit
    # Profit = 1 * (110 - 100) = $10
    # Loss = 1 * (100 - 95) = $5
    # Profit % = (10 / 10) * 100 = 100%
    # Loss % = (5 / 10) * 100 = 50%
    
    assert result['profit_usdt'] == 10.0, f"Expected profit $10, got ${result['profit_usdt']}"
    assert result['loss_usdt'] == 5.0, f"Expected loss $5, got ${result['loss_usdt']}"
    assert result['profit_percent'] == 100.0, f"Expected profit 100%, got {result['profit_percent']}%"
    assert result['loss_percent'] == 50.0, f"Expected loss 50%, got {result['loss_percent']}%"
    
    print("[PASS] test_long_position_profit_loss PASSED")


def test_short_position_profit_loss():
    """Test kalkulasi untuk posisi SHORT (SELL)"""
    result = calculate_profit_loss_estimation(
        entry_price=100.0,
        tp_price=90.0,     # -10% (profit for short)
        sl_price=105.0,    # +5% (loss for short)
        side='sell',
        amount_usdt=20.0,  # $20 margin
        leverage=5         # 5x leverage
    )
    
    # Position size = 20 * 5 = $100
    # Qty = 100 / 100 = 1 unit
    # Profit = 1 * (100 - 90) = $10
    # Loss = 1 * (105 - 100) = $5
    # Profit % = (10 / 20) * 100 = 50%
    # Loss % = (5 / 20) * 100 = 25%
    
    assert result['profit_usdt'] == 10.0, f"Expected profit $10, got ${result['profit_usdt']}"
    assert result['loss_usdt'] == 5.0, f"Expected loss $5, got ${result['loss_usdt']}"
    assert result['profit_percent'] == 50.0, f"Expected profit 50%, got {result['profit_percent']}%"
    assert result['loss_percent'] == 25.0, f"Expected loss 25%, got {result['loss_percent']}%"
    
    print("[PASS] test_short_position_profit_loss PASSED")


def test_high_leverage_calculation():
    """Test dengan leverage tinggi"""
    result = calculate_profit_loss_estimation(
        entry_price=50000.0,  # BTC-like price
        tp_price=51500.0,     # +3%
        sl_price=49000.0,     # -2%
        side='buy',
        amount_usdt=100.0,    # $100 margin
        leverage=20           # 20x leverage
    )
    
    # Position size = 100 * 20 = $2000
    # Qty = 2000 / 50000 = 0.04 BTC
    # Profit = 0.04 * (51500 - 50000) = 0.04 * 1500 = $60
    # Loss = 0.04 * (50000 - 49000) = 0.04 * 1000 = $40
    # Profit % = (60 / 100) * 100 = 60%
    # Loss % = (40 / 100) * 100 = 40%
    
    assert result['profit_usdt'] == 60.0, f"Expected profit $60, got ${result['profit_usdt']}"
    assert result['loss_usdt'] == 40.0, f"Expected loss $40, got ${result['loss_usdt']}"
    assert result['profit_percent'] == 60.0, f"Expected profit 60%, got {result['profit_percent']}%"
    assert result['loss_percent'] == 40.0, f"Expected loss 40%, got {result['loss_percent']}%"
    
    print("[PASS] test_high_leverage_calculation PASSED")


def test_edge_case_zero_values():
    """Test edge case dengan nilai 0"""
    result = calculate_profit_loss_estimation(
        entry_price=0,
        tp_price=100.0,
        sl_price=90.0,
        side='buy',
        amount_usdt=10.0,
        leverage=10
    )
    
    assert result['profit_usdt'] == 0.0
    assert result['loss_usdt'] == 0.0
    assert result['profit_percent'] == 0.0
    assert result['loss_percent'] == 0.0
    
    print("[PASS] test_edge_case_zero_values PASSED")


def test_small_margin_calculation():
    """Test dengan margin kecil ($5)"""
    result = calculate_profit_loss_estimation(
        entry_price=1.0,      # Low price coin
        tp_price=1.1,         # +10%
        sl_price=0.95,        # -5%
        side='buy',
        amount_usdt=5.0,      # $5 margin (minimum)
        leverage=10
    )
    
    # Position size = 5 * 10 = $50
    # Qty = 50 / 1 = 50 units
    # Profit = 50 * (1.1 - 1) = 50 * 0.1 = $5
    # Loss = 50 * (1 - 0.95) = 50 * 0.05 = $2.5
    # Profit % = (5 / 5) * 100 = 100%
    # Loss % = (2.5 / 5) * 100 = 50%
    
    assert result['profit_usdt'] == 5.0, f"Expected profit $5, got ${result['profit_usdt']}"
    assert result['loss_usdt'] == 2.5, f"Expected loss $2.5, got ${result['loss_usdt']}"
    assert result['profit_percent'] == 100.0, f"Expected profit 100%, got {result['profit_percent']}%"
    assert result['loss_percent'] == 50.0, f"Expected loss 50%, got {result['loss_percent']}%"
    
    print("[PASS] test_small_margin_calculation PASSED")


if __name__ == '__main__':
    test_long_position_profit_loss()
    test_short_position_profit_loss()
    test_high_leverage_calculation()
    test_edge_case_zero_values()
    test_small_margin_calculation()
    print("\n[SUCCESS] All tests passed!")

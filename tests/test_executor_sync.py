import pytest
import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root AND src to path to handle mixed imports (import config vs from src...)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.append(src_path)

from src.modules.executor import OrderExecutor

@pytest.mark.asyncio
async def test_sync_pending_orders_filled_and_cancelled():
    # 1. Setup Mock Exchange
    mock_exchange = MagicMock()
    # Return empty list means NO open orders exist on exchange
    mock_exchange.fetch_open_orders = AsyncMock(return_value=[])

    # 2. Setup Executor
    executor = OrderExecutor(mock_exchange)

    # Mock save_tracker to avoid file I/O and verify calls
    executor.save_tracker = AsyncMock()
    # Mock kirim_tele
    with patch('src.modules.executor.kirim_tele', new_callable=AsyncMock) as mock_tele:

        # Mock position cache to simulate filled orders
        # Let's verify Case A: Filled
        executor.position_cache = {
            'BTC': {'contracts': 1.0}
        }

        # Setup Tracker with multiple orders
        executor.safety_orders_tracker = {
            'BTC/USDT': {
                'status': 'WAITING_ENTRY',
                'entry_id': '123'
            },
            'ETH/USDT': {
                'status': 'WAITING_ENTRY',
                'entry_id': '456'
            }
        }

        # 3. Run Sync
        await executor.sync_pending_orders()

        # 4. Verify Results

        # BTC/USDT: entry_id '123' not in [], so missing on exchange.
        # BTC in position_cache -> Status should be PENDING (Filled).
        assert executor.safety_orders_tracker['BTC/USDT']['status'] == 'PENDING'

        # ETH/USDT: entry_id '456' not in [], so missing on exchange.
        # ETH not in position_cache -> Should be deleted (Cancelled).
        assert 'ETH/USDT' not in executor.safety_orders_tracker

        # Verify save_tracker called exactly once
        assert executor.save_tracker.call_count == 1

        # Verify fetch_open_orders called EXACTLY ONCE (Optimization)
        assert mock_exchange.fetch_open_orders.call_count == 1
        mock_exchange.fetch_open_orders.assert_called_with()

@pytest.mark.asyncio
async def test_sync_pending_orders_still_open():
    # 1. Setup Mock Exchange
    mock_exchange = MagicMock()
    # Simulate: BTC order is still open, ETH order is missing
    mock_exchange.fetch_open_orders = AsyncMock(return_value=[
        {'id': '123', 'symbol': 'BTC/USDT'}
    ])

    # 2. Setup Executor
    executor = OrderExecutor(mock_exchange)
    executor.save_tracker = AsyncMock()

    # Mock position cache (Empty)
    executor.position_cache = {}

    with patch('src.modules.executor.kirim_tele', new_callable=AsyncMock):
        # Setup Tracker
        executor.safety_orders_tracker = {
            'BTC/USDT': {
                'status': 'WAITING_ENTRY',
                'entry_id': '123'
            },
            'ETH/USDT': {
                'status': 'WAITING_ENTRY',
                'entry_id': '456'
            }
        }

        # 3. Run Sync
        await executor.sync_pending_orders()

        # 4. Verify Results

        # BTC/USDT: '123' IS in open orders. Should remain WAITING_ENTRY.
        assert 'BTC/USDT' in executor.safety_orders_tracker
        assert executor.safety_orders_tracker['BTC/USDT']['status'] == 'WAITING_ENTRY'

        # ETH/USDT: '456' NOT in open orders. Should be deleted (Cancelled).
        assert 'ETH/USDT' not in executor.safety_orders_tracker

        # Verify save_tracker called (because ETH was modified)
        assert executor.save_tracker.call_count == 1

        # Verify single API call
        assert mock_exchange.fetch_open_orders.call_count == 1

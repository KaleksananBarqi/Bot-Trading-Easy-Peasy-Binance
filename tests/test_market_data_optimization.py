
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os

# Add project root AND src to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.modules.market_data import MarketDataManager
import config

@pytest.mark.asyncio
async def test_maintain_slow_data_uses_bulk_fetch():
    # Mock config to have a few coins
    with patch('config.DAFTAR_KOIN', [{'symbol': 'BTC/USDT'}, {'symbol': 'ETH/USDT'}]), \
         patch('config.CONCURRENCY_LIMIT', 5):

        # Mock Exchange
        mock_exchange = AsyncMock()
        mock_exchange.fetch_funding_rates.return_value = {
            'BTC/USDT': {'symbol': 'BTC/USDT', 'fundingRate': 0.0001},
            'ETH/USDT': {'symbol': 'ETH/USDT', 'fundingRate': 0.0002},
            'SOL/USDT': {'symbol': 'SOL/USDT', 'fundingRate': 0.0003} # Should be ignored
        }
        mock_exchange.fetch_open_interest.return_value = {'openInterestAmount': 1000.0}
        mock_exchange.fapiDataGetTopLongShortAccountRatio.return_value = [{'longShortRatio': 1.5}]

        # Initialize Manager
        manager = MarketDataManager(mock_exchange)

        # Mock other methods to avoid side effects (though they are async, so maybe not strictly needed if we don't await them?)
        # Actually _maintain_slow_data calls _update_funding_rates_bulk and then loops tasks.
        # We need to test the logic inside _maintain_slow_data mostly, or just test the sub-methods.

        # Let's test _update_funding_rates_bulk directly first
        await manager._update_funding_rates_bulk()

        # Verify call
        mock_exchange.fetch_funding_rates.assert_called_once()

        # Verify data update and filtering
        assert manager.funding_rates['BTC/USDT'] == 0.0001
        assert manager.funding_rates['ETH/USDT'] == 0.0002
        assert 'SOL/USDT' not in manager.funding_rates

        # Now test _update_single_coin_slow_data to ensure it DOES NOT call fetch_funding_rate
        mock_exchange.fetch_funding_rate.reset_mock()

        await manager._update_single_coin_slow_data({'symbol': 'BTC/USDT'})

        # Verify it fetched OI and LSR
        mock_exchange.fetch_open_interest.assert_called()
        # Verify it DID NOT fetch funding rate
        mock_exchange.fetch_funding_rate.assert_not_called()

if __name__ == "__main__":
    asyncio.run(test_maintain_slow_data_uses_bulk_fetch())

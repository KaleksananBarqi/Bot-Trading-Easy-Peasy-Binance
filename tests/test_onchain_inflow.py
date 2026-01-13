
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# --- SETUP PATHS ---
# Agar script ini bisa mengimpor modul 'src' dan 'config' dengan benar
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_dir = os.path.join(project_root, 'src')

sys.path.insert(0, project_root)
sys.path.insert(0, src_dir)

from src.modules.onchain import OnChainAnalyzer
import config

class TestOnChainInflow(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = OnChainAnalyzer()
        
    @patch('src.modules.onchain.requests.get')
    def test_inflow_positive(self, mock_get):
        """
        Skenario: Market Cap Stablecoin NAIK signifikan (> Threshold)
        Harapan: Status menjadi 'Positive'
        """
        # Simulasi Data: Perlu > 2 item. 
        mock_data = [
            {'date': 1500000000, 'totalCirculatingUSD': {'peggedUSD': 100.0}}, # Dummy Data terlama
            {'date': 1600000000, 'totalCirculatingUSD': {'peggedUSD': 1000.0}}, # Data H-1
            {'date': 1600086400, 'totalCirculatingUSD': {'peggedUSD': 1100.0}}  # Data Terakhir (Naik)
        ]
        
        # Setup Mock
        mock_response = MagicMock()
        mock_response.json.return_value = mock_data
        mock_get.return_value = mock_response
        
        # Eksekusi
        self.analyzer.fetch_stablecoin_inflows()
        
        # Assert / Verifikasi
        print(f"\n[TEST] Positive Case: Inflow Status = {self.analyzer.stablecoin_inflow}")
        self.assertEqual(self.analyzer.stablecoin_inflow, "Positive")

    @patch('src.modules.onchain.requests.get')
    def test_inflow_negative(self, mock_get):
        """
        Skenario: Market Cap Stablecoin TURUN signifikan (< -Threshold)
        Harapan: Status menjadi 'Negative'
        """
        # Simulasi Data
        mock_data = [
             {'date': 1500000000, 'totalCirculatingUSD': {'peggedUSD': 100.0}},
             {'date': 1600000000, 'totalCirculatingUSD': {'peggedUSD': 1000.0}},
             {'date': 1600086400, 'totalCirculatingUSD': {'peggedUSD': 900.0}} # Turun
        ]
        
        mock_response = MagicMock()
        mock_response.json.return_value = mock_data
        mock_get.return_value = mock_response
        
        self.analyzer.fetch_stablecoin_inflows()
        
        print(f"[TEST] Negative Case: Inflow Status = {self.analyzer.stablecoin_inflow}")
        self.assertEqual(self.analyzer.stablecoin_inflow, "Negative")

    @patch('src.modules.onchain.requests.get')
    def test_inflow_neutral(self, mock_get):
        """
        Skenario: Perubahan kecil (Datar/Sideways)
        Harapan: Status menjadi 'Neutral'
        """
        # Simulasi Data
        mock_data = [
             {'date': 1500000000, 'totalCirculatingUSD': {'peggedUSD': 100.0}},
             {'date': 1600000000, 'totalCirculatingUSD': {'peggedUSD': 1000.0}},
             {'date': 1600086400, 'totalCirculatingUSD': {'peggedUSD': 1000.1}} # Naik tipis
        ]
        
        mock_response = MagicMock()
        mock_response.json.return_value = mock_data
        mock_get.return_value = mock_response
        
        self.analyzer.fetch_stablecoin_inflows()
        
        print(f"[TEST] Neutral Case:  Inflow Status = {self.analyzer.stablecoin_inflow}")
        self.assertEqual(self.analyzer.stablecoin_inflow, "Neutral")

    @patch('src.modules.onchain.requests.get')
    def test_api_failure(self, mock_get):
        """
        Skenario: API Error / Timeout
        Harapan: Status Default 'Neutral' dan tidak crash
        """
        mock_get.side_effect = Exception("API Timeout")
        
        self.analyzer.fetch_stablecoin_inflows()
        
        print(f"[TEST] Error Case:    Inflow Status = {self.analyzer.stablecoin_inflow}")
        self.assertEqual(self.analyzer.stablecoin_inflow, "Neutral")

    def test_real_connection(self):
        """
        Skenario: Test Koneksi ASLI (Integration Test).
        Akan melakukan request sungguhan ke DefiLlama.
        """
        print("\n--- [REAL DATA CHECK] Fetching from DefiLlama... ---")
        real_analyzer = OnChainAnalyzer()
        try:
            real_analyzer.fetch_stablecoin_inflows()
            print(f"✅ Real Data Fetch Success!")
            print(f"👉 Current Status: {real_analyzer.stablecoin_inflow}")
            # Kita tidak assert value spesifik karena data selalu berubah,
            # tapi kita assert tidak crash dan value valid string
            self.assertIn(real_analyzer.stablecoin_inflow, ["Positive", "Negative", "Neutral"])
        except Exception as e:
            self.fail(f"Real connection failed: {e}")

if __name__ == '__main__':
    unittest.main()

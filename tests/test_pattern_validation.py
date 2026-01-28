"""
Unit Test untuk Validasi Pattern Recognition Output
Memastikan fungsi _is_valid_analysis bekerja dengan benar
"""

import unittest
import sys
import os

# Setup path agar bisa import module dari src
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)
sys.path.insert(0, project_root)

import config
from src.modules.pattern_recognizer import PatternRecognizer


class TestPatternValidation(unittest.TestCase):
    """Test suite untuk validasi output Vision AI pattern recognition"""
    
    def setUp(self):
        """Inisialisasi PatternRecognizer tanpa market_data (mock)"""
        self.recognizer = PatternRecognizer.__new__(PatternRecognizer)
        self.recognizer.client = None
        self.recognizer.cache = {}
        
    def test_valid_analysis_bullish(self):
        """Output valid dengan BULLISH keyword dan kalimat lengkap"""
        text = "The chart shows consolidation with a bullish bias. Price above EMA. Overall **BULLISH**."
        self.assertTrue(self.recognizer._is_valid_analysis(text))
    
    def test_valid_analysis_bearish(self):
        """Output valid dengan BEARISH keyword"""
        text = "Price is in downtrend. MACD shows bearish divergence. Strong resistance above. Bias: BEARISH."
        self.assertTrue(self.recognizer._is_valid_analysis(text))
    
    def test_valid_analysis_neutral(self):
        """Output valid dengan NEUTRAL keyword"""
        text = "The market is consolidating with no clear direction. Volume is low. Overall bias is NEUTRAL."
        self.assertTrue(self.recognizer._is_valid_analysis(text))
        
    def test_valid_analysis_ends_with_punctuation(self):
        """Output valid yang diakhiri tanda baca"""
        text = "The 30m chart shows consolidation pattern after strong uptrend. MACD bullish crossover. Bias: **BULLISH**."
        self.assertTrue(self.recognizer._is_valid_analysis(text))
    
    def test_valid_analysis_ends_with_asterisk(self):
        """Output valid yang diakhiri asterisk (markdown bold)"""
        text = "The chart shows a clear uptrend with higher highs. MACD positive. Overall bias is **BULLISH**"
        # Diakhiri asterisk bukan huruf, harusnya valid
        self.assertTrue(self.recognizer._is_valid_analysis(text))
    
    def test_invalid_empty(self):
        """Output kosong harus invalid"""
        self.assertFalse(self.recognizer._is_valid_analysis(""))
        self.assertFalse(self.recognizer._is_valid_analysis(None))
    
    def test_invalid_too_short(self):
        """Output terlalu pendek (di bawah minimum)"""
        text = "Bullish."
        self.assertFalse(self.recognizer._is_valid_analysis(text))
    
    def test_invalid_truncated_mid_word(self):
        """Output terpotong di tengah kata (berakhir huruf)"""
        text = "The MACD shows bullish crossover indicating a potential continuation of the bullish"
        self.assertFalse(self.recognizer._is_valid_analysis(text))
    
    def test_invalid_truncated_example_from_user(self):
        """Contoh output terpotong dari user request"""
        text = "To analyze the 30m chart for BTC/USDT, we will follow the given instructions and examine the chart for visual patterns and MACD divergence. The MACD Line is above the Signal Line, indicating a bullish"
        self.assertFalse(self.recognizer._is_valid_analysis(text))
    
    def test_invalid_no_bias_keyword(self):
        """Output tanpa keyword bias (BULLISH/BEARISH/NEUTRAL)"""
        text = "The chart shows a consolidation pattern with potential breakout. Volume is increasing. Watch for support level."
        self.assertFalse(self.recognizer._is_valid_analysis(text))
    
    def test_valid_long_analysis(self):
        """Output panjang dan lengkap"""
        text = ("The 30m chart for BTC/USDT shows a consolidation pattern after a strong uptrend, "
                "with the price oscillating around the 90,000 level. The MACD indicator shows a "
                "bullish crossover and a positive histogram, indicating a potential continuation "
                "of the uptrend. There is no clear divergence between the price and MACD histogram. "
                "The overall bias is **BULLISH**.")
        self.assertTrue(self.recognizer._is_valid_analysis(text))


class TestPatternConfig(unittest.TestCase):
    """Test untuk memastikan config validasi sudah benar"""
    
    def test_config_exists(self):
        """Pastikan semua config validasi tersedia"""
        self.assertTrue(hasattr(config, 'PATTERN_MAX_RETRIES'))
        self.assertTrue(hasattr(config, 'PATTERN_MIN_ANALYSIS_LENGTH'))
        self.assertTrue(hasattr(config, 'PATTERN_REQUIRED_KEYWORDS'))
    
    def test_config_values(self):
        """Pastikan nilai config masuk akal"""
        self.assertGreaterEqual(config.PATTERN_MAX_RETRIES, 1)
        self.assertGreaterEqual(config.PATTERN_MIN_ANALYSIS_LENGTH, 50)
        self.assertIn('BULLISH', config.PATTERN_REQUIRED_KEYWORDS)
        self.assertIn('BEARISH', config.PATTERN_REQUIRED_KEYWORDS)
        self.assertIn('NEUTRAL', config.PATTERN_REQUIRED_KEYWORDS)


if __name__ == '__main__':
    unittest.main(verbosity=2)

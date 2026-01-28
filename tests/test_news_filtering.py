"""
Unit Test untuk News Filtering Logic di SentimentAnalyzer
Test ini memvalidasi bahwa berita difilter dengan benar berdasarkan koin.
"""
import sys
import os
import unittest

# Add project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.modules.sentiment import SentimentAnalyzer, COIN_ALIASES


class TestNewsFiltering(unittest.TestCase):
    """Test filtering berita berdasarkan relevansi koin"""
    
    def setUp(self):
        """Setup mock data untuk testing"""
        self.analyzer = SentimentAnalyzer()
        # Mock raw news - simulasi output dari RSS feeds
        self.analyzer.raw_news = [
            "Bitcoin surges to new ATH amid ETF inflows (CoinDesk)",
            "PENGU Price Surges Despite 95% Sentiment Drop (TheBlock)",
            "XRP Could Enter New Growth Phase After SEC Ruling (CryptoSlate)",
            "Solana TVL hits $5B milestone as DeFi activity increases (Blockworks)",
            "Ethereum 2.0 staking rewards increase by 10% (BeInCrypto)",
            "Federal Reserve hints at rate cuts in Q2 (Google News)",
            "BTC whale moves $200M to exchange, sparking sell-off fears (U.Today)",
            "Dogecoin sees renewed interest from retail investors (DailyHodl)",
            "Cardano's Hydra upgrade promises 1M TPS (NewsBTC)",
            "Bitcoin miners report record hash rate after halving (Bitcoin.com)",
            "Arbitrum TVL surpasses $3B as layer 2 adoption grows (TheBlock)",
            "Chainlink CCIP expands to 10 new blockchains (CryptoSlate)",
        ]
    
    def test_filter_btc_only_gets_btc_news(self):
        """BTC harus dapat berita BTC saja, tidak termasuk altcoin"""
        result = self.analyzer.filter_news_by_relevance("BTC/USDT")
        
        # Harus ada berita Bitcoin
        btc_news_count = sum(1 for n in result if 'bitcoin' in n.lower() or 'btc' in n.lower())
        self.assertGreater(btc_news_count, 0, "Harusnya ada berita BTC")
        
        # Tidak boleh ada berita PENGU, XRP, atau altcoin lain
        self.assertFalse(any("pengu" in n.lower() for n in result), "PENGU tidak boleh ada di berita BTC")
        self.assertFalse(any("xrp" in n.lower() for n in result), "XRP tidak boleh ada di berita BTC")
        self.assertFalse(any("solana" in n.lower() for n in result), "Solana tidak boleh ada di berita BTC")
    
    def test_filter_sol_gets_sol_and_btc(self):
        """SOL harus dapat berita SOL + BTC (karena BTC selalu disertakan)"""
        result = self.analyzer.filter_news_by_relevance("SOL/USDT")
        
        # Harus ada berita Solana
        sol_news = [n for n in result if 'solana' in n.lower() or 'sol' in n.lower()]
        self.assertTrue(len(sol_news) > 0, "Harusnya ada berita Solana")
        
        # Harus ada berita BTC juga (BTC king effect)
        btc_news = [n for n in result if 'bitcoin' in n.lower() or 'btc' in n.lower()]
        self.assertTrue(len(btc_news) > 0, "Harusnya ada berita BTC untuk SOL")
        
        # Tidak boleh ada berita XRP (tidak relevan)
        self.assertFalse(any("xrp" in n.lower() for n in result), "XRP tidak boleh ada di berita SOL")
    
    def test_filter_eth_gets_ethereum_news(self):
        """ETH harus dapat berita dengan keyword 'ethereum' atau 'eth'"""
        result = self.analyzer.filter_news_by_relevance("ETH/USDT")
        
        eth_news = [n for n in result if 'ethereum' in n.lower()]
        self.assertTrue(len(eth_news) > 0, "Harusnya ada berita Ethereum")
    
    def test_filter_arb_gets_arbitrum_news(self):
        """ARB harus dapat berita Arbitrum"""
        result = self.analyzer.filter_news_by_relevance("ARB/USDT")
        
        arb_news = [n for n in result if 'arbitrum' in n.lower()]
        self.assertTrue(len(arb_news) > 0, "Harusnya ada berita Arbitrum")
    
    def test_filter_unknown_coin_fallback_to_btc(self):
        """Koin tidak dikenal harus tetap dapat berita BTC sebagai fallback"""
        result = self.analyzer.filter_news_by_relevance("UNKNOWN/USDT")
        
        # Meskipun koin tidak dikenal, BTC news harus tetap ada
        btc_news = [n for n in result if 'bitcoin' in n.lower() or 'btc' in n.lower()]
        self.assertTrue(len(btc_news) > 0, "Koin unknown harus tetap dapat berita BTC")
    
    def test_coin_aliases_are_defined(self):
        """Pastikan COIN_ALIASES berisi mapping yang diperlukan"""
        required_coins = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'ADA']
        for coin in required_coins:
            self.assertIn(coin, COIN_ALIASES, f"{coin} harus ada di COIN_ALIASES")
            self.assertTrue(len(COIN_ALIASES[coin]) > 0, f"{coin} harus punya alias")
    
    def test_get_latest_with_symbol_filters(self):
        """get_latest(symbol) harus mengembalikan berita terfilter"""
        result = self.analyzer.get_latest(symbol="SOL/USDT")
        
        self.assertIn('news', result)
        news = result['news']
        
        # Pastikan ada berita
        self.assertTrue(len(news) > 0, "Harusnya ada berita yang dikembalikan")
        
        # Pastikan tidak ada berita XRP (tidak relevan untuk SOL)
        self.assertFalse(any("xrp" in n.lower() for n in news), "XRP tidak boleh ada")
    
    def test_get_latest_without_symbol_returns_all(self):
        """get_latest() tanpa symbol harus mengembalikan last_news (backward compat)"""
        # Set last_news untuk testing
        self.analyzer.last_news = ["Test news 1", "Test news 2"]
        
        result = self.analyzer.get_latest()
        
        self.assertEqual(result['news'], self.analyzer.last_news)
    
    def test_empty_raw_news_returns_empty(self):
        """Jika raw_news kosong, filter harus return list kosong"""
        self.analyzer.raw_news = []
        result = self.analyzer.filter_news_by_relevance("BTC/USDT")
        
        self.assertEqual(result, [])


class TestCoinAliasesCompleteness(unittest.TestCase):
    """Test untuk memastikan COIN_ALIASES lengkap"""
    
    def test_btc_aliases(self):
        """BTC harus punya alias bitcoin dan btc"""
        self.assertIn('bitcoin', COIN_ALIASES['BTC'])
        self.assertIn('btc', COIN_ALIASES['BTC'])
    
    def test_popular_altcoins_have_aliases(self):
        """Altcoin populer harus punya alias yang benar"""
        test_cases = [
            ('ETH', ['ethereum', 'eth']),
            ('SOL', ['solana', 'sol']),
            ('DOGE', ['dogecoin', 'doge']),
            ('LINK', ['chainlink', 'link']),
        ]
        
        for coin, expected_aliases in test_cases:
            for alias in expected_aliases:
                self.assertIn(alias, COIN_ALIASES[coin], 
                             f"{alias} harus ada di alias {coin}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TESTING NEWS FILTERING LOGIC")
    print("="*60 + "\n")
    
    unittest.main(verbosity=2)

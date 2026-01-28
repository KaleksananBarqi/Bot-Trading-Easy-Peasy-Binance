import requests
import feedparser
import random
import config
from datetime import datetime
from typing import Optional
from src.utils.helper import logger

# Mapping nama alternatif koin populer untuk filtering berita
COIN_ALIASES = {
    'BTC': ['bitcoin', 'btc'],
    'ETH': ['ethereum', 'eth', 'ether'],
    'SOL': ['solana', 'sol'],
    'XRP': ['ripple', 'xrp'],
    'DOGE': ['dogecoin', 'doge'],
    'ADA': ['cardano', 'ada'],
    'BNB': ['binance coin', 'bnb'],
    'AVAX': ['avalanche', 'avax'],
    'DOT': ['polkadot', 'dot'],
    'MATIC': ['polygon', 'matic'],
    'LINK': ['chainlink', 'link'],
    'SHIB': ['shiba', 'shib'],
    'PEPE': ['pepe'],
    'ARB': ['arbitrum', 'arb'],
    'OP': ['optimism'],
    'SUI': ['sui'],
    'APT': ['aptos', 'apt'],
    'INJ': ['injective', 'inj'],
    'TIA': ['celestia', 'tia'],
    'SEI': ['sei'],
    'NEAR': ['near protocol', 'near'],
    'FTM': ['fantom', 'ftm'],
    'ATOM': ['cosmos', 'atom'],
    'LTC': ['litecoin', 'ltc'],
    'UNI': ['uniswap', 'uni'],
    'AAVE': ['aave'],
    'MKR': ['maker', 'mkr'],
    'CRV': ['curve', 'crv'],
    'LDO': ['lido', 'ldo'],
    'PENDLE': ['pendle'],
    'WIF': ['dogwifhat', 'wif'],
    'BONK': ['bonk'],
    'FLOKI': ['floki'],
    'RENDER': ['render', 'rndr'],
    'FET': ['fetch.ai', 'fet', 'artificial superintelligence'],
    'AGIX': ['singularitynet', 'agix'],
    'TAO': ['bittensor', 'tao'],
    'WLD': ['worldcoin', 'wld'],
    'AI': ['ai token'],
}


class SentimentAnalyzer:
    def __init__(self):
        self.fng_url = config.CMC_FNG_URL
        self.last_fng = {"value": 50, "classification": "Neutral"}
        self.last_news = []       # Backward compat
        self.raw_news = []        # Berita mentah (unfiltered) untuk filtering per koin

    def fetch_fng(self):
        """Fetch Fear & Greed Index from CoinMarketCap"""
        try:
            headers = {
                'X-CMC_PRO_API_KEY': config.CMC_API_KEY,
                'Accept': 'application/json'
            }
            params = {}
            
            if not config.CMC_API_KEY:
                logger.warning("⚠️ CMC_API_KEY not found. Using default neutral sentiment.")
                return

            resp = requests.get(self.fng_url, headers=headers, params=params, timeout=config.API_REQUEST_TIMEOUT)
            data = resp.json()
            
            if 'status' in data and int(data['status']['error_code']) == 0 and 'data' in data:
                if isinstance(data['data'], list) and len(data['data']) > 0:
                    item = data['data'][0]
                elif isinstance(data['data'], dict):
                    item = data['data']
                else:
                    logger.warning(f"⚠️ CMC API Unexpected Data Format: {data['data']}")
                    return

                self.last_fng = {
                    "value": int(item['value']),
                    "classification": item['value_classification']
                }
                logger.info(f"🧠 Sentiment F&G (CMC): {self.last_fng['value']} ({self.last_fng['classification']})")
            else:
                error_msg = data.get('status', {}).get('error_message')
                logger.warning(f"⚠️ CMC API Error: {error_msg if error_msg else data}")

        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch F&G: {e}")

    def fetch_news(self):
        """Fetch Top News from RSS Feeds dan simpan ke raw_news untuk filtering"""
        rss_urls = getattr(config, 'RSS_FEED_URLS', [])
        if not rss_urls:
            logger.warning("⚠️ No RSS URLs configured in config.")
            return

        all_news = []
        max_per_source = config.NEWS_MAX_PER_SOURCE
        max_age_hours = getattr(config, 'NEWS_MAX_AGE_HOURS', 6) 
        max_total = getattr(config, 'NEWS_MAX_TOTAL', 30)
        
        for url in rss_urls:
            try:
                logger.info(f"🌐 Fetching RSS: {url}")
                response = requests.get(url, timeout=config.API_REQUEST_TIMEOUT)
                feed = feedparser.parse(response.content)
                
                if feed.bozo and hasattr(feed, 'bozo_exception'):
                     pass
                     
                if not feed.entries:
                    continue

                source_name = feed.feed.get('title', 'Unknown Source')
                
                count = 0
                for entry in feed.entries:
                    if count >= max_per_source:
                        break
                    
                    is_recent = True
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        try:
                            published_dt = datetime(*entry.published_parsed[:6])
                            age_seconds = (datetime.utcnow() - published_dt).total_seconds()
                            if age_seconds > (max_age_hours * 3600):
                                is_recent = False
                        except Exception:
                            pass
                    
                    if is_recent:
                        title = entry.title
                        all_news.append(f"{title} ({source_name})")
                        count += 1
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to fetch RSS {url}: {e}")

        random.shuffle(all_news)
        
        # Simpan ke raw_news (lebih banyak untuk filtering per koin)
        self.raw_news = all_news[:max_total]
        
        # Backward compatibility - fallback untuk legacy call tanpa symbol
        self.last_news = self.raw_news[:config.NEWS_RETENTION_LIMIT]
        
        logger.info(f"📰 News Fetched: {len(self.raw_news)} headlines aggregated from RSS.")

    def filter_news_by_relevance(self, symbol: str) -> list:
        """
        Filter berita berdasarkan relevansi dengan koin.
        
        BTC news SELALU disertakan untuk semua koin karena BTC adalah market leader.
        
        Args:
            symbol: Trading pair (e.g. "SOL/USDT", "BTC/USDT")
        
        Returns:
            List berita yang relevan (max NEWS_RETENTION_LIMIT)
        """
        if not self.raw_news:
            return []
        
        # Ekstrak base coin (SOL dari SOL/USDT)
        base_coin = symbol.split('/')[0].upper()
        
        # Keywords untuk koin target
        target_keywords = COIN_ALIASES.get(base_coin, [base_coin.lower()])
        
        # BTC keywords (SELALU include karena BTC king effect)
        btc_keywords = COIN_ALIASES.get('BTC', ['bitcoin', 'btc'])
        
        # Jika koin adalah BTC sendiri, hanya cari BTC news
        is_btc = base_coin == 'BTC'
        
        relevant = []
        for news in self.raw_news:
            news_lower = news.lower()
            
            # Match: Target Coin OR BTC (BTC selalu masuk)
            is_target_match = any(kw in news_lower for kw in target_keywords)
            is_btc_match = any(kw in news_lower for kw in btc_keywords)
            
            if is_btc:
                # Untuk BTC, hanya ambil berita BTC
                if is_btc_match:
                    relevant.append(news)
            else:
                # Untuk altcoin, ambil berita koin tsb + BTC
                if is_target_match or is_btc_match:
                    relevant.append(news)
        
        return relevant[:config.NEWS_RETENTION_LIMIT]

    def get_latest(self, symbol: Optional[str] = None) -> dict:
        """
        Get latest sentiment data.
        
        Args:
            symbol: Optional. Jika diberikan, filter berita berdasarkan relevansi koin.
                    Contoh: "SOL/USDT" akan mendapat berita SOL + BTC.
        
        Returns:
            Dict dengan fng_value, fng_text, dan news (terfilter jika symbol diberikan)
        """
        # Default ke last_news (backward compat)
        news = self.last_news
        
        # Jika symbol diberikan dan ada raw_news, filter berdasarkan relevansi
        if symbol and self.raw_news:
            news = self.filter_news_by_relevance(symbol)
            
            # Jika tidak ada berita relevan, fallback ke berita BTC saja
            if not news:
                btc_keywords = COIN_ALIASES.get('BTC', ['bitcoin', 'btc'])
                news = [n for n in self.raw_news if any(kw in n.lower() for kw in btc_keywords)][:config.NEWS_RETENTION_LIMIT]
        
        return {
            "fng_value": self.last_fng['value'],
            "fng_text": self.last_fng['classification'],
            "news": news
        }

    def update_all(self):
        self.fetch_fng()
        self.fetch_news()

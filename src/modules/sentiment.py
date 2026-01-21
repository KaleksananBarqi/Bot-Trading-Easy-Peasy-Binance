import requests
import feedparser
import random
import config
from datetime import datetime, timedelta
from src.utils.helper import logger

class SentimentAnalyzer:
    def __init__(self):
        self.fng_url = config.CMC_FNG_URL
        self.last_fng = {"value": 50, "classification": "Neutral"}
        self.last_news = []

    def fetch_fng(self):
        """Fetch Fear & Greed Index from CoinMarketCap"""
        try:
            headers = {
                'X-CMC_PRO_API_KEY': config.CMC_API_KEY,
                'Accept': 'application/json'
            }
            # Endpoint /latest tidak butuh limit
            params = {}
            
            if not config.CMC_API_KEY:
                logger.warning("⚠️ CMC_API_KEY not found. Using default neutral sentiment.")
                return

            resp = requests.get(self.fng_url, headers=headers, params=params, timeout=config.API_REQUEST_TIMEOUT)
            data = resp.json()
            
            # Error code bisa integer 0 atau string "0"
            if 'status' in data and int(data['status']['error_code']) == 0 and 'data' in data:
                # Handle response format (bisa dict atau list tergantung endpoint)
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
        """Fetch Top News from RSS Feeds"""
        rss_urls = getattr(config, 'RSS_FEED_URLS', [])
        if not rss_urls:
            logger.warning("⚠️ No RSS URLs configured in config.")
            return

        all_news = []
        max_per_source = config.NEWS_MAX_PER_SOURCE # Ambil sedikit per source agar variatif
        max_age_hours = getattr(config, 'NEWS_MAX_AGE_HOURS', 1) 
        
        for url in rss_urls:
            try:
                logger.info(f"🌐 Fetching RSS: {url}")
                # Use requests with timeout to avoid hanging
                response = requests.get(url, timeout=config.API_REQUEST_TIMEOUT)
                feed = feedparser.parse(response.content)
                
                # Check status (bozo bit)
                if feed.bozo and hasattr(feed, 'bozo_exception'):
                     # Logger warning di skip agar log tidak penuh, best effort saja
                     pass
                     
                if not feed.entries:
                    continue

                source_name = feed.feed.get('title', 'Unknown Source')
                
                # Filter dan ambil N berita terbaru
                count = 0
                for entry in feed.entries:
                    if count >= max_per_source:
                        break
                    
                    # Logika Filter Waktu (1 Jam Terakhir)
                    is_recent = True
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        try:
                            # feedparser returns UTC struct_time
                            published_dt = datetime(*entry.published_parsed[:6])
                            # Bandingkan dengan UTC Now
                            age_seconds = (datetime.utcnow() - published_dt).total_seconds()
                            if age_seconds > (max_age_hours * 3600):
                                is_recent = False
                        except Exception:
                            pass # Jika gagal parse tanggal, anggap relevant (fallback)
                    
                    if is_recent:
                        title = entry.title
                        all_news.append(f"{title} ({source_name})")
                        count += 1
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to fetch RSS {url}: {e}")

        # Acak hasil gabungan agar prompt mendapat variasi topik
        random.shuffle(all_news)
        
        # Batasi total berita yang disimpan (misal top 15) agar prompt tidak kepanjangan
        self.last_news = all_news[:config.NEWS_RETENTION_LIMIT]
        
        logger.info(f"📰 News Fetched: {len(self.last_news)} headlines aggregated from RSS.")

    def get_latest(self):
        return {
            "fng_value": self.last_fng['value'],
            "fng_text": self.last_fng['classification'],
            "news": self.last_news
        }

    def update_all(self):
        self.fetch_fng()
        self.fetch_news()

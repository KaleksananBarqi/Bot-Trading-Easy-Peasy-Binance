import sys
import os

# Tambahkan root directory ke path agar modules bisa diimport
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'src'))

from src.modules.sentiment import SentimentAnalyzer
from src import config
import logging

# Setup logging ke console
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_sentiment_fng():
    print("--- Testing Sentiment F&G Source ---")
    analyzer = SentimentAnalyzer()
    
    print(f"URL: {analyzer.fng_url}")
    print(f"Current Config Key Present: {bool(config.CMC_API_KEY)}")
    
    if not config.CMC_API_KEY:
        print("⚠️  No CMC_API_KEY found in env. Expected to fail/warn.")
    
    analyzer.fetch_fng()
    
    result = analyzer.get_latest()
    print("\nResult:")
    print(result)

if __name__ == "__main__":
    test_sentiment_fng()

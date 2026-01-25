import sys
import os
import base64
import random
import time
import pandas as pd

# Setup Path
# Assuming script is in tests/test_chart_generation.py
# Root is# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')

print(f"Adding to sys.path: {project_root}")
sys.path.append(project_root)
print(f"Adding to sys.path: {src_path}")
sys.path.append(src_path)

# Mock config availability for pattern_recognizer
# pattern_recognizer does 'import config', so src must be in path
try:
    # Try importing from src.modules first (standard)
    try:
        from src.modules.pattern_recognizer import PatternRecognizer
    except ImportError:
        # Fallback if src is not package
        from modules.pattern_recognizer import PatternRecognizer
        
    import config
    # Ensure config values are what we expect
    print(f"Config Loaded - MACD: {config.MACD_FAST}/{config.MACD_SLOW}/{config.MACD_SIGNAL}")
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

class MockMarketData:
    def __init__(self, data):
        self.market_store = data

def generate_dummy_candles(count=100):
    candles = []
    base_price = 50000.0
    now = int(time.time() * 1000)
    
    for i in range(count):
        ts = now - (count - i) * 60 * 30 * 1000 # 30m candles
        change = random.uniform(-100, 100)
        open_p = base_price
        close_p = base_price + change
        high_p = max(open_p, close_p) + random.uniform(0, 50)
        low_p = min(open_p, close_p) - random.uniform(0, 50)
        vol = random.uniform(10, 100)
        
        candles.append([ts, open_p, high_p, low_p, close_p, vol])
        base_price = close_p
        
    return candles

def test_chart_generation():
    print("Testing Chart Generation...")
    
    # Prepare Data
    symbol = "BTC/USDT"
    candles = generate_dummy_candles(100)
    
    # Mock Manager
    market_data = {symbol: {config.TIMEFRAME_SETUP: candles}}
    mock_manager = MockMarketData(market_data)
    
    # Initialize Recognizer
    recognizer = PatternRecognizer(mock_manager)
    
    # Generate Chart
    img_base64 = recognizer.generate_chart_image(symbol)
    
    if img_base64:
        print("✅ Chart generated successfully!")
        
        # Save to file
        output_file = os.path.join(current_dir, f"chart_{symbol.replace('/','-')}.png")
        with open(output_file, "wb") as f:
            f.write(base64.b64decode(img_base64))
        print(f"✅ Saved chart to: {output_file}")
        print("Please Check the image manually to verify colors (Green=Up, Red=Down) and MACD lines.")
    else:
        print("❌ Failed to generate chart (result is None).")

if __name__ == "__main__":
    test_chart_generation()

import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time

# --- KONFIGURASI ---
SYMBOL = 'BTC/USDT'
TIMEFRAME = '15m'
HARI_MUNDUR = 365  # Ambil data 1 TAHUN ke belakang

print(f"--- 📥 SEDANG DOWNLOAD DATA {HARI_MUNDUR} HARI... ---")

exchange = ccxt.binance()
limit = 1000 # Limit maksimal binance per request
since = exchange.parse8601((datetime.now() - timedelta(days=HARI_MUNDUR)).strftime('%Y-%m-%d %H:%M:%S'))

all_candles = []

while True:
    try:
        # Download per 1000 candle
        candles = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=limit, since=since)
        
        if not candles:
            break
            
        all_candles += candles
        
        # Update waktu 'since' untuk request berikutnya
        since = candles[-1][0] + 1 
        
        print(f"   > Terambil: {len(all_candles)} candle... (Tgl: {pd.to_datetime(candles[-1][0], unit='ms')})")
        
        # Stop kalau sudah sampai hari ini
        if len(candles) < limit:
            break
            
        # Istirahat dikit biar gak diblokir binance
        time.sleep(0.5)
        
    except Exception as e:
        print(f"Error: {e}")
        break

# Simpan ke CSV
df = pd.DataFrame(all_candles, columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume'])
df['Time'] = pd.to_datetime(df['Time'], unit='ms')

# Bersihkan duplikat
df = df.drop_duplicates(subset=['Time'])

nama_file = f"data_{SYMBOL.replace('/', '')}_{TIMEFRAME}_1tahun.csv"
df.to_csv(nama_file, index=False)

print(f"\n✅ SELESAI! Total Data: {len(df)} Candle.")
print(f"Disimpan di: {nama_file}")
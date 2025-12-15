import ccxt
import pandas as pd
import pandas_ta as ta

# Setup Exchange
exchange = ccxt.binance()

print("Menganalisa Liquidity Grab pada BTC/USDT...")

# 1. Ambil Data lebih banyak (misal 100 candle 1 jam)
bars = exchange.fetch_ohlcv('BTC/USDT', timeframe='1h', limit=100)
df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
df['time'] = pd.to_datetime(df['time'], unit='ms')

# 2. Tentukan Area Likuiditas (Support Terkuat dalam 20 jam terakhir)
# Kita cari nilai Low terendah dalam periode candle ke-20 sampai candle ke-2 yang lalu (jangan hitung candle sekarang)
window_liquidity = 20 

# Rolling min akan mencari nilai terendah, shift(1) agar tidak menghitung candle yang sedang berjalan
df['low_liquidity_area'] = df['low'].rolling(window=window_liquidity).min().shift(1)

# 3. Ambil data candle terakhir (yang sedang aktif/baru tutup)
last_candle = df.iloc[-1]
support_area = last_candle['low_liquidity_area']

print(f"Waktu: {last_candle['time']}")
print(f"Area Stop Loss Ritel (Support 20 Jam): ${support_area}")
print(f"Low Candle Terakhir: ${last_candle['low']}")
print(f"Close Candle Terakhir: ${last_candle['close']}")

print("\n--- HASIL ANALISA ---")

# 4. LOGIKA LIQUIDITY GRAB (SWEEP)
# Syarat 1: Low candle terakhir tembus ke bawah Support (Nusuk bawah)
syarat_tembus = last_candle['low'] < support_area

# Syarat 2: Tapi Close candle terakhir BALIK ke atas Support (Gagal breakdown)
syarat_reject = last_candle['close'] > support_area

if syarat_tembus and syarat_reject:
    print("⚠️  LIQUIDITY GRAB TERDETEKSI! (Swing Failure Pattern)")
    print("Logika: Harga menusuk support untuk ambil Stop Loss, lalu naik lagi.")
    print("Sinyal: POTENSI REVERSAL NAIK (LONG) 🚀")
elif last_candle['close'] < support_area:
    print("Bukan Grab, ini murni BREAKDOWN (Jebol Support). Hati-hati Long.")
else:
    print("Belum ada Liquidity Grab. Harga masih bermain aman di atas support.")
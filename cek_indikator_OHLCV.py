import ccxt
import pandas as pd
import pandas_ta as ta

# 1. Setup Exchange (Pastikan VPN/DNS aktif jika di laptop)
exchange = ccxt.binance()

print("Sedang mengambil data Candle...")

# 2. Ambil data Candlestick (OHLCV)
# Symbol: BTC/USDT, Timeframe: 1 jam (1h), Jumlah: 100 candle terakhir
bars = exchange.fetch_ohlcv('BTC/USDT', timeframe='1h', limit=100)

# 3. Ubah data mentah menjadi Tabel (DataFrame) biar rapi
df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])

# Ubah format waktu dari angka aneh (timestamp) menjadi waktu yang bisa dibaca
df['time'] = pd.to_datetime(df['time'], unit='ms')

# 4. HITUNG INDIKATOR (Bagian Paling Penting!)
# Kita pakai library pandas_ta untuk hitung RSI periode 14
df['RSI'] = df.ta.rsi(length=14)

# Tambahan: Hitung EMA 50 (Exponential Moving Average)
df['EMA_50'] = df.ta.ema(length=50)

# Tambahan: Hitung MACD (Moving Average Convergence Divergence)
# Ini akan otomatis menambahkan kolom MACD, histogram, dan signal line
df.ta.macd(append=True)

# 5. Tampilkan 5 data terakhir
print("\n--- DATA 5 CANDLE TERAKHIR ---")
# Kita print kolom waktu, close, RSI, EMA, dan MACD
# Kolom MACD default: MACD_12_26_9 (MACD Line), MACDs_12_26_9 (Signal Line)
print(df[['time', 'close', 'RSI', 'EMA_50', 'MACD_12_26_9', 'MACDs_12_26_9']].tail(5))

# 6. Cek Logika Sederhana
print("\n--- Cek Sinyal RSI ---")
rsi_terakhir = df['RSI'].iloc[-1]
print(f"RSI Saat ini: {rsi_terakhir:.2f}")

if rsi_terakhir > 70:
    print("Sinyal: OVERBOUGHT (Mahal, Hati-hati / Siap Sell)")
elif rsi_terakhir < 30:
    print("Sinyal: OVERSOLD (Murah, Potensi Buy)")
else:
    print("Sinyal: NETRAL (Wait and See)")

# 7. Cek Logika MACD Crossover
print("\n--- Cek Sinyal MACD ---")
macd_line = df['MACD_12_26_9']
signal_line = df['MACDs_12_26_9']

print(f"MACD Line Saat Ini: {macd_line.iloc[-1]:.2f} | Signal Line Saat Ini: {signal_line.iloc[-1]:.2f}")

# Cek Golden Cross (MACD line memotong ke atas signal line)
if macd_line.iloc[-2] < signal_line.iloc[-2] and macd_line.iloc[-1] > signal_line.iloc[-1]:
    print("Sinyal: BULLISH CROSSOVER (Golden Cross, Potensi Buy)")
# Cek Death Cross (MACD line memotong ke bawah signal line)
elif macd_line.iloc[-2] > signal_line.iloc[-2] and macd_line.iloc[-1] < signal_line.iloc[-1]:
    print("Sinyal: BEARISH CROSSOVER (Death Cross, Potensi Sell)")
else:
    print("Sinyal: NETRAL (Tidak ada Crossover)")
print("\n--- CEK INDIKATOR SELESAI ---")
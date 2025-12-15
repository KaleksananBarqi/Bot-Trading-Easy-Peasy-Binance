import ccxt
from datetime import datetime

# 1. Inisialisasi Exchange (Pakai Binance public data dulu, tanpa API Key)
exchange = ccxt.binance()

print("Sedang mengambil data dari Binance...")

# 2. Ambil harga ticker BTC/USDT
ticker = exchange.fetch_ticker('BTC/USDT')

# 3. Tampilkan hasilnya
harga_terakhir = ticker['last']
waktu = datetime.now().strftime("%H:%M:%S")

print(f"--- Cek Harga Sukses ---")
print(f"Waktu: {waktu}")
print(f"Harga Bitcoin (BTC/USDT): ${harga_terakhir}")

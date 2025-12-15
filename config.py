import os
from dotenv import load_dotenv

load_dotenv()

# --- 1. DATA RAHASIA ---
API_KEY = os.getenv('BINANCE_API_KEY')
SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

if not API_KEY or not SECRET_KEY:
    print("❌ ERROR: API KEY tidak ditemukan di file .env!")
    exit()

# --- 2. PENGATURAN STRATEGI (MAGIC NUMBERS DISINI) ---
# Ubah angka di sini, otomatis logika bot berubah semua.

# Indikator EMA
EMA_FAST = 13          # EMA Cepat
EMA_SLOW = 21          # EMA Lambat
EMA_TREND_H1 = 200     # EMA Trend Besar

# Batasan RSI
RSI_BUY_LIMIT = 60     # Buy jika RSI di bawah ini
RSI_SELL_LIMIT = 40    # Sell jika RSI di atas ini
RSI_PERIOD = 14

# Validasi Volume
VOL_MULTIPLIER = 1.2   # Volume harus 1.2x rata-rata
VOL_PERIOD = 20        # Periode rata-rata volume

# ATR & Risk Management
ATR_PERIOD = 14
SL_MULTIPLIER = 2.0    # Stop Loss = 2x ATR
TP_MULTIPLIER = 3.0    # Take Profit = 3x ATR

# Setting Lain
LIQUIDITY_PERIOD = 20  # Cek Low/High 20 candle terakhir
COOLDOWN_MINUTES = 15  # Istirahat setelah entry

# --- 3. DAFTAR KOIN ---
DAFTAR_KOIN = [
    {
        "symbol": "BTC/USDT",
        "modal": 100000,
        "leverage": 15
    },
    {
        "symbol": "ETH/USDT",
        "modal": 5000,
        "leverage": 10
    },
    {
        "symbol": "BNB/USDT",
        "modal": 2000,
        "leverage": 20
    },
    {
        "symbol": "SOL/USDT",
        "modal": 3000,
        "leverage": 10
    },
     {
        "symbol": "HYPE/USDT",
        "modal": 3000,
        "leverage": 10
    },
]
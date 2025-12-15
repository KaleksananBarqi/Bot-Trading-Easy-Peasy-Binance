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

# --- 2. PENGATURAN STRATEGI (MODE AGRESIF/MOMENTUM) ---

# Indikator EMA
EMA_FAST = 13          # Tetap (Momentum 15m)
EMA_SLOW = 21          # Tetap (Momentum 15m)
EMA_TREND_H1 = 50      # UBAH: Dari 200 jadi 50 (Biar lebih responsif ikut tren baru)

# Batasan RSI (DILONGGARKAN)
RSI_BUY_LIMIT = 90     # UBAH: Boleh Buy selama RSI belum tembus 70 (Overbought)
RSI_SELL_LIMIT = 20    # UBAH: Boleh Sell selama RSI belum tembus 30 (Oversold)
RSI_PERIOD = 14

# Validasi Volume (DILONGGARKAN)
VOL_MULTIPLIER = 1.0   # UBAH: Cukup 1.0x (Sama dengan rata-rata aja sudah valid)
VOL_PERIOD = 20        

# ATR & Risk Management (TETAP AMAN)
ATR_PERIOD = 14
SL_MULTIPLIER = 2.0    # SL tetap 2x ATR (Jangan diubah biar akun aman)
TP_MULTIPLIER = 3.0    # TP tetap 3x ATR

# Setting Lain
LIQUIDITY_PERIOD = 10  # UBAH: Cek Low/High 10 candle terakhir (Sweep pendek diambil)
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
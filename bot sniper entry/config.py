import os
from dotenv import load_dotenv

# Load file .env
load_dotenv()

# --- 1. DATA RAHASIA ---
API_KEY = os.getenv('BINANCE_API_KEY')
SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Validasi Key
if not API_KEY or not SECRET_KEY:
    print("❌ ERROR: API KEY tidak ditemukan di file .env!")

# --- PENGATURAN BOT ---
DEMO_MODE = True  # Ubah False jika uang asli

# --- 2. PENGATURAN STRATEGI (MODE SNIPER 1 MENIT) ---

# Indikator EMA (Settingan Scalper Cepat)
EMA_FAST = 5           # Garis Cepat (Momentum)
EMA_SLOW = 13          # Garis Lambat (Trend Kecil)
EMA_TREND_H1 = 20      # Trend Besar (Timeframe 15m) pakai EMA 20 biar responsif

# Batasan RSI (SNIPER TRIGGER)
# Kita pakai angka 75 agar sinkron dengan logika di 'bot_sniper_fixed.py'
RSI_BUY_LIMIT = 75     # Di atas 75 dianggap Overbought (Siap Short)
RSI_SELL_LIMIT = 25    # Di bawah 25 dianggap Oversold (Siap Long)
RSI_PERIOD = 14

# Validasi Volume
VOL_MULTIPLIER = 0.5   # Volume 50% dari rata-rata sudah cukup (Agresif)
VOL_PERIOD = 20        

# ATR & Risk Management (Scalping Ketat)
ATR_PERIOD = 14
SL_MULTIPLIER = 1.5    # SL Rapat (1.5x ATR)
TP_MULTIPLIER = 1.5    # TP Pendek (1.5x ATR) - Cepat keluar market

# Setting Lain
LIQUIDITY_PERIOD = 3   # Cek 3 candle terakhir
COOLDOWN_MINUTES = 1   # Istirahat 1 menit setelah close posisi

# --- 3. DAFTAR KOIN ---
# Note: Koin yg tidak ada di Binance Futures otomatis akan error/diskip bot.
DAFTAR_KOIN = [
    # --- KOIN DARI GAMBAR (High Risk / Mungkin belum listing Futures) ---
    {"symbol": "MERL/USDT", "modal": 100, "leverage": 10},
    {"symbol": "COAI/USDT", "modal": 100, "leverage": 10},
    {"symbol": "M/USDT",    "modal": 100, "leverage": 10}, # Bisa jadi MAV/MANTA, tapi kita coba M
    {"symbol": "HUMA/USDT", "modal": 100, "leverage": 10},
    {"symbol": "BAS/USDT",  "modal": 100, "leverage": 10},
    {"symbol": "GUN/USDT",  "modal": 100, "leverage": 10},
    {"symbol": "TAG/USDT",  "modal": 100, "leverage": 10},
    {"symbol": "PIPPIN/USDT", "modal": 100, "leverage": 10},
]
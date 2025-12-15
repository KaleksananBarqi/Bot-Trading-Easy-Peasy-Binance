import os
from dotenv import load_dotenv

# Load file .env (Pastikan file .env sudah diisi API KEY)
load_dotenv()

# --- 1. DATA RAHASIA ---
API_KEY = os.getenv('BINANCE_API_KEY')
SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Validasi jika kunci belum diisi
if not API_KEY or not SECRET_KEY:
    print("❌ ERROR: API KEY tidak ditemukan di file .env!")
    # exit() # Bisa di-uncomment jika ingin bot mati kalau tidak ada key

# --- PENGATURAN BOT ---
DEMO_MODE = True  # True = Uang Mainan (Aman buat tes), False = Uang Asli

# --- 2. PENGATURAN STRATEGI (KONSERVATIF 15M) ---

# Indikator EMA (Standar)
EMA_FAST = 9           
EMA_SLOW = 21          
EMA_TREND_H1 = 50      # Trend H1 pakai EMA 50

# RSI (Normal)
RSI_BUY_LIMIT = 70     
RSI_SELL_LIMIT = 30    
RSI_PERIOD = 14

# Volume
VOL_MULTIPLIER = 1.0   # Volume harus rata-rata (Valid)
VOL_PERIOD = 20        

# Risk Management
ATR_PERIOD = 14
SL_MULTIPLIER = 2.0    # SL Standar
TP_MULTIPLIER = 2.5    # TP Standar
# --- 3. DAFTAR KOIN ---
DAFTAR_KOIN = [
    {"symbol": "BTC/USDT", "modal": 200, "leverage": 10},
    {"symbol": "ETH/USDT", "modal": 60,  "leverage": 10},
    {"symbol": "ZEC/USDT", "modal": 60,  "leverage": 10},
    {"symbol": "SOL/USDT", "modal": 200,  "leverage": 10},
    {"symbol": "BNB/USDT", "modal": 60,  "leverage": 10},
    {"symbol": "XRP/USDT", "modal": 60,  "leverage": 10},
    {"symbol": "TRX/USDT", "modal": 60,  "leverage": 10},
    {"symbol": "SUI/USDT", "modal": 60,  "leverage": 10},
    {"symbol": "DOGE/USDT", "modal": 60, "leverage": 10},
]
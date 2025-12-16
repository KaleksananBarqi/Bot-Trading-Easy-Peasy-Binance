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
TP_MULTIPLIER = 3.0    # TP Standar

# Filter Sideways
ADX_PERIOD = 14
ADX_LIMIT = 20  # Trend dianggap kuat jika ADX > 20

# Safety
MAX_OPEN_POSITIONS = 3 # Maksimal cuma boleh pegang 3 koin sekaligus

# =========================================================
# 3. DAFTAR PAIR KOIN YANG DIPANTAU
# =========================================================

DAFTAR_KOIN = [
    # --- 1. THE KINGS (Major & Aman) ---
    {"symbol": "BTC/USDT", "modal": 2000, "leverage": 30}, # King coin, modal lebih besar
    {"symbol": "ETH/USDT", "modal": 500,  "leverage": 30},
    {"symbol": "BNB/USDT", "modal": 500,  "leverage": 30},
    {"symbol": "SOL/USDT", "modal": 500,  "leverage": 30},
    {"symbol": "XRP/USDT", "modal": 500,  "leverage": 30},
    {"symbol": "ADA/USDT", "modal": 500,  "leverage": 30},
    {"symbol": "AVAX/USDT", "modal": 500, "leverage": 30},

    # --- 2. CLASSIC & ESTABLISHED ALTS ---
    {"symbol": "LTC/USDT", "modal": 500, "leverage": 30},
    {"symbol": "BCH/USDT", "modal": 500, "leverage": 30},
    {"symbol": "TRX/USDT", "modal": 500, "leverage": 30},
    {"symbol": "LINK/USDT", "modal": 500, "leverage": 30},
    {"symbol": "DOT/USDT", "modal": 500, "leverage": 30},
    {"symbol": "UNI/USDT", "modal": 500, "leverage": 30},
    {"symbol": "FIL/USDT", "modal": 500, "leverage": 30},
    {"symbol": "AAVE/USDT", "modal": 500, "leverage": 30},
    {"symbol": "NEAR/USDT", "modal": 500, "leverage": 30},
    {"symbol": "ZEC/USDT", "modal": 500, "leverage": 30},
    {"symbol": "XLM/USDT", "modal": 500, "leverage": 30},
    {"symbol": "ETC/USDT", "modal": 500, "leverage": 30},
    {"symbol": "XMR/USDT", "modal": 500, "leverage": 30},
    {"symbol": "DASH/USDT", "modal": 500, "leverage": 30},
    {"symbol": "XTZ/USDT", "modal": 500, "leverage": 30},
    {"symbol": "ATOM/USDT", "modal": 500, "leverage": 30},
    {"symbol": "ONT/USDT", "modal": 500, "leverage": 30},
    {"symbol": "CRV/USDT", "modal": 500, "leverage": 30},

    # --- 3. TRENDING / AI / L2 (Modern) ---
    {"symbol": "SUI/USDT", "modal": 500, "leverage": 30},
    {"symbol": "APT/USDT", "modal": 500, "leverage": 30},
    {"symbol": "ARB/USDT", "modal": 500, "leverage": 30},
    {"symbol": "TAO/USDT", "modal": 500, "leverage": 30},
    {"symbol": "WLD/USDT", "modal": 500, "leverage": 30},
    {"symbol": "ENA/USDT", "modal": 500, "leverage": 30},
    {"symbol": "PNUT/USDT", "modal": 500, "leverage": 30},

    # --- 4. MEMES (High Volatility) ---
    {"symbol": "DOGE/USDT",     "modal": 500, "leverage": 30},
    {"symbol": "1000PEPE/USDT", "modal": 500, "leverage": 30}, # Pastikan pakai 1000PEPE di Binance
    {"symbol": "WIF/USDT",      "modal": 500, "leverage": 30},

    # --- 5. HATI-HATI / BELUM LISTING FUTURES MAJOR (Cek Manual) ---
    # Hilangkan tanda pagar (#) HANYA jika sudah yakin ada di exchange futures Anda
     {"symbol": "BEAT/USDT",     "modal": 500, "leverage": 20},
     {"symbol": "PIPPIN/USDT",   "modal": 500, "leverage": 20},
     {"symbol": "ASTER/USDT",    "modal": 500, "leverage": 20},
     {"symbol": "FARTCOIN/USDT", "modal": 500, "leverage": 20},
     {"symbol": "PUMP/USDT",     "modal": 500, "leverage": 20},
     {"symbol": "ARC/USDT",      "modal": 500, "leverage": 20},
     {"symbol": "HYPE/USDT",     "modal": 500, "leverage": 20},
]
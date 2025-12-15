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

# --- 2. PENGATURAN STRATEGI (HIGH ACCURACY 1M) ---

# Indikator EMA
EMA_FAST = 5           
EMA_SLOW = 13          
EMA_TREND_H1 = 50      # Kita perhalus trend besar jadi 50 biar gak sering berubah-ubah

# Filter Kekuatan Tren (ADX) - INI KUNCINYA
ADX_MINIMUM = 20       # Hanya trade jika kekuatan tren > 20 (Anti-Sideways)
ADX_PERIOD = 14

# Indikator Momentum (StochRSI)
STOCHRSI_PERIOD = 14
STOCHRSI_K = 3
STOCHRSI_D = 3
STOCH_BUY_LIMIT = 20   # Beli jika StochRSI di bawah 20 (Murah)
STOCH_SELL_LIMIT = 80  # Jual jika StochRSI di atas 80 (Mahal)

# Validasi Volume (Diperketat)
VOL_MULTIPLIER = 1.0   # Wajib di atas rata-rata (Volume Kuat)
VOL_PERIOD = 20        

# ATR & Risk Management (Ratio 1:1.5)
ATR_PERIOD = 14
SL_MULTIPLIER = 1.5    # Jarak SL
TP_MULTIPLIER = 2.5    # Jarak TP (Kita incar profit lebih lebar karena sinyal lebih valid)

# Setting Lain
LIQUIDITY_PERIOD = 5   
COOLDOWN_MINUTES = 5   # Istirahat 5 menit biar gak kemaruk

# --- 3. DAFTAR KOIN ---
# PERHATIAN: Beberapa simbol dari request Anda tidak valid di Binance Futures (misal: GUN, KITE, GIGGLE).
# Simbol-simbol di bawah ini adalah hasil pembersihan dan asumsi dari request Anda.
DAFTAR_KOIN = [
    {"symbol": "BTC/USDT", "modal": 200, "leverage": 10},
    {"symbol": "ETH/USDT", "modal": 60,  "leverage": 10},
    {"symbol": "ZEC/USDT", "modal": 60,  "leverage": 10},
    {"symbol": "SOL/USDT", "modal": 200,  "leverage": 10},
    {"symbol": "BNB/USDT", "modal": 60,  "leverage": 10},
    {"symbol": "XRP/USDT", "modal": 60,  "leverage": 10},
    {"symbol": "SUI/USDT", "modal": 60,  "leverage": 10},
    {"symbol": "DOGE/USDT", "modal": 60, "leverage": 10},
]
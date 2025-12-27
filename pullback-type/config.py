import os
from dotenv import load_dotenv

load_dotenv()
# strategi pullback sniper

# --- 1. AKUN & API ---
PAKAI_DEMO = True 
API_KEY_DEMO = os.getenv("BINANCE_TESTNET_KEY")
SECRET_KEY_DEMO = os.getenv("BINANCE_TESTNET_SECRET")
API_KEY_LIVE = os.getenv("BINANCE_API_KEY")
SECRET_KEY_LIVE = os.getenv("BINANCE_SECRET_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
 
# --- 2. GLOBAL RISK ---
DEFAULT_LEVERAGE = 10
DEFAULT_MARGIN_TYPE = 'isolated' 
DEFAULT_AMOUNT_USDT = 10  

# [SARAN UBAH] Dari 20 ke 50 atau 100
# 50  = Medium Trend (Cocok untuk Swing/Day Trade normal)
# 100 = Major Trend (Lebih santai, filter "badai" saja)
# 200 = Long Term (Sangat toleran, jarang berubah arah)

# --- 3. FILTER BTC (GLOBAL TREND) ---
BTC_SYMBOL = 'BTC/USDT'
BTC_TIMEFRAME = '1h'
BTC_EMA_PERIOD = 50             
BTC_CHECK_INTERVAL = 300        

# --- 4. STRATEGI INDIKATOR (REVISED FOR CHOPPY MARKET) ---
# Kita gunakan EMA hanya untuk menentukan bias jangka pendek
EMA_TREND_MAJOR = 50    
EMA_FAST = 21   # Dipercepat dari 13 agar lebih responsif scalping        
EMA_SLOW = 50          

# ADX FILTER (CRUCIAL!)
ADX_PERIOD = 14
# Jika ADX < 25, kita anggap sideways -> Aktifkan strategi BB Reversal
# Jika ADX > 25, kita anggap trending -> Aktifkan strategi EMA Cross
ADX_LIMIT_TREND  = 30 
ADX_LIMIT_CHOPPY = 20 

# VOLUME FILTER
VOL_MA_PERIOD = 20

# BOLLINGER BANDS (RAJA DI MARKET SIDEWAYS)
# Kita pakai standar deviasi 2.0. Jika market sangat tenang, turunkan ke 1.8 tapi risiko naik.
BB_LENGTH = 20
BB_STD = 2.0 

# STOCHASTIC RSI (SENSITIVE TRIGGER)
# Settingan cepat untuk scalping 15m
STOCHRSI_LEN = 14
STOCHRSI_K = 3
STOCHRSI_D = 3
STOCH_OVERSOLD = 20
STOCH_OVERBOUGHT = 80

# --- 5. TEKNIKAL & EKSEKUSI ---
TIMEFRAME_TREND = '1h'      
TIMEFRAME_EXEC = '5m'      
LIMIT_TREND = 500           
LIMIT_EXEC = 100            

ATR_PERIOD = 14             
ATR_MULTIPLIER_SL = 1.0
ATR_MULTIPLIER_TP1 = 2.2

MIN_ORDER_USDT = 5           
ORDER_TYPE = 'market'     
COOLDOWN_PER_SYMBOL_SECONDS = 300 # Kurangi cooldown jadi 5 menit agar bisa re-entry cepat
CONCURRENCY_LIMIT = 20

# Order / Retry
ORDER_SLTP_RETRIES = 5
ORDER_SLTP_RETRY_DELAY = 2
POSITION_POLL_RETRIES = 6
POSITION_POLL_DELAY = 0.5


# --- 5. TEKNIKAL & EKSEKUSI ---

# MODE LIQUIDITY HUNT (Anti-Retail)
USE_LIQUIDITY_HUNT = True  # Set True untuk aktifkan strategi "Jaring Bawah/Atas"
TRAP_SAFETY_SL = 0.5       # Jarak SL baru dari Entry baru (Satuan ATR)

# --- SETTING STRATEGI: TREND TRAP (SNIPER PULLBACK) ---
# Mode ini mencari harga diskon saat tren kuat, bukan breakout.
USE_TREND_TRAP_STRATEGY = True  # Set False jika ingin kembali ke strategi breakout lama

# Filter Kekuatan Tren
TREND_TRAP_ADX_MIN = 25         # Minimal ADX untuk validasi tren (biar gak kejebak sideways)

# Filter RSI (Momentum) - Agar tidak beli dipucuk / jual di dasar
# Kita hanya entry jika RSI berada di zona "sehat" (tidak overbought/oversold parah)
TREND_TRAP_RSI_LONG_MIN = 40    # Batas bawah RSI untuk Buy (jangan beli kalau momentum mati < 40)
TREND_TRAP_RSI_LONG_MAX = 60    # Batas atas RSI untuk Buy (jangan beli kalau sudah kepanasan > 60)

TREND_TRAP_RSI_SHORT_MIN = 40   # Batas bawah RSI untuk Sell (jangan jual kalau sudah oversold < 40)
TREND_TRAP_RSI_SHORT_MAX = 60   # Batas atas RSI untuk Sell (jangan jual kalau momentum naik > 60)

# Opsi Scalping Sideways (BB Bounce)
USE_SIDEWAYS_SCALP = True       # Aktifkan strategi pantulan BB saat market diam (ADX rendah)
SIDEWAYS_ADX_MAX = 20           # Batas ADX dianggap sideways

# --- 6. DAFTAR KOIN ---
DAFTAR_KOIN = [
    # --- Major Coins (Cross Margin) ---
    {"symbol": "BTC/USDT", "leverage": 20, "margin_type": "cross", "amount": 50},
    {"symbol": "ETH/USDT", "leverage": 20, "margin_type": "cross", "amount": 40},

    # --- Strong Alts (Isolated, Mid Leverage) ---
    {"symbol": "SOL/USDT", "leverage": 15, "margin_type": "isolated", "amount": 30},
    {"symbol": "BNB/USDT", "leverage": 15, "margin_type": "isolated", "amount": 30},
    {"symbol": "XRP/USDT", "leverage": 10, "margin_type": "isolated", "amount": 15},
    {"symbol": "ADA/USDT", "leverage": 10, "margin_type": "isolated", "amount": 15},
    {"symbol": "DOGE/USDT", "leverage": 10, "margin_type": "isolated", "amount": 15},
    {"symbol": "TRX/USDT", "leverage": 10, "margin_type": "isolated", "amount": 15},
    {"symbol": "LTC/USDT", "leverage": 10, "margin_type": "isolated", "amount": 15},
    {"symbol": "AVAX/USDT", "leverage": 10, "margin_type": "isolated", "amount": 15},

    # --- Volatile/Newer Alts (Isolated, Low Leverage) ---
    {"symbol": "SUI/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "APT/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "HYPE/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "ENA/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "SEI/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},

    # --- Top Pump Futures (Added) ---
    {"symbol": "ZBT/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "RVV/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "0G/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "IR/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "CLO/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "BANANA/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "XPIN/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "MON/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "HIPPO/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "LAYER/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "NEWT/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "AKE/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "SKYAI/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "NOM/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "METIS/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "OM/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "PUMPBTC/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "RECALL/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "VELVET/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "STBL/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    
    # --- High Volume Futures (New Additions) ---
    {"symbol": "AT/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "ZEC/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "BEAT/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "ZKP/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "LIGHT/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "PIPPIN/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "BCH/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "AVNT/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "KAITO/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
    {"symbol": "1000PEPE/USDT", "leverage": 5, "margin_type": "isolated", "amount": 10},
]
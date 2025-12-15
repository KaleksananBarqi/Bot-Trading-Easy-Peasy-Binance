"""
===========================================================
BOT TRADING V3 - SMART KONSERVATIF (ADX FILTERED)
Created for: Mas Aji
===========================================================
Logic Baru:
1. Tren Besar: H1 (EMA 50)
2. Filter Sideways: ADX > 20 (Wajib Strong Trend)
3. Eksekusi: 15m (EMA 9/21 Cross)
4. Risk Management: 
   - Max Open Positions (Global Check)
   - Dynamic ATR SL/TP
===========================================================
"""
import ccxt
import pandas as pd
import pandas_ta as ta
import time
import requests 
import sys
from datetime import datetime
import config 

# --- KONFIGURASI DEFAULT (Jaga-jaga jika config.py belum diupdate) ---
MAX_POSITIONS = getattr(config, 'MAX_OPEN_POSITIONS', 3) # Maksimal posisi terbuka
ADX_THRESHOLD = getattr(config, 'ADX_LIMIT', 20)         # Minimal kekuatan tren
ADX_LEN = getattr(config, 'ADX_PERIOD', 14)

print(f"--- 🛡️ BOT V3 SMART-DEFENSIVE STARTED ---")
print(f"Setingan: Max Posisi={MAX_POSITIONS} | Min ADX={ADX_THRESHOLD}")

# ==========================================
# 1. SETUP KONEKSI
# ==========================================
try:
    exchange = ccxt.binance({
        'apiKey': config.API_KEY,
        'secret': config.SECRET_KEY,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future',
            'adjustForTimeDifference': True, 
        }
    })
    
    # Cek Mode
    if getattr(config, 'DEMO_MODE', True): 
        exchange.enable_demo_trading(True) # Hanya aktif di library ccxt versi baru/tertentu
        print("⚠️  MODE: DEMO / TESTNET (Pastikan API Key Testnet)")
    else:
        print("🚨  MODE: LIVE TRADING (UANG ASLI)")
        
    exchange.load_markets() # Load market data dulu
    print("✅  Koneksi Binance: BERHASIL")
    
except Exception as e:
    print(f"❌  Gagal koneksi: {e}")
    sys.exit(1)

# ==========================================
# 2. FUNGSI PENDUKUNG
# ==========================================

def lapor_telegram(pesan):
    try:
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
        data = {'chat_id': config.TELEGRAM_CHAT_ID, 'text': pesan}
        requests.post(url, data=data)
    except Exception as e:
        print(f"⚠️ Gagal lapor Telegram: {e}")

lapor_telegram(f"🛡️ BOT V3 RESTART\nFitur: ADX Filter + Max Position Protection")

def ambil_data(symbol, timeframe, limit=200):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        return df
    except Exception as e:
        print(f"⚠️  Gagal data {symbol}: {e}")
        return pd.DataFrame()

def cek_jumlah_posisi_aktif():
    """Menghitung berapa koin yang sedang kita pegang saat ini"""
    try:
        # Ambil semua posisi risk
        balance = exchange.fetch_positions()
        # Filter hanya yang sizenya > 0
        active_pos = [x for x in balance if float(x['contracts']) > 0]
        return len(active_pos)
    except Exception as e:
        print(f"⚠️  Gagal cek posisi global: {e}")
        return 99 # Return angka besar biar gak entry kalau error

# ==========================================
# 3. FUNGSI EKSEKUSI (ORDER)
# ==========================================
def eksekusi_full_auto(symbol, modal, leverage, signal, price, sl, tp):
    print(f"\n>>> 🚀 ACTION: {symbol} - {signal} DETECTED! ...")
    
    pesan_notif = f"🔥 {symbol} ENTRY {signal}\n"
    pesan_notif += f"Price: ${price}\n"
    
    try:
        # 1. Persiapan Simbol
        exchange.cancel_all_orders(symbol) # Cancel pending order lama
        try: exchange.set_margin_mode('isolated', symbol)
        except: pass
        try: exchange.set_leverage(leverage, symbol)
        except: pass

        # 2. Hitung Size
        amount_coin = modal / price
        amount_final = exchange.amount_to_precision(symbol, amount_coin)
        sl_final = exchange.price_to_precision(symbol, sl)
        tp_final = exchange.price_to_precision(symbol, tp)
        
        # Tentukan Side
        side = 'buy' if "LONG" in signal else 'sell'
        side_close = 'sell' if side == 'buy' else 'buy'

        # 3. Entry Market
        order = exchange.create_order(symbol, 'market', side, amount_final)
        avg_fill_price = order.get('average', price) # Coba ambil harga fill asli
        pesan_notif += f"✅ Filled: {amount_final} @ ${avg_fill_price}\n"
        time.sleep(1)

        # 4. Pasang SL (Wajib!) - Trigger by Mark Price
        params_sl = {'stopPrice': sl_final, 'reduceOnly': True, 'workingType': 'MARK_PRICE'}
        exchange.create_order(symbol, 'STOP_MARKET', side_close, amount_final, params=params_sl)
        pesan_notif += f"🛡️ SL: ${sl_final}\n"

        # 5. Pasang TP - Trigger by Last Price
        params_tp = {'stopPrice': tp_final, 'reduceOnly': True, 'workingType': 'CONTRACT_PRICE'}
        exchange.create_order(symbol, 'TAKE_PROFIT_MARKET', side_close, amount_final, params=params_tp)
        pesan_notif += f"💰 TP: ${tp_final}\n"
        
        lapor_telegram(pesan_notif)

    except Exception as e:
        error_msg = f"❌ GAGAL EKSEKUSI {symbol}: {e}"
        print(error_msg)
        lapor_telegram(error_msg)

# ==========================================
# 4. OTAK ANALISA (H1 Trend + 15m Entry + ADX)
# ==========================================
def analisa_satu_koin(data_koin):
    SYMBOL = data_koin['symbol']
    MODAL = data_koin['modal']     
    LEVERAGE = data_koin['leverage'] 

    try:
        # A. Cek Posisi Existing di Koin Ini
        # Kita fetch khusus simbol ini biar cepat
        pos = exchange.fetch_positions([SYMBOL])
        if pos and float(pos[0]['contracts']) > 0:
            return # Skip diam-diam kalau sudah punya barang

        # B. Ambil Data Candle
        df_big = ambil_data(SYMBOL, '1h', limit=100)  # Trend H1
        df = ambil_data(SYMBOL, '15m', limit=60)      # Eksekusi 15m
        
        if df_big.empty or df.empty: return

        # C. Hitung Indikator
        # 1. H1 Trend (EMA 50)
        df_big['EMA_Trend'] = df_big.ta.ema(length=config.EMA_TREND_H1)
        trend_h1_bull = df_big.iloc[-1]['close'] > df_big.iloc[-1]['EMA_Trend']

        # 2. 15m Setup
        df['EMA_Fast'] = df.ta.ema(length=config.EMA_FAST) 
        df['EMA_Slow'] = df.ta.ema(length=config.EMA_SLOW)
        df['ATR'] = df.ta.atr(length=config.ATR_PERIOD)
        df['RSI'] = df.ta.rsi(length=config.RSI_PERIOD)
        
        # --- NEW: ADX Filter (Anti-Sideways) ---
        adx_df = df.ta.adx(length=ADX_LEN)
        # Pandas TA output kolomnya: ADX_14, DMP_14, DMN_14. Kita perlu nama kolom dinamis:
        col_adx_name = f"ADX_{ADX_LEN}"
        df['ADX'] = adx_df[col_adx_name]
        
        # Data Candle Terakhir & Sebelumnya
        last = df.iloc[-1]
        prev = df.iloc[-2]

        # Logika Cross (Sinyal Awal)
        cross_up = (prev['EMA_Fast'] < prev['EMA_Slow']) and (last['EMA_Fast'] > last['EMA_Slow'])
        cross_down = (prev['EMA_Fast'] > prev['EMA_Slow']) and (last['EMA_Fast'] < last['EMA_Slow'])
        
        # Logika Validasi (Filter)
        # 1. ADX harus kuat (di atas threshold, misal 20)
        is_trend_strong = last['ADX'] > ADX_THRESHOLD
        
        # 2. RSI Filter (Jangan beli di pucuk)
        rsi_safe_long = last['RSI'] < config.RSI_BUY_LIMIT
        rsi_safe_short = last['RSI'] > config.RSI_SELL_LIMIT

        signal = "WAIT"
        alasan = ""

        # --- LOGIKA KEPUTUSAN FINAL ---
        
        # SKENARIO LONG
        if trend_h1_bull: # Syarat 1: Tren H1 Naik
            if cross_up:  # Syarat 2: EMA Cross Up
                if is_trend_strong: # Syarat 3: Tidak Sideways
                    if rsi_safe_long: # Syarat 4: RSI Aman
                        signal = "BUY / LONG"
                    else: alasan = "RSI Overbought"
                else: alasan = f"Weak ADX ({last['ADX']:.1f})"
            else: alasan = "No Cross"
        
        # SKENARIO SHORT
        elif not trend_h1_bull: # Syarat 1: Tren H1 Turun
            if cross_down: # Syarat 2: EMA Cross Down
                if is_trend_strong: # Syarat 3: Tidak Sideways
                    if rsi_safe_short: # Syarat 4: RSI Aman
                        signal = "SELL / SHORT"
                    else: alasan = "RSI Oversold"
                else: alasan = f"Weak ADX ({last['ADX']:.1f})"
            else: alasan = "No Cross"

        # PRINT LOG STATUS (Biar enak dipantau)
        # Format: Symbol | Trend H1 | ADX | Signal
        trend_str = "🟢BULL" if trend_h1_bull else "🔴BEAR"
        adx_str = f"{last['ADX']:.1f}"
        print(f"   > {SYMBOL:<9} | H1:{trend_str} | ADX:{adx_str} | {signal} ({alasan})")

        # --- EKSEKUSI ---
        if "LONG" in signal or "SHORT" in signal:
            # SAFETY CHECK 1: Max Open Positions
            total_posisi = cek_jumlah_posisi_aktif()
            if total_posisi >= MAX_POSITIONS:
                print(f"     ⚠️ SKIP Entry: Max Posisi Tercapai ({total_posisi}/{MAX_POSITIONS})")
                return

            # SAFETY CHECK 2: Saldo
            try:
                bal = exchange.fetch_balance()
                usdt = float(bal['USDT']['free'])
                margin = MODAL / LEVERAGE
                if usdt < margin:
                    print("     ⚠️ SKIP Entry: Saldo USDT habis.")
                    return
            except: pass

            # Hitung TP/SL Dinamis via ATR
            atr = prev['ATR']
            sl_dist = config.SL_MULTIPLIER * atr
            tp_dist = (config.TP_MULTIPLIER * atr) * 0.95

            sl_price, tp_price = 0, 0
            if "LONG" in signal:
                sl_price = last['close'] - sl_dist
                tp_price = last['close'] + tp_dist
            else:
                sl_price = last['close'] + sl_dist
                tp_price = last['close'] - tp_dist
            
            # FIRE!
            eksekusi_full_auto(SYMBOL, MODAL, LEVERAGE, signal, last['close'], sl_price, tp_price)

    except Exception as e:
        print(f"⚠️ Error Analisa {SYMBOL}: {e}")

# ==========================================
# 5. MAIN LOOP (Jantung Bot)
# ==========================================
if __name__ == "__main__":
    print(f"\n[{datetime.now().strftime('%H:%M')}] Menunggu Candle 15m berikutnya...")
    
    while True:
        try:
            now = datetime.now()
            
            # --- LOGIKA SMART SLEEP ---
            # Tidur sampai menit: 00, 15, 30, 45
            # Ditambah 10 detik buffer (biar data candle matang)
            menit_sisa = 15 - (now.minute % 15)
            detik_tidur = (menit_sisa * 60) - now.second + 10 
            
            if detik_tidur <= 0: detik_tidur = 1 # Safety kalau detiknya minus
            
            # Countdown print setiap 1 menit (opsional, biar gak spam log, kita sleep langsung aja)
            # Tapi untuk Mas Aji biar tenang, kita print sekali aja.
            
            time.sleep(detik_tidur)
            
            # --- BANGUN & SCAN ---
            ts = datetime.now().strftime('%H:%M:%S')
            print(f"\n[{ts}] 🕯️ CANDLE BARU! Scanning Market...")
            
            # Cek koneksi internet/binance simple check
            try: exchange.fetch_time()
            except: 
                print("⚠️ Koneksi timeout, coba lagi nanti...")
                continue

            # Loop Koin
            for koin in config.DAFTAR_KOIN:
                analisa_satu_koin(koin)
                time.sleep(1) # Jeda antar koin biar gak kena limit API
            
            print(f"--- Scan Selesai. Tidur lagi... ---")

        except KeyboardInterrupt:
            print("\n🛑 Bot dihentikan manual.")
            sys.exit()
        except Exception as e:
            print(f"⚠️ CRITICAL ERROR di Main Loop: {e}")
            time.sleep(60) # Tidur 1 menit kalau error parah
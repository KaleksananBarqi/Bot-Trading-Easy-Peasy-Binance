"""
===========================================================
BOT TRADING V2 - KONSERVATIF (SWING SANTAI 15 MENIT)
===========================================================
1. Analisa Tren Besar: Timeframe 1 JAM (H1).
2. Analisa Eksekusi: Timeframe 15 MENIT (EMA Cross).
3. Filter: Volume, RSI.
4. Manajemen Risiko:
   - SL: Mark Price (2x ATR).
   - TP: Last Price (Safety Margin 95%).
   - Mode: Isolated Margin.
5. Loop: Smart Sleep (Cek setiap ganti candle 15m).
===========================================================
"""
import ccxt
import pandas as pd
import pandas_ta as ta
import time
import requests 
from datetime import datetime
import config  # Pastikan file config.py ada di folder yang sama

print(f"--- 🐢 BOT KONSERVATIF 15 MENIT STARTED ---")
print(f"Menjalankan {len(config.DAFTAR_KOIN)} Koin Sekaligus.")

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
    
    if getattr(config, 'DEMO_MODE', True): 
        exchange.enable_demo_trading(True)
        print("⚠️ MODE: DEMO TRADING")
    else:
        print("🚨 MODE: LIVE TRADING")
    
    print("✅ Koneksi Binance: BERHASIL")
    
except Exception as e:
    print(f"❌ Gagal koneksi ke Binance: {e}")
    exit(1)

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

lapor_telegram(f"🔔 BOT START!\nMode: Konservatif (Trend H1 -> Eksekusi 15m)")

def ambil_data(symbol, timeframe, limit=200):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        return df
    except Exception as e:
        print(f"⚠️ Gagal ambil data {symbol} ({timeframe}): {e}")
        return pd.DataFrame()

# ==========================================
# 3. FUNGSI EKSEKUSI
# ==========================================
def eksekusi_full_auto(symbol, modal, leverage, signal, price, sl, tp):
    print(f"\n>>> 🚀 ACTION: {symbol} - {signal} DETECTED! ...")
    
    pesan_notif = f"🔥 {symbol} EKSEKUSI {signal}!!!\n"
    pesan_notif += f"Harga Entry: ${price}\n"
    
    try:
        # Bersih-bersih order lama
        try: exchange.cancel_all_orders(symbol)
        except: pass

        # Setting Margin
        try: exchange.set_margin_mode('isolated', symbol)
        except: pass
        try: exchange.set_leverage(leverage, symbol)
        except: pass

        # Hitung Size & Harga
        amount_coin = modal / price
        amount_final = exchange.amount_to_precision(symbol, amount_coin)
        sl_final = exchange.price_to_precision(symbol, sl)
        tp_final = exchange.price_to_precision(symbol, tp)
        
        side = 'buy' if "LONG" in signal else 'sell'
        side_close = 'sell' if side == 'buy' else 'buy'

        # 1. Entry Market
        exchange.create_order(symbol, 'market', side, amount_final)
        pesan_notif += f"✅ Entry: {amount_final} (ISOLATED {leverage}x)\n"
        time.sleep(1)

        # 2. Pasang SL (Mark Price)
        params_sl = {'stopPrice': sl_final, 'reduceOnly': True, 'workingType': 'MARK_PRICE'}
        exchange.create_order(symbol, 'STOP_MARKET', side_close, amount_final, params=params_sl)
        pesan_notif += f"🛡️ SL (Mark): ${sl_final}\n"

        # 3. Pasang TP (Last Price)
        params_tp = {'stopPrice': tp_final, 'reduceOnly': True, 'workingType': 'CONTRACT_PRICE'}
        exchange.create_order(symbol, 'TAKE_PROFIT_MARKET', side_close, amount_final, params=params_tp)
        pesan_notif += f"💰 TP (Last): ${tp_final}\n"
        
        lapor_telegram(pesan_notif)
        time.sleep(1) 

    except Exception as e:
        error_msg = f"❌ GAGAL EKSEKUSI {symbol}: {e}"
        print(error_msg)
        lapor_telegram(error_msg)

# ==========================================
# 4. OTAK ANALISA (LOGIKA 15 MENIT)
# ==========================================
def analisa_satu_koin(data_koin):
    SYMBOL = data_koin['symbol']
    MODAL = data_koin['modal']     
    LEVERAGE = data_koin['leverage'] 

    try:
        # A. Cek Posisi Aktif
        positions = exchange.fetch_positions([SYMBOL])
        for pos in positions:
            if float(pos['contracts']) > 0:
                return # Skip kalau sudah punya posisi

        # B. Ambil Data
        # TREND: Ambil 1 Jam (H1) - Kita lihat gambaran besar
        df_big = ambil_data(SYMBOL, '1h', limit=200) 
        # EKSEKUSI: Ambil 15 Menit
        df = ambil_data(SYMBOL, '15m', limit=100)
        
        if df_big.empty or df.empty: return

        # C. Hitung Indikator
        
        # 1. Tren Besar (H1) - Pakai EMA 50 (Sesuai Config)
        df_big['EMA_Trend'] = df_big.ta.ema(length=config.EMA_TREND_H1) 
        trend_is_bullish = df_big.iloc[-1]['close'] > df_big.iloc[-1]['EMA_Trend']

        # 2. Indikator Eksekusi (15m)
        df['EMA_Fast'] = df.ta.ema(length=config.EMA_FAST) 
        df['EMA_Slow'] = df.ta.ema(length=config.EMA_SLOW)
        df['ATR'] = df.ta.atr(length=config.ATR_PERIOD)
        df['RSI'] = df.ta.rsi(length=config.RSI_PERIOD)
        df['Vol_MA'] = df['volume'].rolling(config.VOL_PERIOD).mean()
        
        last = df.iloc[-1]
        prev = df.iloc[-2] 

        # Logika Cross (Sinyal Entry)
        is_cross_up = (prev['EMA_Fast'] < prev['EMA_Slow']) and (last['EMA_Fast'] > last['EMA_Slow'])
        is_cross_down = (prev['EMA_Fast'] > prev['EMA_Slow']) and (last['EMA_Fast'] < last['EMA_Slow'])

        # Filter
        vol_confirm = prev['volume'] > (config.VOL_MULTIPLIER * prev['Vol_MA'])
        rsi_ok_long = last['RSI'] < config.RSI_BUY_LIMIT
        rsi_ok_short = last['RSI'] > config.RSI_SELL_LIMIT

        signal = "WAIT"
        
        # --- ENTRY RULES (TREND FOLLOWING) ---
        
        # LONG: Trend H1 Naik + Cross Up di 15m
        if trend_is_bullish:
            if is_cross_up and vol_confirm and rsi_ok_long:
                signal = "BUY / LONG"

        # SHORT: Trend H1 Turun + Cross Down di 15m
        elif not trend_is_bullish: 
            if is_cross_down and vol_confirm and rsi_ok_short:
                signal = "SELL / SHORT"
        
        # Status
        trend_text = "BULL" if trend_is_bullish else "BEAR"
        print(f"   > {SYMBOL:<9} | H1:{trend_text} | 15m Cross:{'YES' if is_cross_up or is_cross_down else 'NO'} | Sig:{signal}")

        # --- EKSEKUSI ---
        if signal != "WAIT":
            # Cek Saldo
            try:
                margin_butuh = MODAL / LEVERAGE 
                balance = exchange.fetch_balance()
                usdt_free = float(balance['USDT']['free'])
                if usdt_free < margin_butuh:
                    lapor_telegram(f"⚠️ GAGAL ENTRY {SYMBOL}! Saldo Kurang.")
                    return 
            except: pass

            # Hitung TP/SL
            atr = prev['ATR']
            jarak_sl = config.SL_MULTIPLIER * atr
            jarak_tp = (config.TP_MULTIPLIER * atr) * 0.95 # Safety margin

            sl, tp = 0, 0
            if "LONG" in signal:
                sl = last['close'] - jarak_sl
                tp = last['close'] + jarak_tp
            else:
                sl = last['close'] + jarak_sl
                tp = last['close'] - jarak_tp
            
            eksekusi_full_auto(SYMBOL, MODAL, LEVERAGE, signal, last['close'], sl, tp)

    except Exception as e:
        print(f"⚠️ Error {SYMBOL}: {e}")

# ==========================================
# 5. JANTUNG UTAMA (SMART LOOP 15 MENIT)
# ==========================================
if __name__ == "__main__":
    print("🤖 Bot Berjalan (Mode KONSERVATIF 15 Menit)...")
    
    while True:
        now = datetime.now()
        
        # --- LOGIKA SMART SLEEP 15 MENIT ---
        # Bot bangun di menit 00, 15, 30, 45 (Detik ke-5)
        # Rumus: (15 - (menit % 15))
        
        sisa_menit = 15 - (now.minute % 15)
        detik_tidur = (sisa_menit * 60) - now.second + 5
        
        print(f"\n[{now.strftime('%H:%M:%S')}] Menunggu candle 15m baru ({int(detik_tidur/60)}m {int(detik_tidur%60)}s)...")
        time.sleep(detik_tidur)
        
        # BANGUN!
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"\n[{timestamp}] 🕯️ CANDLE 15M BARU! SCANNING...")
        
        for koin in config.DAFTAR_KOIN:
            analisa_satu_koin(koin)
            time.sleep(1) 
            
        print("--- Scan Selesai ---")
        
        if datetime.now().minute < 15:
             lapor_telegram(f"👮 Laporan Rutin Jam {datetime.now().hour}:00. Bot Aman.")
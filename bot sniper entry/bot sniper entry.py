"""
===========================================================
BOT SNIPER ENTRY (SCALPING 1 MENIT) - FIXED LOGIC
===========================================================
Fitur Utama:
1. Sniper Mode: Tangkap pucuk saat RSI Extreme + Jebol EMA 5.
2. Trend Mode: Ikut arus saat EMA Cross (5 & 13).
3. Logic Fix: Menggunakan Candle 'Confirmed' (Prev vs Prev_2) 
   agar sinyal tidak hilang saat bot tidur.
===========================================================
"""
import ccxt
import pandas as pd
import pandas_ta as ta
import time
import requests 
from datetime import datetime
import config  # Pastikan file config.py ada di folder yang sama

print(f"--- 🤖 BOT SNIPER 1 MENIT (FIXED) STARTED ---")
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
    except: pass

lapor_telegram(f"🔔 BOT SNIPER START!\nStrategy: 1m Sniper + Trend")

def ambil_data(symbol, timeframe, limit=200):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        return df
    except:
        return pd.DataFrame()

# ==========================================
# 3. FUNGSI EKSEKUSI
# ==========================================
def eksekusi_full_auto(symbol, modal, leverage, signal, price, sl, tp):
    print(f"\n>>> 🚀 ACTION: {symbol} - {signal} DETECTED! ...")
    lapor_telegram(f"🔥 {symbol} EKSEKUSI {signal}!!!\nEntry: ${price}")
    
    try:
        try: exchange.cancel_all_orders(symbol)
        except: pass

        try: exchange.set_margin_mode('isolated', symbol)
        except: pass
        
        try: exchange.set_leverage(leverage, symbol)
        except: pass

        amount_coin = modal / price
        amount_final = exchange.amount_to_precision(symbol, amount_coin)
        sl_final = exchange.price_to_precision(symbol, sl)
        tp_final = exchange.price_to_precision(symbol, tp)
        
        side = 'buy' if "LONG" in signal else 'sell'
        side_close = 'sell' if side == 'buy' else 'buy'

        # 1. Entry Market
        exchange.create_order(symbol, 'market', side, amount_final)
        time.sleep(0.5)

        # 2. SL (Mark Price)
        params_sl = {'stopPrice': sl_final, 'reduceOnly': True, 'workingType': 'MARK_PRICE'}
        exchange.create_order(symbol, 'STOP_MARKET', side_close, amount_final, params=params_sl)

        # 3. TP (Last Price)
        params_tp = {'stopPrice': tp_final, 'reduceOnly': True, 'workingType': 'CONTRACT_PRICE'}
        exchange.create_order(symbol, 'TAKE_PROFIT_MARKET', side_close, amount_final, params=params_tp)
        
        print(f"✅ Order Sukses: {symbol}")

    except Exception as e:
        print(f"❌ Gagal Eksekusi {symbol}: {e}")

# ==========================================
# 4. OTAK ANALISA (LOGIKA SNIPER DIPERBAIKI)
# ==========================================
def analisa_satu_koin(data_koin):
    SYMBOL = data_koin['symbol']
    MODAL = data_koin['modal']     
    LEVERAGE = data_koin['leverage'] 

    try:
        # Cek Posisi (Biar gak double)
        positions = exchange.fetch_positions([SYMBOL])
        for pos in positions:
            if float(pos['contracts']) > 0: return 

        # Ambil Data
        df_big = ambil_data(SYMBOL, '15m', limit=100) 
        df = ambil_data(SYMBOL, '1m', limit=100)
        
        if df_big.empty or df.empty: return

        # Indikator
        df_big['EMA_Trend'] = df_big.ta.ema(length=config.EMA_TREND_H1) 
        trend_is_bullish = df_big.iloc[-1]['close'] > df_big.iloc[-1]['EMA_Trend']

        df['EMA_Fast'] = df.ta.ema(length=config.EMA_FAST) # EMA 5
        df['EMA_Slow'] = df.ta.ema(length=config.EMA_SLOW) # EMA 13
        df['ATR'] = df.ta.atr(length=config.ATR_PERIOD)
        df['RSI'] = df.ta.rsi(length=config.RSI_PERIOD)
        df['Vol_MA'] = df['volume'].rolling(config.VOL_PERIOD).mean()
        
        # --- LOGIKA FIXED (Prev vs Prev_2) ---
        # Kita pakai data candle yang BARU SAJA TUTUP (Confirmed)
        # Agar sinyal tidak hilang saat bot tidur
        
        last = df.iloc[-1]      # Candle Live (Jalan)
        prev = df.iloc[-2]      # Candle Baru Tutup (Menit lalu)
        prev_2 = df.iloc[-3]    # Candle 2 Menit lalu

        # 1. Logic Trend Follow (EMA Cross)
        # Cross terjadi di candle yang baru tutup
        is_cross_up = (prev_2['EMA_Fast'] < prev_2['EMA_Slow']) and (prev['EMA_Fast'] > prev['EMA_Slow'])
        is_cross_down = (prev_2['EMA_Fast'] > prev_2['EMA_Slow']) and (prev['EMA_Fast'] < prev['EMA_Slow'])
        
        vol_confirm = prev['volume'] > (config.VOL_MULTIPLIER * prev['Vol_MA'])

        # 2. Logic SNIPER (Reversal Pucuk)
        # Syarat Short: RSI > 75 DAN Candle baru tutup JEBOL ke bawah EMA 5 (padahal sebelumnya di atas)
        is_sniper_short = (prev['RSI'] > 75) and (prev['close'] < prev['EMA_Fast']) and (prev_2['close'] > prev_2['EMA_Fast'])
        
        # Syarat Long: RSI < 25 DAN Candle baru tutup JEBOL ke atas EMA 5
        is_sniper_long = (prev['RSI'] < 25) and (prev['close'] > prev['EMA_Fast']) and (prev_2['close'] < prev_2['EMA_Fast'])

        signal = "WAIT"
        tipe_entry = "-"

        # --- PRIORITAS SINYAL ---
        
        # 1. SNIPER (Counter Trend / Pucuk) -> Hajar duluan!
        if is_sniper_short:
            signal = "SELL / SHORT"
            tipe_entry = "SNIPER 🎯"
        elif is_sniper_long:
            signal = "BUY / LONG"
            tipe_entry = "SNIPER 🎯"
        
        # 2. TREND FOLLOWING (Ikut Arus) -> Kalau gak ada sniper
        elif signal == "WAIT":
            if trend_is_bullish and is_cross_up and vol_confirm:
                signal = "BUY / LONG"
                tipe_entry = "TREND 🌊"
            elif not trend_is_bullish and is_cross_down and vol_confirm:
                signal = "SELL / SHORT"
                tipe_entry = "TREND 🌊"
        
        print(f"   > {SYMBOL:<9} | RSI:{prev['RSI']:.1f} | Sig:{signal} ({tipe_entry})")

        # --- EKSEKUSI ---
        if signal != "WAIT":
            # Cek Saldo
            try:
                margin_butuh = MODAL / LEVERAGE 
                balance = exchange.fetch_balance()
                if float(balance['USDT']['free']) < margin_butuh: return 
            except: return

            atr = prev['ATR']
            
            # Setting TP/SL Khusus Sniper (Lebih Ketat)
            if "SNIPER" in tipe_entry:
                faktor_sl = 1.5 
                faktor_tp = 1.5 
            else:
                faktor_sl = config.SL_MULTIPLIER
                faktor_tp = config.TP_MULTIPLIER

            jarak_sl = faktor_sl * atr
            jarak_tp = faktor_tp * atr

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
# 5. LOOPING
# ==========================================
if __name__ == "__main__":
    print("🤖 Bot Berjalan (Mode SNIPER 1 Menit)...")
    while True:
        now = datetime.now()
        # Tidur sampai detik ke-5 menit berikutnya
        detik_tidur = 60 - now.second + 5
        if detik_tidur > 60: detik_tidur -= 60
        
        print(f"\n[{now.strftime('%H:%M:%S')}] Menunggu candle close... ({int(detik_tidur)}s)")
        time.sleep(detik_tidur)
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] SCANNING...")
        for koin in config.DAFTAR_KOIN:
            analisa_satu_koin(koin)
            time.sleep(1)
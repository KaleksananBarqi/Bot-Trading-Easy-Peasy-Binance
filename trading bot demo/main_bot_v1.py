"""
===========================================================
CHECKLIST FINAL (QUALITY CONTROL) - STRATEGI MAS AJI
===========================================================
1. Analisa Tren Besar (Timeframe H1)
 [ ] Indikator: EMA 200.
2. Analisa Eksekusi (Timeframe 15 Menit)
 [ ] Indikator Momentum: EMA 13 & EMA 21 (Cross).
3. Pemicu Entry (Trigger)
 [ ] Metode: Liquidity Grab (Sweep).
4. Filter Validasi
 [ ] Volume > 1.2x Rata-rata.
 [ ] MACD Searah.
 [ ] RSI Filter (60/40).
5. Manajemen Risiko
 [ ] SL: 2x ATR (Mark Price).
 [ ] TP: 3x ATR (Last Price).
 [ ] Mode: Isolated Margin.
6. Setelan Bot
 [ ] Smart Sleep (Cek tiap ganti candle 15m).
===========================================================
"""
import ccxt
import pandas as pd
import pandas_ta as ta
import time
import requests 
from datetime import datetime
import config  # Pastikan file config.py ada di folder yang sama

print(f"--- 🤖 MULTI-COIN BOT START ---")
print(f"Menjalankan {len(config.DAFTAR_KOIN)} Koin Sekaligus.")

# ==========================================
# 1. SETUP KONEKSI (UPDATED TIME SYNC)
# ==========================================
try:
    exchange = ccxt.binance({
        'apiKey': config.API_KEY,
        'secret': config.SECRET_KEY,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future',
            'adjustForTimeDifference': True, # Anti error timestamp
        }
    })
    
    # ⚠️ PENTING: Hapus tanda '#' di bawah ini jika pakai API MOCK TRADING
    exchange.enable_demo_trading(True)
    
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

lapor_telegram(f"🔔 BOT START!\nMemantau: {[k['symbol'] for k in config.DAFTAR_KOIN]}")

def ambil_data(symbol, timeframe, limit=200):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        return df
    except:
        return pd.DataFrame()

# ==========================================
# 3. FUNGSI EKSEKUSI (FINAL PERFECTED VERSION)
# ==========================================
def eksekusi_full_auto(symbol, modal, leverage, signal, price, sl, tp):
    print(f"\n>>> 🚀 ACTION: {symbol} - {signal} DETECTED! ...")
    
    pesan_notif = f"🔥 {symbol} EKSEKUSI {signal}!!!\n"
    pesan_notif += f"Harga Entry: ${price}\n"
    
    try:
        # A. BERSIH-BERSIH DULU (Hapus order lama yg nyangkut)
        try: exchange.cancel_all_orders(symbol)
        except: pass

        # B. SETTING MARGIN & LEVERAGE
        try: exchange.set_margin_mode('isolated', symbol)
        except: pass
        try: exchange.set_leverage(leverage, symbol)
        except: pass

        # C. HITUNG SIZE & HARGA (DENGAN PRECISION FIX)
        # 1. Size (Jumlah Koin)
        amount_coin = modal / price
        amount_final = exchange.amount_to_precision(symbol, amount_coin)
        
        # 2. Price (SL & TP) - Format harga biar diterima Binance
        sl_final = exchange.price_to_precision(symbol, sl)
        tp_final = exchange.price_to_precision(symbol, tp)
        
        side = 'buy' if "LONG" in signal else 'sell'
        side_close = 'sell' if side == 'buy' else 'buy'

        # D. EKSEKUSI BERUNTUN
        # 1. ENTRY MARKET
        exchange.create_order(symbol, 'market', side, amount_final)
        pesan_notif += f"✅ Entry: {amount_final} (ISOLATED)\n"
        time.sleep(1) # Jeda nafas

        # 2. PASANG SL (Mark Price - Anti Jarum)
        params_sl = {'stopPrice': sl_final, 'reduceOnly': True, 'workingType': 'MARK_PRICE'}
        exchange.create_order(symbol, 'STOP_MARKET', side_close, amount_final, params=params_sl)
        pesan_notif += f"🛡️ SL (Mark): ${sl_final}\n"

        # 3. PASANG TP (Last Price - Eksekusi Cepat)
        params_tp = {'stopPrice': tp_final, 'reduceOnly': True, 'workingType': 'CONTRACT_PRICE'}
        exchange.create_order(symbol, 'TAKE_PROFIT_MARKET', side_close, amount_final, params=params_tp)
        pesan_notif += f"💰 TP (Last): ${tp_final}\n"
        
        # Lapor Sukses
        lapor_telegram(pesan_notif)
        
        # Jeda dikit biar gak nabrak order koin lain di loop
        time.sleep(2) 

    except Exception as e:
        # ERROR HANDLING DARURAT
        # Kalau Entry Sukses tapi SL Gagal -> BAHAYA!
        error_msg = f"❌ CRITICAL ERROR {symbol}: {e}"
        print(error_msg)
        lapor_telegram(error_msg)

# ==========================================
# 4. OTAK ANALISA (Updated: Cek Saldo Dulu!)
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
                # Jika ada posisi, skip analisa (biar gak double entry)
                return 

        # B. Ambil Data
        df_big = ambil_data(SYMBOL, '1h', limit=200)
        df = ambil_data(SYMBOL, '15m', limit=100)
        
        if df_big.empty or df.empty: return

        # C. Hitung Indikator (Sesuai Config)
        df_big['EMA_200'] = df_big.ta.ema(length=config.EMA_TREND_H1) 
        trend_big = "BULLISH" if df_big.iloc[-1]['close'] > df_big.iloc[-1]['EMA_200'] else "BEARISH"

        df['EMA_Fast'] = df.ta.ema(length=config.EMA_FAST)
        df['EMA_Slow'] = df.ta.ema(length=config.EMA_SLOW)
        df['ATR'] = df.ta.atr(length=config.ATR_PERIOD)
        df['RSI'] = df.ta.rsi(length=config.RSI_PERIOD)
        df['Vol_MA'] = df['volume'].rolling(config.VOL_PERIOD).mean()
        
        macd = df.ta.macd(fast=12, slow=26, signal=9)
        df = pd.concat([df, macd], axis=1)
        
        df['low_liq'] = df['low'].rolling(config.LIQUIDITY_PERIOD).min().shift(1)
        df['high_liq'] = df['high'].rolling(config.LIQUIDITY_PERIOD).max().shift(1)
        
        last = df.iloc[-1]
        prev = df.iloc[-2]

        # Logic Vars
        macd_bull = last['MACD_12_26_9'] > last['MACDs_12_26_9']
        macd_bear = last['MACD_12_26_9'] < last['MACDs_12_26_9']
        vol_confirm = prev['volume'] > (config.VOL_MULTIPLIER * prev['Vol_MA'])
        rsi_ok_long = last['RSI'] < config.RSI_BUY_LIMIT
        rsi_ok_short = last['RSI'] > config.RSI_SELL_LIMIT
        cross_15m_bull = last['EMA_Fast'] > last['EMA_Slow']
        cross_15m_bear = last['EMA_Fast'] < last['EMA_Slow']

        signal = "WAIT"
        
        # --- ENTRY RULES ---
        if trend_big == "BULLISH":
            sweep = (prev['low'] < prev['low_liq']) and (prev['close'] > prev['low_liq'])
            if sweep and cross_15m_bull and vol_confirm and macd_bull and rsi_ok_long:
                signal = "BUY / LONG"

        elif trend_big == "BEARISH":
            sweep = (prev['high'] > prev['high_liq']) and (prev['close'] < prev['high_liq'])
            if sweep and cross_15m_bear and vol_confirm and macd_bear and rsi_ok_short:
                signal = "SELL / SHORT"
        
        print(f"   > {SYMBOL:<9} | H1:{trend_big:<7} | Sig:{signal}")

        # --- EKSEKUSI DENGAN PENGECEKAN SALDO ---
        if signal != "WAIT":
            
            # 1. CEK DOMPET DULU SEBELUM GAS
            margin_butuh = MODAL / LEVERAGE 
            
            try:
                balance = exchange.fetch_balance()
                usdt_free = balance['USDT']['free'] # Saldo nganggur
                
                if usdt_free < margin_butuh:
                    pesan_error = f"⚠️ GAGAL ENTRY {SYMBOL}!\nSaldo Kurang.\nButuh Margin: ${margin_butuh:.2f}\nSaldo Ada: ${usdt_free:.2f}"
                    print(pesan_error)
                    lapor_telegram(pesan_error)
                    return # BATALKAN PROSES
            except Exception as e:
                print(f"Gagal cek saldo: {e}")
                return 

            # 2. KALAU SALDO CUKUP, LANJUT HITUNG TP/SL
            atr = last['ATR']
            sl, tp = 0, 0
            
            if "LONG" in signal:
                sl = last['close'] - (config.SL_MULTIPLIER * atr)
                tp = last['close'] + (config.TP_MULTIPLIER * atr)
            else:
                sl = last['close'] + (config.SL_MULTIPLIER * atr)
                tp = last['close'] - (config.TP_MULTIPLIER * atr)
            
            # 3. PANGGIL EKSEKUTOR
            eksekusi_full_auto(SYMBOL, MODAL, LEVERAGE, signal, last['close'], sl, tp)

    except Exception as e:
        print(f"⚠️ Error {SYMBOL}: {e}")

# ==========================================
# 5. JANTUNG UTAMA (SMART LOOP)
# ==========================================
if __name__ == "__main__":
    print("🤖 Bot Berjalan (Mode Hemat Energi)...")
    lapor_telegram("Bot Start! Mode: Smart Sleep (Cek tiap ganti candle 15m).")

    while True:
        # 1. AMBIL WAKTU SEKARANG
        now = datetime.now()
        
        # 2. HITUNG MENIT BERIKUTNYA (Kelipatan 15)
        # Target waktu bangun: Tepat di menit kelipatan 15, detik ke-5
        sisa_menit = 15 - (now.minute % 15)
        detik_tidur = (sisa_menit * 60) - now.second + 5
        
        print(f"\n[{now.strftime('%H:%M:%S')}] Menunggu candle baru dalam {int(detik_tidur/60)} menit {int(detik_tidur%60)} detik...")
        
        # 3. TIDUR PANJANG (Smart Sleep)
        # Bot benar-benar diam, hemat CPU & Kuota
        time.sleep(detik_tidur)
        
        # 4. BANGUN & KERJA!
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"\n[{timestamp}] 🕯️ CANDLE BARU TERBENTUK! SCANNING...")
        
        # Looping scan semua koin
        for koin in config.DAFTAR_KOIN:
            analisa_satu_koin(koin)
            time.sleep(1) # Jeda dikit antar koin
            
        print("--- Scan Selesai ---")
        
        # Laporan Rutin Tiap Jam
        if datetime.now().minute < 15: # Lapor pas candle jam bulat baru mulai
             lapor_telegram(f"👮 Laporan Rutin Jam {datetime.now().hour}:00\nSemua Aman.")
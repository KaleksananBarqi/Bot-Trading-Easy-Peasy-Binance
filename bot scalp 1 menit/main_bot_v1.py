"""
===========================================================
BOT TRADING V1 - FINAL REVISION (SCALPING 1 MENIT)
===========================================================
1. Analisa Tren Besar: Timeframe 15 Menit (EMA Trend).
2. Analisa Eksekusi: Timeframe 1 Menit (EMA Cross/Momentum).
3. Trigger: Liquidity Sweep (1m).
4. Filter: Volume, MACD, RSI.
5. Manajemen Risiko:
   - SL: Mark Price (2x ATR).
   - TP: Last Price (Safety Margin 95% dari 2.5x ATR).
   - Mode: Isolated Margin.
6. Loop: Smart Sleep (Sinkron setiap ganti candle 1m).
===========================================================
"""
import ccxt
import pandas as pd
import pandas_ta as ta
import time
import requests 
from datetime import datetime
import config  # Pastikan file config.py ada di folder yang sama

print(f"--- 🤖 BOT SCALPING 1 MENIT STARTED ---")
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
            'adjustForTimeDifference': True, # Anti error timestamp
        }
    })
    
    # Cek Mode Demo/Live dari Config
    if getattr(config, 'DEMO_MODE', True): 
        exchange.enable_demo_trading(True)
        print("⚠️ MODE: DEMO TRADING (Paper Money)")
    else:
        print("🚨 MODE: LIVE TRADING (Real Money)")
    
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

# Kirim notifikasi awal
lapor_telegram(f"🔔 BOT START!\nStrategy: Scalping 1m (Trend 15m)\nMemantau: {[k['symbol'] for k in config.DAFTAR_KOIN]}")

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
# 3. FUNGSI EKSEKUSI (ORDERING)
# ==========================================
def eksekusi_full_auto(symbol, modal, leverage, signal, price, sl, tp):
    print(f"\n>>> 🚀 ACTION: {symbol} - {signal} DETECTED! ...")
    
    pesan_notif = f"🔥 {symbol} EKSEKUSI {signal}!!!\n"
    pesan_notif += f"Harga Entry: ${price}\n"
    
    try:
        # A. BERSIH-BERSIH DULU (Hapus order lama yg nyangkut / Zombie Order)
        try: exchange.cancel_all_orders(symbol)
        except: pass

        # B. SETTING MARGIN & LEVERAGE
        try: 
            exchange.set_margin_mode('isolated', symbol)
        except Exception: 
            pass # Lanjut aja kalau sudah isolated atau error api
        
        try: 
            exchange.set_leverage(leverage, symbol)
        except Exception as e:
            # Kalau set leverage gagal, batalkan trade karena resiko margin salah hitung
            raise Exception(f"Gagal set leverage: {e}")

        # C. HITUNG SIZE & HARGA
        # 1. Size (Jumlah Koin)
        amount_coin = modal / price
        amount_final = exchange.amount_to_precision(symbol, amount_coin)
        
        # 2. Price (SL & TP) - Format harga biar diterima Binance
        sl_final = exchange.price_to_precision(symbol, sl)
        tp_final = exchange.price_to_precision(symbol, tp)
        
        side = 'buy' if "LONG" in signal else 'sell'
        side_close = 'sell' if side == 'buy' else 'buy'

        # D. EKSEKUSI ORDER BERUNTUN
        # 1. ENTRY MARKET
        exchange.create_order(symbol, 'market', side, amount_final)
        pesan_notif += f"✅ Entry: {amount_final} (ISOLATED {leverage}x)\n"
        time.sleep(0.5) # Jeda nafas

        # 2. PASANG SL (Trigger: Mark Price)
        params_sl = {'stopPrice': sl_final, 'reduceOnly': True, 'workingType': 'MARK_PRICE'}
        exchange.create_order(symbol, 'STOP_MARKET', side_close, amount_final, params=params_sl)
        pesan_notif += f"🛡️ SL (Mark): ${sl_final}\n"

        # 3. PASANG TP (Trigger: Last Price)
        params_tp = {'stopPrice': tp_final, 'reduceOnly': True, 'workingType': 'CONTRACT_PRICE'}
        exchange.create_order(symbol, 'TAKE_PROFIT_MARKET', side_close, amount_final, params=params_tp)
        pesan_notif += f"💰 TP (Last): ${tp_final}\n"
        
        # Lapor Sukses
        lapor_telegram(pesan_notif)
        time.sleep(1) 

    except Exception as e:
        error_msg = f"❌ GAGAL EKSEKUSI {symbol}: {e}"
        print(error_msg)
        lapor_telegram(error_msg)

# ==========================================
# 4. OTAK ANALISA (HIGH ACCURACY: ADX + STOCHRSI)
# ==========================================
def analisa_satu_koin(data_koin):
    SYMBOL = data_koin['symbol']
    MODAL = data_koin['modal']     
    LEVERAGE = data_koin['leverage'] 

    try:
        # A. Cek Posisi Aktif
        positions = exchange.fetch_positions([SYMBOL])
        for pos in positions:
            if float(pos['contracts']) > 0: return 

        # B. Ambil Data
        df_big = ambil_data(SYMBOL, '15m', limit=config.EMA_TREND_H1 + 50) 
        df = ambil_data(SYMBOL, '1m', limit=100)
        
        if df_big.empty or df.empty: return

        # C. Hitung Indikator
        
        # 1. Trend Filter (15m)
        df_big['EMA_Trend'] = df_big.ta.ema(length=config.EMA_TREND_H1) 
        trend_is_bullish = df_big.iloc[-1]['close'] > df_big.iloc[-1]['EMA_Trend']

        # 2. Indikator Eksekusi (1m)
        df['EMA_Fast'] = df.ta.ema(length=config.EMA_FAST) 
        df['EMA_Slow'] = df.ta.ema(length=config.EMA_SLOW) 
        df['ATR'] = df.ta.atr(length=config.ATR_PERIOD)
        df['Vol_MA'] = df['volume'].rolling(config.VOL_PERIOD).mean()
        
        # --- INDIKATOR BARU: ADX & StochRSI ---
        # ADX (Kekuatan Tren)
        adx_df = df.ta.adx(length=config.ADX_PERIOD)
        # Pandas TA menamakan kolomnya ADX_14, DMP_14, DMN_14. Kita ambil ADX nya aja.
        col_adx = f"ADX_{config.ADX_PERIOD}"
        df['ADX'] = adx_df[col_adx]

        # StochRSI (Momentum Cepat)
        stoch_rsi = df.ta.stochrsi(length=config.STOCHRSI_PERIOD, rsi_length=14, k=3, d=3)
        # Nama kolomnya biasanya STOCHRSIk_14_14_3_3 dan STOCHRSId_14_14_3_3
        df['Stoch_K'] = stoch_rsi.iloc[:, 0] # Kolom pertama (K)
        df['Stoch_D'] = stoch_rsi.iloc[:, 1] # Kolom kedua (D)
        
        # Ambil Data Terakhir
        last = df.iloc[-1]
        prev = df.iloc[-2] 

        # --- LOGIKA ENTRY PRESISI ---
        
        # 1. Cek Cross EMA (Trigger Utama)
        is_cross_up = (prev['EMA_Fast'] < prev['EMA_Slow']) and (last['EMA_Fast'] > last['EMA_Slow'])
        is_cross_down = (prev['EMA_Fast'] > prev['EMA_Slow']) and (last['EMA_Fast'] < last['EMA_Slow'])

        # 2. Filter ADX (Anti Sideways)
        # Kalau ADX di bawah 20, market lagi males gerak. Jangan masuk.
        trend_strong = last['ADX'] > config.ADX_MINIMUM

        # 3. Filter Volume
        vol_confirm = prev['volume'] > (config.VOL_MULTIPLIER * prev['Vol_MA'])
        
        # 4. Filter StochRSI (Cari yang murah/mahal)
        # Buy hanya kalau StochRSI tidak di pucuk (masih punya ruang naik)
        stoch_ok_buy = last['Stoch_K'] < 80 
        # Sell hanya kalau StochRSI tidak di dasar (masih punya ruang turun)
        stoch_ok_sell = last['Stoch_K'] > 20

        signal = "WAIT"
        alasan = ""
        
        # RULE: ENTRY HANYA JIKA TREND KUAT (ADX > 20)
        if trend_strong:
            
            # SKENARIO LONG
            if trend_is_bullish and is_cross_up and vol_confirm and stoch_ok_buy:
                signal = "BUY / LONG"
                alasan = f"ADX:{last['ADX']:.1f} | Vol:{vol_confirm}"

            # SKENARIO SHORT
            elif not trend_is_bullish and is_cross_down and vol_confirm and stoch_ok_sell:
                signal = "SELL / SHORT"
                alasan = f"ADX:{last['ADX']:.1f} | Vol:{vol_confirm}"
        
        # Print monitoring (Biar tau kenapa bot gak entry)
        trend_text = "BULL" if trend_is_bullish else "BEAR"
        status_adx = "KUAT" if trend_strong else "LEMAH (SKIP)"
        print(f"   > {SYMBOL:<9} | H1:{trend_text} | ADX:{last['ADX']:.1f} ({status_adx}) | Sig:{signal}")

        # --- EKSEKUSI ---
        if signal != "WAIT":
            # Cek Saldo
            try:
                margin_butuh = MODAL / LEVERAGE 
                balance = exchange.fetch_balance()
                if float(balance['USDT']['free']) < margin_butuh: return 
            except: return

            atr = prev['ATR']
            
            # SL & TP
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
# 5. JANTUNG UTAMA (SMART LOOP 1 MENIT)
# ==========================================
if __name__ == "__main__":
    print("🤖 Bot Berjalan (Mode SCALPING 1 Menit)...")
    
    while True:
        now = datetime.now()
        
        # --- LOGIKA SMART SLEEP 1 MENIT ---
        # Bot akan tidur dan bangun tepat di detik ke-5 setiap menit baru.
        # Contoh: 10:00:05, 10:01:05, dst.
        # Ini memberi waktu exchange untuk menutup candle 1 menit sebelumnya.
        
        detik_tidur = 60 - now.second + 5
        if detik_tidur > 60: detik_tidur -= 60
        
        print(f"\n[{now.strftime('%H:%M:%S')}] Menunggu candle 1m baru ({int(detik_tidur)} detik)...")
        time.sleep(detik_tidur)
        
        # BANGUN!
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"\n[{timestamp}] 🕯️ CANDLE 1M BARU! SCANNING...")
        
        # Scan semua koin
        for koin in config.DAFTAR_KOIN:
            analisa_satu_koin(koin)
            time.sleep(1) # Jeda dikit antar koin biar API gak spam
            
        print("--- Scan Selesai ---")
        
        # Laporan Rutin (Tiap Jam, di menit ke-1)
        if datetime.now().minute == 1:
             lapor_telegram(f"👮 Laporan Rutin Jam {datetime.now().hour}:00. Bot Scalping 1m Aman.")
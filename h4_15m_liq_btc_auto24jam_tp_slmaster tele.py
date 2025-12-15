import ccxt
import pandas as pd
import pandas_ta as ta
import time
import requests 
from datetime import datetime

# --- 1. KONFIGURASI PRIBADI ---
API_KEY = 'Vir005RqmDLFeQFaOzlijfaY9yONcJiYAqfgB9snJXxWei2wjoOcmYmTHtlLurCM'
SECRET_KEY = '0le4T0ByB2a6CAPKtooKIz4gZ65rICCpOksfMCSkNP9WGSoc1ssQViQEsWs0WDzp'

# --- KONFIGURASI TELEGRAM ---
TELEGRAM_TOKEN = '8494523779:AAExn6kcQUevwGzNa9ZEsnh9hq3w3hTThL0'
TELEGRAM_CHAT_ID = '1256933697'

SYMBOL = 'BTC/USDT'
MODAL_USDT = 1000   
LEVERAGE = 10       

print(f"--- 🤖 BOT CEREWET AKTIF: {SYMBOL} ---")

# --- 2. SETUP KONEKSI ---
try:
    exchange = ccxt.binance({
        'apiKey': API_KEY,
        'secret': SECRET_KEY,
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    })
    exchange.enable_demo_trading(True)
    print("✅ Koneksi Binance Demo: BERHASIL")
except Exception as e:
    print(f"❌ Gagal Konek Binance: {e}")
    exit()

# --- FUNGSI LAPOR TELEGRAM ---
def lapor_telegram(pesan):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {'chat_id': TELEGRAM_CHAT_ID, 'text': pesan}
        requests.post(url, data=data)
    except Exception as e:
        print(f"Gagal kirim Telegram: {e}")

# Kirim notifikasi saat bot pertama nyala
lapor_telegram(f"🔔 BOT START!\nPair: {SYMBOL}\nSaya akan laporan setiap scan (30 detik).")

# --- 3. FUNGSI UTAMA ---

def ambil_data(symbol, timeframe, limit=200):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        return df
    except:
        return pd.DataFrame()

def eksekusi_full_auto(signal, price, stop_loss, take_profit):
    print(f"\n>>> 🚀 ACTION: {signal} DETECTED! EKSEKUSI...")
    
    # Pesan Notifikasi Khusus Entry
    pesan_notif = f"🔥 EKSEKUSI {signal}!!!\n"
    pesan_notif += f"Harga: ${price}\n"
    
    try:
        try: exchange.set_leverage(LEVERAGE, SYMBOL)
        except: pass

        amount_btc = MODAL_USDT / price
        amount_final = exchange.amount_to_precision(SYMBOL, amount_btc)
        
        side = 'buy' if "LONG" in signal else 'sell'
        side_close = 'sell' if side == 'buy' else 'buy'

        # 1. ORDER ENTRY
        order_entry = exchange.create_order(SYMBOL, 'market', side, amount_final)
        print(f"✅ Entry Sukses! ID: {order_entry['id']}")
        pesan_notif += f"✅ Entry: {amount_final} BTC\n"
        
        time.sleep(1)

        # 2. ORDER SL
        params_sl = {'stopPrice': stop_loss, 'reduceOnly': True}
        exchange.create_order(SYMBOL, 'STOP_MARKET', side_close, amount_final, params=params_sl)
        print(f"🛡️ SL Terpasang: ${stop_loss:.2f}")
        pesan_notif += f"🛡️ SL: ${stop_loss:.2f}\n"

        # 3. ORDER TP
        params_tp = {'stopPrice': take_profit, 'reduceOnly': True}
        exchange.create_order(SYMBOL, 'TAKE_PROFIT_MARKET', side_close, amount_final, params=params_tp)
        print(f"💰 TP Terpasang: ${take_profit:.2f}")
        pesan_notif += f"💰 TP: ${take_profit:.2f}\n"
        
        pesan_notif += "😴 Bot istirahat 15 Menit..."
        
        # KIRIM LAPORAN KE HP
        lapor_telegram(pesan_notif)
        
        print("⏸️ Bot istirahat 15 menit...")
        time.sleep(900) 

    except Exception as e:
        error_msg = f"❌ ERROR EKSEKUSI: {e}"
        print(error_msg)
        lapor_telegram(error_msg)

def analisa_market():
    try:
        # Cek Posisi Aktif
        positions = exchange.fetch_positions([SYMBOL])
        for pos in positions:
            if float(pos['contracts']) > 0:
                pnl = round(float(pos['unrealizedPnl']), 2)
                # Lapor posisi aktif juga biar tenang
                pesan_aktif = f"⏳ POSISI AKTIF\nPnL: {pnl} USDT\nMenunggu TP/SL..."
                print(pesan_aktif)
                lapor_telegram(pesan_aktif)
                return 

        # Ambil Data
        df_big = ambil_data(SYMBOL, '1h', limit=200) # H1 Trend
        if df_big.empty: return
        df_big['EMA_200'] = df_big.ta.ema(length=200)
        trend_big = "BULLISH" if df_big.iloc[-1]['close'] > df_big.iloc[-1]['EMA_200'] else "BEARISH"

        df = ambil_data(SYMBOL, '15m', limit=100) # 15m Eksekusi
        if df.empty: return
        
        # Indikator
        df['EMA_13'] = df.ta.ema(length=13)
        df['EMA_21'] = df.ta.ema(length=21)
        df['ATR'] = df.ta.atr(length=14)
        df['RSI'] = df.ta.rsi(length=14)
        df['Vol_MA'] = df['volume'].rolling(20).mean()
        
        macd = df.ta.macd(fast=12, slow=26, signal=9)
        df = pd.concat([df, macd], axis=1)
        
        df['low_liq'] = df['low'].rolling(20).min().shift(1)
        df['high_liq'] = df['high'].rolling(20).max().shift(1)
        
        last = df.iloc[-1]
        prev = df.iloc[-2]

        # Logic Vars
        macd_bull = last['MACD_12_26_9'] > last['MACDs_12_26_9']
        macd_bear = last['MACD_12_26_9'] < last['MACDs_12_26_9']
        vol_confirm = prev['volume'] > (1.2 * prev['Vol_MA'])
        rsi_ok_long = last['RSI'] < 60
        rsi_ok_short = last['RSI'] > 40
        cross_15m_bull = last['EMA_13'] > last['EMA_21']
        cross_15m_bear = last['EMA_13'] < last['EMA_21']

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

        # --- UPDATE: SMART NOTIFICATION ---
        jam_sekarang = datetime.now()
        menit_sekarang = jam_sekarang.minute
        
        pesan_status = f"[{jam_sekarang.strftime('%H:%M')}] {SYMBOL} | H1:{trend_big} | 15m:{'UP' if cross_15m_bull else 'DOWN'}"
        print(pesan_status) # Di Laptop tetap print terus biar kita tau dia jalan
        
        # LOGIKA: Lapor Telegram HANYA JIKA...
        # 1. Ada Sinyal (BUY/SELL) -> WAJIB LAPOR
        # 2. ATAU.. Pas menit ke-0 (Setiap 1 jam sekali) buat absen doang
        
        if signal != "WAIT":
            # Kalau ada sinyal, lapor entry nanti di fungsi eksekusi_full_auto
            pass 
            
        elif menit_sekarang == 0:
            # Laporan rutin tiap jam (misal jam 10:00, 11:00) biar tau bot masih hidup
            lapor_telegram(f"👮 Laporan Rutin (Per Jam)\n{pesan_status}\nStatus: Aman (WAIT)")
        
        if signal != "WAIT":
            atr = last['ATR']
            sl, tp = 0, 0
            if "LONG" in signal:
                sl = last['close'] - (2 * atr)
                tp = last['close'] + (3 * atr)
            else:
                sl = last['close'] + (2 * atr)
                tp = last['close'] - (3 * atr)
                
            eksekusi_full_auto(signal, last['close'], sl, tp)

    except Exception as e:
        print(f"⚠️ Error: {e}")
        time.sleep(5)

if __name__ == "__main__":
    print("Bot mulai berjalan... (Scan tiap 1 menit, Lapor WAIT tiap 1 jam)")
    
    # Variabel buat ngitung waktu laporan
    last_report_time = 0
    
    while True:
        # 1. Jalankan Analisa seperti biasa
        # Kita modifikasi sedikit pemanggilan fungsinya agar return status
        # (Perlu edit dikit fungsi analisa_market di atas biar return signal)
        
        # --- CARA GAMPANG: UPDATE LOGIKA LAPOR DI DALAM FUNGSI ---
        # (Lihat instruksi di bawah kode ini untuk update fungsi analisa_market)
        
        analisa_market()
        
        # 2. Tidur 60 Detik (1 Menit)
        # Ini waktu paling ideal buat Timeframe 15m
        time.sleep(60)
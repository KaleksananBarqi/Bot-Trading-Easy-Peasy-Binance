import ccxt
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime

# --- 1. KONFIGURASI PRIBADI ---
API_KEY = 'Vir005RqmDLFeQFaOzlijfaY9yONcJiYAqfgB9snJXxWei2wjoOcmYmTHtlLurCM'
SECRET_KEY = '0le4T0ByB2a6CAPKtooKIz4gZ65rICCpOksfMCSkNP9WGSoc1ssQViQEsWs0WDzp'

SYMBOL = 'BTC/USDT'
MODAL_USDT = 1000   # Modal per posisi
LEVERAGE = 10       # Leverage

print(f"--- 🤖 BOT AUTO PILOT 24 JAM: {SYMBOL} ---")
print("Tekan Ctrl + C untuk menghentikan bot.")

# --- 2. SETUP KONEKSI ---
try:
    exchange = ccxt.binance({
        'apiKey': API_KEY,
        'secret': SECRET_KEY,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future',
        }
    })
    exchange.enable_demo_trading(True)
    print("✅ Koneksi Server Demo: BERHASIL\n")
except Exception as e:
    print(f"❌ Gagal Konek: {e}")
    exit()

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
    
    try:
        # A. Pastikan Leverage
        try: exchange.set_leverage(LEVERAGE, SYMBOL)
        except: pass

        # B. Hitung Size
        amount_btc = MODAL_USDT / price
        amount_final = exchange.amount_to_precision(SYMBOL, amount_btc)
        
        # Tentukan Sisi (Side)
        side = 'buy' if "LONG" in signal else 'sell'
        side_close = 'sell' if side == 'buy' else 'buy' # Kebalikan untuk TP/SL

        # C. ORDER 1: ENTRY POSISI
        order_entry = exchange.create_order(SYMBOL, 'market', side, amount_final)
        print(f"✅ 1. Entry Sukses! ID: {order_entry['id']} | Size: {amount_final} BTC")
        
        # Tunggu 1 detik biar server Binance mencatat posisi dulu
        time.sleep(1)

        # D. ORDER 2: PASANG STOP LOSS (STOP_MARKET)
        # Penting: reduceOnly=True artinya order ini cuma buat nutup, gak bisa buka posisi baru
        params_sl = {'stopPrice': stop_loss, 'reduceOnly': True}
        order_sl = exchange.create_order(SYMBOL, 'STOP_MARKET', side_close, amount_final, params=params_sl)
        print(f"🛡️ 2. Stop Loss Terpasang di ${stop_loss:.2f}")

        # E. ORDER 3: PASANG TAKE PROFIT (TAKE_PROFIT_MARKET)
        params_tp = {'stopPrice': take_profit, 'reduceOnly': True}
        order_tp = exchange.create_order(SYMBOL, 'TAKE_PROFIT_MARKET', side_close, amount_final, params=params_tp)
        print(f"💰 3. Take Profit Terpasang di ${take_profit:.2f}")
        
        print(">>> SEMUA ORDER SELESAI. POSISI AMAN. KEMBALI MONITORING...")
        
        # JEDA LAMA SETELAH ENTRY (Misal 15 menit)
        # Supaya bot tidak 'bingung' dan open posisi lagi di candle yang sama
        print("⏸️ Bot istirahat 15 menit agar tidak spam order di candle yang sama...")
        time.sleep(900) 

    except Exception as e:
        print(f"❌ ERROR EKSEKUSI: {e}")
        print("Cek saldo atau minimal order size.")

def analisa_market():
    # KITA PAKAI TRY-EXCEPT BIAR KALAU ERROR INTERNET, BOT GAK MATI (RESTART SENDIRI)
    try:
        # A. CEK POSISI AKTIF DULU
        # Kalau sudah punya posisi, JANGAN analisa/beli lagi. Fokus monitoring saja.
        positions = exchange.fetch_positions([SYMBOL])
        for pos in positions:
            if float(pos['contracts']) > 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ Posisi sedang aktif (PnL: {pos['unrealizedPnl']} USDT). Menunggu TP/SL...")
                return # Stop analisa, biarkan posisi jalan

        # B. ANALISA TREN (H1)
        df_big = ambil_data(SYMBOL, '1h', limit=200)
        if df_big.empty: return

        df_big['EMA_200'] = df_big.ta.ema(length=200)
        last_big = df_big.iloc[-1]
        
        trend_big = "BULLISH" if last_big['close'] > last_big['EMA_200'] else "BEARISH"

        # C. ANALISA EKSEKUSI (15m)
        df = ambil_data(SYMBOL, '15m', limit=100)
        if df.empty: return
        
        # Indikator
        df['EMA_13'] = df.ta.ema(length=13)
        df['EMA_21'] = df.ta.ema(length=21)
        df['ATR'] = df.ta.atr(length=14)
        df['RSI'] = df.ta.rsi(length=14)
        df['Vol_MA'] = df['volume'].rolling(20).mean()
        
        # MACD
        macd = df.ta.macd(fast=12, slow=26, signal=9)
        df = pd.concat([df, macd], axis=1)
        
        # Liquidity Grab
        df['low_liq'] = df['low'].rolling(20).min().shift(1)
        df['high_liq'] = df['high'].rolling(20).max().shift(1)
        
        last = df.iloc[-1]
        prev = df.iloc[-2]

        # Logic Filter
        macd_bull = last['MACD_12_26_9'] > last['MACDs_12_26_9']
        macd_bear = last['MACD_12_26_9'] < last['MACDs_12_26_9']
        vol_confirm = prev['volume'] > (1.2 * prev['Vol_MA'])
        rsi_ok_long = last['RSI'] < 60
        rsi_ok_short = last['RSI'] > 40
        cross_15m_bull = last['EMA_13'] > last['EMA_21']
        cross_15m_bear = last['EMA_13'] < last['EMA_21']

        signal = "WAIT"
        
        # LOGIKA ENTRY FINAL
        if trend_big == "BULLISH":
            sweep = (prev['low'] < prev['low_liq']) and (prev['close'] > prev['low_liq'])
            if sweep and cross_15m_bull and vol_confirm and macd_bull and rsi_ok_long:
                signal = "BUY / LONG"

        elif trend_big == "BEARISH":
            sweep = (prev['high'] > prev['high_liq']) and (prev['close'] < prev['high_liq'])
            if sweep and cross_15m_bear and vol_confirm and macd_bear and rsi_ok_short:
                signal = "SELL / SHORT"

        # TAMPILAN STATUS (Update tiap 30 detik)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] H1:{trend_big} | 15m Cross:{'UP' if cross_15m_bull else 'DOWN'} | Sinyal:{signal}")
        
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
        print(f"⚠️ Error Sementara: {e}")
        time.sleep(5)

# --- 4. LOOPING UTAMA (JANTUNG BOT) ---
if __name__ == "__main__":
    print("Bot mulai memantau pasar setiap 30 detik...")
    while True:
        analisa_market()
        # Bot tidur 30 detik sebelum cek lagi (Biar gak kena limit API)
        time.sleep(30)
"""
===========================================================
CHECKLIST FINAL (QUALITY CONTROL) - STRATEGI MAS AJI
===========================================================

1. Analisa Tren Besar (Timeframe H1)
 [ ] Indikator: EMA 200.
 [ ] Aturan:
     Harga di atas EMA 200 = Hanya cari BUY (Bullish).
     Harga di bawah EMA 200 = Hanya cari SELL (Bearish).

2. Analisa Eksekusi (Timeframe 15 Menit)
 [ ] Indikator Momentum: EMA 13 & EMA 21.
 [ ] Aturan Cross:
     Buy: Garis EMA 13 (Cepat) harus di atas EMA 21.
     Sell: Garis EMA 13 (Cepat) harus di bawah EMA 21.

3. Pemicu Entry (Trigger)
 [ ] Metode: Liquidity Grab (Sweep).
     Buy: Harga menusuk Low terendah dari 20 candle terakhir, tapi Close candle kembali naik.
     Sell: Harga menusuk High tertinggi dari 20 candle terakhir, tapi Close candle kembali turun.

4. Filter Validasi (Syarat Wajib)
 [ ] Volume: Volume candle saat sweep harus > 1.2x rata-rata volume 20 candle terakhir (Tanda bandar masuk).
 [ ] MACD: Garis Biru harus searah (Biru di atas Oranye untuk Buy, dan sebaliknya).
 [ ] RSI:
     Buy: RSI harus di bawah 60 (Belum kemahalan).
     Sell: RSI harus di atas 40 (Belum kemurahan).

5. Manajemen Risiko (Otomatis)
 [ ] Stop Loss (SL): Jarak 2x ATR dari harga entry.
 [ ] Take Profit (TP): Jarak 3x ATR dari harga entry (Risk:Reward 1:1.5).
 [ ] Tipe Order: Market Order (Langsung eksekusi).
 [ ] Modal: $1000 per posisi (Leverage 10x).

6. Setelan Bot
 [ ] Looping: Bot mengecek pasar setiap 60 detik (1 menit).
 [ ] Notifikasi Telegram:
     Laporan Entry: Instan (Real-time).
     Laporan Wait: Setiap jam (biar tidak spam).
 [ ] Cooldown: Setelah entry, bot istirahat 15 menit (mencegah open posisi ganda di candle yang sama).

===========================================================
"""

import ccxt
import pandas as pd
import pandas_ta as ta
import time
import requests 
from datetime import datetime

# ==========================================
# ⚙️ KONFIGURASI PRIBADI (ISI INI DULU!)
# ==========================================
API_KEY = 'Vir005RqmDLFeQFaOzlijfaY9yONcJiYAqfgB9snJXxWei2wjoOcmYmTHtlLurCM'
SECRET_KEY = '0le4T0ByB2a6CAPKtooKIz4gZ65rICCpOksfMCSkNP9WGSoc1ssQViQEsWs0WDzp'

# Konfigurasi Telegram
TELEGRAM_TOKEN = '8494523779:AAExn6kcQUevwGzNa9ZEsnh9hq3w3hTThL0'
TELEGRAM_CHAT_ID = '1256933697'

# Konfigurasi Trading
SYMBOL = 'BNB/USDT'
MODAL_USDT = 1000   # Modal per posisi (USD)
LEVERAGE = 10       # Leverage 10x

print(f"--- 🤖 BOT TRADING FINAL: {SYMBOL} ---")
print("Fitur: Strategi Lengkap + Auto TP/SL + Smart Notif")

# ==========================================
# 1. SETUP KONEKSI BINANCE DEMO
# ==========================================
try:
    exchange = ccxt.binance({
        'apiKey': API_KEY,
        'secret': SECRET_KEY,
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    })
    exchange.enable_demo_trading(True)
    print("✅ Koneksi Server Demo: BERHASIL")
except Exception as e:
    print(f"❌ Gagal Konek Binance: {e}")
    exit()

# ==========================================
# 2. FUNGSI PENDUKUNG
# ==========================================

def lapor_telegram(pesan):
    """Fungsi buat kirim pesan ke HP"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {'chat_id': TELEGRAM_CHAT_ID, 'text': pesan}
        requests.post(url, data=data)
    except Exception as e:
        print(f"⚠️ Gagal lapor Telegram: {e}")

# Lapor saat bot pertama kali nyala
lapor_telegram(f"🔔 BOT START! ({SYMBOL})\nMode: Scan tiap 1 menit.\nLaporan rutin: Tiap 1 jam.\nLaporan ENTRY: INSTAN!")

def ambil_data(symbol, timeframe, limit=200):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        return df
    except:
        return pd.DataFrame()

# ==========================================
# 3. FUNGSI EKSEKUSI (AUTO TP/SL)
# ==========================================
def eksekusi_full_auto(signal, price, stop_loss, take_profit):
    print(f"\n>>> 🚀 ACTION: {signal} DETECTED! EKSEKUSI...")
    
    # Siapkan Laporan Telegram (Akan dikirim LANGSUNG)
    pesan_notif = f"🔥 EKSEKUSI {signal}!!!\n"
    pesan_notif += f"Harga: ${price}\n"
    
    try:
        # Set Leverage
        try: exchange.set_leverage(LEVERAGE, SYMBOL)
        except: pass

        # Hitung Size Order
        amount_BNB = MODAL_USDT / price
        amount_final = exchange.amount_to_precision(SYMBOL, amount_BNB)
        
        side = 'buy' if "LONG" in signal else 'sell'
        side_close = 'sell' if side == 'buy' else 'buy'

        # A. ORDER UTAMA (MARKET)
        order_entry = exchange.create_order(SYMBOL, 'market', side, amount_final)
        print(f"✅ Entry Sukses! ID: {order_entry['id']}")
        pesan_notif += f"✅ Entry: {amount_final} BNB\n"
        
        time.sleep(1) # Jeda sebentar biar server nafas

        # B. PASANG SL (STOP MARKET)
        params_sl = {'stopPrice': stop_loss, 'reduceOnly': True}
        exchange.create_order(SYMBOL, 'STOP_MARKET', side_close, amount_final, params=params_sl)
        print(f"🛡️ SL Terpasang: ${stop_loss:.2f}")
        pesan_notif += f"🛡️ SL: ${stop_loss:.2f}\n"

        # C. PASANG TP (TAKE PROFIT MARKET)
        params_tp = {'stopPrice': take_profit, 'reduceOnly': True}
        exchange.create_order(SYMBOL, 'TAKE_PROFIT_MARKET', side_close, amount_final, params=params_tp)
        print(f"💰 TP Terpasang: ${take_profit:.2f}")
        pesan_notif += f"💰 TP: ${take_profit:.2f}\n"
        
        pesan_notif += "😴 Bot istirahat 15 Menit..."
        
        # --- KIRIM NOTIFIKASI SEKARANG JUGA ---
        lapor_telegram(pesan_notif)
        
        print("⏸️ Bot cooldown 15 menit agar tidak spam di candle yang sama...")
        time.sleep(900) 

    except Exception as e:
        error_msg = f"❌ ERROR EKSEKUSI: {e}"
        print(error_msg)
        lapor_telegram(error_msg)

# ==========================================
# 4. OTAK ANALISA (STRATEGI KAMU)
# ==========================================
def analisa_market():
    try:
        # A. Cek Apakah Punya Posisi?
        positions = exchange.fetch_positions([SYMBOL])
        for pos in positions:
            if float(pos['contracts']) > 0:
                pnl = round(float(pos['unrealizedPnl']), 2)
                # Kalau punya posisi, Lapor rutin aja kalau pas jam-nya
                if datetime.now().minute == 0:
                    lapor_telegram(f"⏳ POSISI AKTIF\nPnL: {pnl} USDT\nMenunggu TP/SL...")
                print(f"Posisi Aktif (PnL: {pnl}). Skip analisa.")
                return 

        # B. Ambil Data Tren Besar (H1)
        df_big = ambil_data(SYMBOL, '15m', limit=200)
        if df_big.empty: return
        
        # Strategi H1: Harga di atas/bawah EMA 200
        df_big['EMA_200'] = df_big.ta.ema(length=200)
        last_big = df_big.iloc[-1]
        
        trend_big = "NETRAL"
        if last_big['close'] > last_big['EMA_200']: trend_big = "BULLISH"
        elif last_big['close'] < last_big['EMA_200']: trend_big = "BEARISH"

        # C. Ambil Data Eksekusi (15m)
        df = ambil_data(SYMBOL, '15m', limit=100)
        if df.empty: return
        
        # Hitung Semua Indikator
        df['EMA_13'] = df.ta.ema(length=13)
        df['EMA_21'] = df.ta.ema(length=21)
        df['ATR'] = df.ta.atr(length=14)
        df['RSI'] = df.ta.rsi(length=14)
        df['Vol_MA'] = df['volume'].rolling(20).mean()
        
        macd = df.ta.macd(fast=12, slow=26, signal=9)
        df = pd.concat([df, macd], axis=1)
        
        # Liquidity Grab (Low/High 20 Candle Terakhir)
        df['low_liq'] = df['low'].rolling(20).min().shift(1)
        df['high_liq'] = df['high'].rolling(20).max().shift(1)
        
        last = df.iloc[-1]
        prev = df.iloc[-2] # Candle Konfirmasi (yang baru close)

        # Variabel Filter
        macd_bull = last['MACD_12_26_9'] > last['MACDs_12_26_9']
        macd_bear = last['MACD_12_26_9'] < last['MACDs_12_26_9']
        vol_confirm = prev['volume'] > (1.2 * prev['Vol_MA'])
        rsi_ok_long = last['RSI'] < 60
        rsi_ok_short = last['RSI'] > 40
        
        # EMA Cross 15m (Momentum Pendek)
        cross_15m_bull = last['EMA_13'] > last['EMA_21']
        cross_15m_bear = last['EMA_13'] < last['EMA_21']

        signal = "WAIT"
        reason = "-"
        
        # --- LOGIKA ENTRY FINAL ---
        
        # 1. SETUP LONG
        if trend_big == "BULLISH":
            # Sweep Support (Nusuk Bawah lalu Balik Naik)
            sweep = (prev['low'] < prev['low_liq']) and (prev['close'] > prev['low_liq'])
            
            # Wajib Cross UP + Volume + MACD + RSI + Tren H1
            if sweep and cross_15m_bull and vol_confirm and macd_bull and rsi_ok_long:
                signal = "BUY / LONG"
                reason = "Sweep Support + 15m Cross Up + H1 Bull"

        # 2. SETUP SHORT
        elif trend_big == "BEARISH":
            # Sweep Resistance (Nusuk Atas lalu Balik Turun)
            sweep = (prev['high'] > prev['high_liq']) and (prev['close'] < prev['high_liq'])
            
            # Wajib Cross DOWN + Volume + MACD + RSI + Tren H1
            if sweep and cross_15m_bear and vol_confirm and macd_bear and rsi_ok_short:
                signal = "SELL / SHORT"
                reason = "Sweep Resist + 15m Cross Down + H1 Bear"

        # --- LAPORAN STATUS (SMART NOTIF) ---
        jam_sekarang = datetime.now()
        info_status = f"[{jam_sekarang.strftime('%H:%M')}] {SYMBOL} | Trend H1:{trend_big} | Signal:{signal}"
        print(info_status) # Selalu print di laptop biar tau jalan
        
        # KEPUTUSAN EKSEKUSI
        if signal != "WAIT":
            # HITUNG TP/SL
            atr = last['ATR']
            sl, tp = 0, 0
            
            if "LONG" in signal:
                sl = last['close'] - (2 * atr)
                tp = last['close'] + (3 * atr)
            else:
                sl = last['close'] + (2 * atr)
                tp = last['close'] - (3 * atr)
            
            # EKSEKUSI SEKARANG (Notif Entry ada di dalam fungsi ini)
            eksekusi_full_auto(signal, last['close'], sl, tp)
            
        else:
            # KALAU WAIT: Cuma lapor Telegram pas menit ke-0 (Ganti Jam)
            if jam_sekarang.minute == 0:
                 lapor_telegram(f"👮 Laporan Rutin\n{info_status}\nStatus: Aman (Monitoring)")

    except Exception as e:
        print(f"⚠️ Error Loop: {e}")
        time.sleep(5)

# ==========================================
# 5. JANTUNG UTAMA (LOOPING)
# ==========================================
if __name__ == "__main__":
    print("Bot berjalan... (Tekan Ctrl+C untuk stop)")
    while True:
        analisa_market()
        # Scan setiap 1 Menit (60 Detik)
        time.sleep(60)
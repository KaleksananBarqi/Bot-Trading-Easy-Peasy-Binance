import ccxt
import pandas as pd
import pandas_ta as ta
import time

# --- 1. KONFIGURASI PRIBADI ---
API_KEY = 'Vir005RqmDLFeQFaOzlijfaY9yONcJiYAqfgB9snJXxWei2wjoOcmYmTHtlLurCM'
SECRET_KEY = '0le4T0ByB2a6CAPKtooKIz4gZ65rICCpOksfMCSkNP9WGSoc1ssQViQEsWs0WDzp'

SYMBOL = 'BTC/USDT'
MODAL_USDT = 1000   # Modal per posisi (USD)
LEVERAGE = 10       # Leverage

print(f"--- BOT TRADING: {SYMBOL} (FINAL STRATEGY) ---")

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
    print("✅ Koneksi Demo Berhasil!")
except Exception as e:
    print(f"❌ Gagal Konek: {e}")
    exit()

# --- 3. FUNGSI ---

def ambil_data(symbol, timeframe, limit=200):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        return df
    except:
        return pd.DataFrame()

def eksekusi_market(signal, price, stop_loss, take_profit):
    print(f"\n>>> 🚀 MENGEKSEKUSI SINYAL {signal}...")
    try:
        exchange.set_leverage(LEVERAGE, SYMBOL)
    except: pass

    try:
        amount_btc = MODAL_USDT / price
        amount_final = exchange.amount_to_precision(SYMBOL, amount_btc)
        side = 'buy' if "LONG" in signal else 'sell'
        
        order = exchange.create_order(SYMBOL, 'market', side, amount_final)
        
        print(f"✅ ORDER SUKSES! ID: {order['id']}")
        print(f"   Posisi: {side.upper()} {amount_final} BTC")
        print(f"⚠️ PASANG MANUAL -> SL: ${stop_loss:.2f} | TP: ${take_profit:.2f}")
    except Exception as e:
        print(f"❌ Gagal Eksekusi: {e}")

def analisa_market():
    print(f"\n[{pd.Timestamp.now()}] Menganalisa Pasar...")
    
    # ------------------------------------------
    # A. ANALISA TREN BESAR (H1) - HARGA vs EMA 200
    # ------------------------------------------
    # (Sesuai request: Tidak pakai Cross, hanya arah tren umum)
    df_big = ambil_data(SYMBOL, '1h', limit=200)
    if df_big.empty: return

    df_big['EMA_200'] = df_big.ta.ema(length=200)
    last_big = df_big.iloc[-1]
    
    trend_big = "NETRAL"
    if last_big['close'] > last_big['EMA_200']:
        trend_big = "BULLISH"
    else:
        trend_big = "BEARISH"
        
    print(f"1. Tren Besar (H1)  : {trend_big} (Harga vs EMA 200)")

    # ------------------------------------------
    # B. ANALISA EKSEKUSI (15m) - EMA CROSS 13/21 + SWEEP
    # ------------------------------------------
    df = ambil_data(SYMBOL, '15m', limit=100)
    if df.empty: return
    
    # Indikator 15m
    df['EMA_13'] = df.ta.ema(length=13)
    df['EMA_21'] = df.ta.ema(length=21) # Cross di timeframe kecil
    df['ATR'] = df.ta.atr(length=14)
    df['RSI'] = df.ta.rsi(length=14)
    df['Vol_MA'] = df['volume'].rolling(20).mean()
    
    # MACD
    macd = df.ta.macd(fast=12, slow=26, signal=9)
    df = pd.concat([df, macd], axis=1)
    
    # Liquidity Zones (Sweep)
    df['low_liq'] = df['low'].rolling(20).min().shift(1)
    df['high_liq'] = df['high'].rolling(20).max().shift(1)
    
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Cek Indikator
    macd_bull = last['MACD_12_26_9'] > last['MACDs_12_26_9']
    macd_bear = last['MACD_12_26_9'] < last['MACDs_12_26_9']
    
    vol_confirm = prev['volume'] > (1.2 * prev['Vol_MA'])
    rsi_ok_long = last['RSI'] < 60
    rsi_ok_short = last['RSI'] > 40

    # Cek EMA Cross di 15m
    cross_15m_bull = last['EMA_13'] > last['EMA_21']
    cross_15m_bear = last['EMA_13'] < last['EMA_21']

    signal = "WAIT"
    reason = "-"
    
    # --- LOGIKA KEPUTUSAN FINAL ---
    
    # LONG (Tren Besar Bullish + 15m Cross Up + Sweep Support)
    if trend_big == "BULLISH":
        sweep = (prev['low'] < prev['low_liq']) and (prev['close'] > prev['low_liq'])
        
        if sweep and cross_15m_bull and vol_confirm and macd_bull and rsi_ok_long:
            signal = "BUY / LONG"
            reason = "H1 Bull + 15m Cross Up + Sweep Support"

    # SHORT (Tren Besar Bearish + 15m Cross Down + Sweep Resist)
    elif trend_big == "BEARISH":
        sweep = (prev['high'] > prev['high_liq']) and (prev['close'] < prev['high_liq'])
        
        if sweep and cross_15m_bear and vol_confirm and macd_bear and rsi_ok_short:
            signal = "SELL / SHORT"
            reason = "H1 Bear + 15m Cross Down + Sweep Resist"

    # Output
    print(f"2. Harga BTC    : ${last['close']}")
    print(f"3. EMA 15m      : 13={last['EMA_13']:.1f} | 21={last['EMA_21']:.1f}")
    print(f"4. Status Bot   : {signal}")
    
    if signal != "WAIT":
        atr = last['ATR']
        if "LONG" in signal:
            sl = last['close'] - (2 * atr)
            tp = last['close'] + (3 * atr)
        else:
            sl = last['close'] + (2 * atr)
            tp = last['close'] - (3 * atr)
            
        print(f"   Alasan: {reason}")
        eksekusi_market(signal, last['close'], sl, tp)
    else:
        print("   (Menunggu setup valid...)")

if __name__ == "__main__":
    analisa_market()
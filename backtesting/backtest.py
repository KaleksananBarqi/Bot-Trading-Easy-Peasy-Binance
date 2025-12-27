import ccxt
import pandas as pd
import pandas_ta as ta
import config
import time
from datetime import datetime

# ==========================================
# KONFIGURASI BACKTEST
# ==========================================
SYMBOL_TO_TEST = 'ETH/USDT'  # Ganti koin yang mau di tes
JUMLAH_CANDLE = 10000         # Seberapa jauh ke belakang
SALDO_AWAL = 100             # Simulasi saldo USDT
LEVERAGE = config.DEFAULT_LEVERAGE

# ==========================================
# ENGINE BACKTEST
# ==========================================
def fetch_data(symbol, timeframe, limit):
    print(f"📥 Mengambil data historis {symbol} ({timeframe})...")
    exchange = ccxt.binance()
    bars = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
    df['time'] = pd.to_datetime(df['time'], unit='ms')
    return df

def apply_indicators(df):
    # Copy paste logika indikator dari bot.py agar 100% sama
    df['EMA_FAST'] = df.ta.ema(length=config.EMA_FAST)
    df['EMA_SLOW'] = df.ta.ema(length=config.EMA_SLOW)
    df['EMA_MAJOR'] = df.ta.ema(length=config.EMA_TREND_MAJOR)
    df['ATR'] = df.ta.atr(length=config.ATR_PERIOD)
    adx = df.ta.adx(length=config.ADX_PERIOD)
    df['ADX'] = adx[f"ADX_{config.ADX_PERIOD}"]
    df['RSI'] = df.ta.rsi(length=14)
    bb = df.ta.bbands(length=config.BB_LENGTH, std=config.BB_STD)
    df['BBL'] = bb[f'BBL_{config.BB_LENGTH}_{config.BB_STD}']
    df['BBU'] = bb[f'BBU_{config.BB_LENGTH}_{config.BB_STD}']
    stoch = df.ta.stochrsi(length=config.STOCHRSI_LEN, rsi_length=config.STOCHRSI_LEN, k=config.STOCHRSI_K, d=config.STOCHRSI_D)
    df['STOCH_K'] = stoch.iloc[:, 0]
    df['STOCH_D'] = stoch.iloc[:, 1]
    return df

def calculate_entry_logic(row, prev_row, use_liq_hunt):
    # Logika Signal (Copy dari bot.py)
    signal = None
    strategy_type = "NONE"
    
    adx_val = prev_row['ADX']
    current_price = prev_row['close']
    current_rsi = prev_row['RSI']
    
    # --- LOGIC SIGNAL SAMA PERSIS DENGAN BOT ---
    if adx_val > config.ADX_LIMIT_TREND:
        # Trending Logic
        is_perfect_uptrend = (prev_row['close'] > prev_row['EMA_FAST']) and \
                             (prev_row['EMA_FAST'] > prev_row['EMA_SLOW']) and \
                             (prev_row['EMA_SLOW'] > prev_row['EMA_MAJOR'])
        
        if is_perfect_uptrend and (current_price < prev_row['BBU']) and (current_rsi < 70):
            signal = "LONG"
            strategy_type = "TREND_STRONG"

        is_perfect_downtrend = (prev_row['close'] < prev_row['EMA_FAST']) and \
                               (prev_row['EMA_FAST'] < prev_row['EMA_SLOW']) and \
                               (prev_row['EMA_SLOW'] < prev_row['EMA_MAJOR'])
        
        if is_perfect_downtrend and (current_price > prev_row['BBL']) and (current_rsi > 30):
            signal = "SHORT"
            strategy_type = "TREND_STRONG"
            
    else:
        # Sideways Logic
        is_at_bottom = current_price <= (prev_row['BBL'] * 1.002)
        is_stoch_buy = (prev_row['STOCH_K'] > prev_row['STOCH_D']) and (prev_row['STOCH_K'] < 30)
        if is_at_bottom and is_stoch_buy:
            signal = "LONG"
            strategy_type = "SCALP_REVERSAL"
            
        is_at_top = current_price >= (prev_row['BBU'] * 0.998)
        is_stoch_sell = (prev_row['STOCH_K'] < prev_row['STOCH_D']) and (prev_row['STOCH_K'] > 70)
        if is_at_top and is_stoch_sell:
            signal = "SHORT"
            strategy_type = "SCALP_REVERSAL"

    if not signal:
        return None

    # --- HITUNG HARGA ENTRY/SL/TP (Liquidity Hunt Logic) ---
    atr = prev_row['ATR']
    
    # 1. Logic Retail Original
    retail_sl_dist = atr * config.ATR_MULTIPLIER_SL
    retail_tp_dist = atr * config.ATR_MULTIPLIER_TP1
    
    if signal == "LONG":
        retail_sl = current_price - retail_sl_dist
        retail_tp = current_price + retail_tp_dist
    else:
        retail_sl = current_price + retail_sl_dist
        retail_tp = current_price - retail_tp_dist

    # 2. Modifikasi Liquidity Hunt
    if use_liq_hunt:
        entry_price = retail_sl # Entry di SL Retail
        tp_price = retail_tp    # Target tetap TP Retail (High RR)
        
        safety_sl_dist = atr * getattr(config, 'TRAP_SAFETY_SL', 1.0)
        if signal == "LONG":
            sl_price = entry_price - safety_sl_dist
        else:
            sl_price = entry_price + safety_sl_dist
            
        return {
            "signal": signal, "type": "LIMIT", "strategy": strategy_type,
            "entry": entry_price, "sl": sl_price, "tp": tp_price, 
            "original_price_at_signal": current_price
        }
    else:
        return {
            "signal": signal, "type": "MARKET", "strategy": strategy_type,
            "entry": current_price, "sl": retail_sl, "tp": retail_tp
        }

def run_backtest():
    df = fetch_data(SYMBOL_TO_TEST, config.TIMEFRAME_EXEC, JUMLAH_CANDLE)
    df = apply_indicators(df)
    
    # State Variables
    balance = SALDO_AWAL
    position = None # {'type': 'LONG', 'entry': 100, 'sl': 90, 'tp': 120}
    pending_order = None # {'type': 'LONG', 'entry': 95, ...}
    
    history = []
    win = 0
    loss = 0
    missed_orders = 0 # Order limit yg gak kejemput
    
    print(f"\n🚀 MEMULAI BACKTEST: {SYMBOL_TO_TEST}")
    print(f"🔹 Mode: {'LIQUIDITY HUNT (LIMIT)' if config.USE_LIQUIDITY_HUNT else 'NORMAL (MARKET)'}")
    print(f"🔹 Range: {df['time'].iloc[0]} s/d {df['time'].iloc[-1]}")
    print("-" * 60)

    # Loop Candle demi Candle
    for i in range(50, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        # 1. CEK POSISI AKTIF (Apakah kena SL/TP?)
        if position:
            pnl = 0
            exit_reason = ""
            
            if position['signal'] == 'LONG':
                if row['low'] <= position['sl']:
                    exit_reason = "SL Hit 🔴"
                    pnl = (position['sl'] - position['entry']) / position['entry'] * LEVERAGE
                elif row['high'] >= position['tp']:
                    exit_reason = "TP Hit 🟢"
                    pnl = (position['tp'] - position['entry']) / position['entry'] * LEVERAGE
            
            elif position['signal'] == 'SHORT':
                if row['high'] >= position['sl']:
                    exit_reason = "SL Hit 🔴"
                    pnl = (position['entry'] - position['sl']) / position['entry'] * LEVERAGE
                elif row['low'] <= position['tp']:
                    exit_reason = "TP Hit 🟢"
                    pnl = (position['entry'] - position['tp']) / position['entry'] * LEVERAGE
            
            if exit_reason:
                balance = balance + (balance * pnl)
                history.append({'time': row['time'], 'type': exit_reason, 'pnl': f"{pnl*100:.2f}%", 'bal': balance})
                if pnl > 0: win += 1 
                else: loss += 1
                position = None # Clear posisi
                continue # Lanjut ke candle berikutnya

        # 2. CEK PENDING ORDER (Khusus Limit/Liq Hunt)
        if pending_order:
            # Apakah harga market menjemput order limit kita?
            filled = False
            if pending_order['signal'] == 'LONG':
                # Entry Long ke-fill jika Low candle ini < Harga Limit
                if row['low'] <= pending_order['entry']:
                    filled = True
            elif pending_order['signal'] == 'SHORT':
                # Entry Short ke-fill jika High candle ini > Harga Limit
                if row['high'] >= pending_order['entry']:
                    filled = True
            
            if filled:
                position = pending_order
                pending_order = None
                print(f"⚡ ORDER FILLED! {position['signal']} @ {position['entry']:.4f} (Time: {row['time']})")
            else:
                # Opsi: Cancel order jika terlalu lama? (Misal 10 candle)
                # Disini kita biarkan dulu, atau reset jika ada sinyal baru
                pass

        # 3. CARI SIGNAL BARU (Jika tidak ada posisi)
        # Kita hanya cari sinyal jika tidak ada posisi aktif DAN tidak ada pending order
        if not position and not pending_order:
            trade_setup = calculate_entry_logic(row, prev_row, config.USE_LIQUIDITY_HUNT)
            
            if trade_setup:
                if trade_setup['type'] == 'MARKET':
                    # Langsung Entry
                    position = trade_setup
                    print(f"OPEN {position['signal']} (Market) @ {position['entry']:.4f}")
                else:
                    # Pasang Pending Order
                    pending_order = trade_setup
                    dist_pct = abs(trade_setup['entry'] - trade_setup['original_price_at_signal']) / trade_setup['original_price_at_signal'] * 100
                    print(f"⏳ PENDING {trade_setup['signal']} (Trap) @ {trade_setup['entry']:.4f} (Jarak: {dist_pct:.2f}%)")

    # ==========================================
    # REPORT
    # ==========================================
    print("\n" + "="*30)
    print("📊 HASIL BACKTEST")
    print("="*30)
    print(f"Total Trade Terisi : {win + loss}")
    print(f"Win                : {win}")
    print(f"Loss               : {loss}")
    if (win+loss) > 0:
        print(f"Win Rate           : {(win / (win+loss)) * 100:.2f}%")
    else:
        print("Win Rate           : 0%")
    print(f"Saldo Akhir        : ${balance:.2f} (Awal $100)")
    
    # Bersihkan pending order sisa
    if pending_order:
        print(f"⚠️ Note: Ada 1 pending order yang tidak terjemput sampai akhir data.")

if __name__ == "__main__":
    try:
        run_backtest()
    except KeyboardInterrupt:
        print("Backtest dibatalkan.")
    except Exception as e:
        print(f"Error: {e}")
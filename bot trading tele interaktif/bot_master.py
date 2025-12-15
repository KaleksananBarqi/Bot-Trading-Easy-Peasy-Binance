import telebot
import threading
import json
import time
import ccxt
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import config 

print("--- 🤖 BOT MASTER: INTERACTIVE + SMART LOGIC V1 ---")

# ==========================================
# 1. SETUP & DATABASE
# ==========================================
bot = telebot.TeleBot(config.TELEGRAM_TOKEN)
CACHE_POSISI = {} # Memori untuk melacak posisi yang sedang berjalan

def load_settings():
    try:
        with open('settings.json', 'r') as f: return json.load(f)
    except: 
        # Default settings jika file hilang
        return {
            "bot_active": False,
            "modal_usdt": 20,
            "leverage": 10,
            "daftar_koin": ["BTC/USDT", "ETH/USDT"],
            "margin_mode": "isolated"
        }

def save_settings(new_data):
    with open('settings.json', 'w') as f: json.dump(new_data, f, indent=4)

# Koneksi Binance
try:
    exchange = ccxt.binance({
        'apiKey': config.API_KEY,
        'secret': config.SECRET_KEY,
        'enableRateLimit': True,
        'options': {'defaultType': 'future', 'adjustForTimeDifference': True}
    })
    exchange.enable_demo_trading(True) # UNCOMMENT UTK DEMO/PAPER TRADING
    print("✅ Binance Connected.")
except Exception as e:
    print(f"❌ Error Binance: {e}")
    exit()

# ==========================================
# 2. FITUR TELEGRAM (CONTROL & MONITOR)
# ==========================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    teks = """
🤖 **COMMAND CENTER** 🤖

💰 /saldo - Cek Saldo Detail
🔍 /posisi - Cek Posisi & PnL
🚀 /on - Nyalakan Trading
🛑 /off - Matikan Trading
    """
    bot.reply_to(message, teks, parse_mode="Markdown")

@bot.message_handler(commands=['on', 'off'])
def switch_bot(message):
    if str(message.chat.id) != str(config.TELEGRAM_CHAT_ID): return
    data = load_settings()
    perintah = message.text.replace("/", "")
    if perintah == "on":
        data['bot_active'] = True
        bot.reply_to(message, "✅ **BOT ON!** Mencari momentum...")
    else:
        data['bot_active'] = False
        bot.reply_to(message, "🛑 **BOT OFF.** Standby.")
    save_settings(data)

@bot.message_handler(commands=['posisi'])
def cek_posisi_handler(message):
    if str(message.chat.id) != str(config.TELEGRAM_CHAT_ID): return
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        positions = exchange.fetch_positions()
        text = "📈 **POSISI AKTIF:**\n\n"
        total_pnl = 0
        found = False
        
        for pos in positions:
            if float(pos['contracts']) > 0:
                found = True
                pnl = float(pos['unrealizedPnl'])
                total_pnl += pnl
                icon = "🟢" if pnl >= 0 else "🔴"
                text += f"{icon} **{pos['symbol']}** ({pos['side'].upper()})\n   PnL: ${pnl:.2f} ({float(pos['percentage']):.2f}%)\n\n"
        
        if not found: text = "💤 Tidak ada posisi aktif."
        else: text += f"💰 Total PnL: ${total_pnl:.2f}"
        
        bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['saldo'])
def cek_saldo_detail(message):
    if str(message.chat.id) != str(config.TELEGRAM_CHAT_ID): return
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        bal = exchange.fetch_balance()['info']
        teks = f"""
💰 **DOMPET FUTURE**
💵 Wallet: `${float(bal['totalWalletBalance']):.2f}`
⚠️ Unrea. PnL: `${float(bal['totalUnrealizedProfit']):.2f}`
✅ Available: `${float(bal['availableBalance']):.2f}`
        """
        bot.reply_to(message, teks, parse_mode="Markdown")
    except:
        bot.reply_to(message, "❌ Gagal ambil saldo.")

def lapor_trading(pesan):
    try: bot.send_message(config.TELEGRAM_CHAT_ID, pesan)
    except: pass

# ==========================================
# 3. FITUR "DETEKTIF" (MONITOR POSISI BACKGROUND)
# ==========================================
def monitor_posisi_background():
    global CACHE_POSISI
    try:
        positions = exchange.fetch_positions()
        current_active = {}
        
        # 1. Catat posisi sekarang
        for pos in positions:
            if float(pos['contracts']) > 0:
                current_active[pos['symbol']] = float(pos['unrealizedPnl'])
        
        # 2. Bandingkan dengan memory lama
        for symbol in CACHE_POSISI:
            if symbol not in current_active:
                # Posisi HILANG = Closed (TP/SL)
                time.sleep(2) # Tunggu server update history
                trades = exchange.fetch_my_trades(symbol, limit=1)
                if trades:
                    last = trades[-1]
                    pnl = float(last['info'].get('realizedPnl', 0))
                    if pnl > 0: lapor_trading(f"🏆 **TP HIT: {symbol}**\nProfit: +${pnl:.2f} 💰")
                    elif pnl < 0: lapor_trading(f"🛡️ **SL HIT: {symbol}**\nLoss: ${pnl:.2f} 🩹")
        
        CACHE_POSISI = current_active
    except Exception as e:
        print(f"⚠️ Error Monitor: {e}")

# ==========================================
# 4. LOGIKA ANALISA & TRADING (SMART V1)
# ==========================================
def ambil_data(symbol, timeframe, limit=100):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        return df
    except: return pd.DataFrame()

def eksekusi_trade(symbol, signal, price, sl, tp, modal, leverage):
    lapor_trading(f"🚀 **ENTRY {signal}: {symbol}**\nPrice: ${price}\nTP: ${tp:.2f} | SL: ${sl:.2f}")
    
    try:
        # Cancel order lama & Set Leverage
        exchange.cancel_all_orders(symbol)
        try: exchange.set_margin_mode('isolated', symbol)
        except: pass 
        exchange.set_leverage(leverage, symbol)

        # Hitung Amount
        amount = exchange.amount_to_precision(symbol, modal / price)
        sl_price = exchange.price_to_precision(symbol, sl)
        tp_price = exchange.price_to_precision(symbol, tp)
        
        side = 'buy' if "LONG" in signal else 'sell'
        side_close = 'sell' if side == 'buy' else 'buy'

        # 1. Market Order
        exchange.create_order(symbol, 'market', side, amount)
        
        # 2. Stop Loss (Mark Price)
        params_sl = {'stopPrice': sl_price, 'reduceOnly': True, 'workingType': 'MARK_PRICE'}
        exchange.create_order(symbol, 'STOP_MARKET', side_close, amount, params=params_sl)
        
        # 3. Take Profit (Last Price - Agresif)
        params_tp = {'stopPrice': tp_price, 'reduceOnly': True, 'workingType': 'CONTRACT_PRICE'}
        exchange.create_order(symbol, 'TAKE_PROFIT_MARKET', side_close, amount, params=params_tp)

        lapor_trading("✅ Order Terpasang!")
        
    except Exception as e:
        lapor_trading(f"❌ Gagal Eksekusi {symbol}: {e}")

def analisa_market_loop():
    print("🚀 TRADING ENGINE STARTED...")
    lapor_trading("🤖 **BOT MASTER ONLINE**\nLogic: Smart V1 (H1 Trend + 5m Entry)")

    while True:
        # --- TASK 1: MONITOR POSISI (Jalan setiap detik) ---
        monitor_posisi_background()
        
        # --- TASK 2: CEK WAKTU UTK ANALISA (Hanya saat candle close 5m) ---
        settings = load_settings()
        if not settings['bot_active']:
            time.sleep(10)
            continue 

        now = datetime.now()
        # Jika belum waktu ganti candle (detik != 5), skip analisa berat
        # Kita kasih toleransi: Analisa dilakukan di detik ke-5 setiap kelipatan 5 menit
        # Biar gak terlalu berat. Tapi utk coding simpel, kita pakai sleep mechanism di bawah.
        
        for symbol in settings['daftar_koin']:
            try:
                # Skip jika sudah punya posisi
                if symbol in CACHE_POSISI: continue 

                # 1. DATA BIG TREND (15m/1H)
                df_big = ambil_data(symbol, '1h', 100) # Cek Trend H1
                df_big['EMA_Trend'] = ta.ema(df_big['close'], length=config.EMA_TREND_H1)
                trend_bull = df_big.iloc[-1]['close'] > df_big.iloc[-1]['EMA_Trend']

                # 2. DATA ENTRY (5m)
                df = ambil_data(symbol, '5m', 100)
                if df.empty: continue

                # Indikator
                df['EMA_Fast'] = ta.ema(df['close'], length=config.EMA_FAST)
                df['EMA_Slow'] = ta.ema(df['close'], length=config.EMA_SLOW)
                df['RSI'] = ta.rsi(df['close'], length=config.RSI_PERIOD)
                df['ATR'] = ta.atr(df['high'], df['low'], df['close'], length=config.ATR_PERIOD)
                
                # MACD
                macd = df.ta.macd(fast=12, slow=26, signal=9)
                df = pd.concat([df, macd], axis=1)
                
                # Liquidity Logic
                df['liq_low'] = df['low'].rolling(config.LIQUIDITY_PERIOD).min().shift(1)
                df['liq_high'] = df['high'].rolling(config.LIQUIDITY_PERIOD).max().shift(1)

                last = df.iloc[-1]
                prev = df.iloc[-2]
                
                # Naming Column MACD (Dinamis dari pandas_ta)
                macd_col = 'MACD_12_26_9'
                macds_col = 'MACDs_12_26_9'
                
                # --- LOGIC ENTRY ---
                signal = "WAIT"
                
                # Setup BUY
                if trend_bull:
                    # Syarat 1: Sweep Liquidity Bawah
                    sweep = (prev['low'] < prev['liq_low']) and (prev['close'] > prev['liq_low'])
                    # Syarat 2: MACD Bullish Cross/Up
                    macd_bull = last[macd_col] > last[macds_col]
                    # Syarat 3: RSI Tidak Overbought
                    rsi_safe = last['RSI'] < config.RSI_BUY_LIMIT
                    
                    if sweep and macd_bull and rsi_safe:
                        signal = "BUY / LONG"

                # Setup SELL (Kebalikan)
                if not trend_bull:
                    sweep = (prev['high'] > prev['liq_high']) and (prev['close'] < prev['liq_high'])
                    macd_bear = last[macd_col] < last[macds_col]
                    rsi_safe = last['RSI'] > config.RSI_SELL_LIMIT
                    
                    if sweep and macd_bear and rsi_safe:
                        signal = "SELL / SHORT"
                
                print(f"> {symbol} | Trend H1: {'UP' if trend_bull else 'DOWN'} | Sig: {signal}")

                if signal != "WAIT":
                    # Cek Saldo
                    bal = exchange.fetch_balance()['USDT']['free']
                    margin = settings['modal_usdt'] / settings['leverage']
                    if bal < margin:
                        lapor_trading(f"⚠️ Signal {symbol} skip! Saldo kurang.")
                        continue

                    # Hitung TP/SL
                    atr = last['ATR']
                    sl_dist = atr * config.SL_MULTIPLIER
                    tp_dist = (atr * config.TP_MULTIPLIER) * 0.95 # Safety diskon
                    
                    if "LONG" in signal:
                        sl = last['close'] - sl_dist
                        tp = last['close'] + tp_dist
                    else:
                        sl = last['close'] + sl_dist
                        tp = last['close'] - tp_dist
                        
                    eksekusi_trade(symbol, signal, last['close'], sl, tp, settings['modal_usdt'], settings['leverage'])
                    time.sleep(5) # Jeda biar gak double order

            except Exception as e:
                print(f"Err {symbol}: {e}")
            
            time.sleep(1) # Jeda antar koin

        # SMART SLEEP (Tidur sampai candle 5 menit berikutnya)
        now = datetime.now()
        sleep_sec = (5 - (now.minute % 5)) * 60 - now.second + 5
        # Kalau sleepnya kelamaan (>300 detik), batasi aja check posisi tiap 10 detik
        # Tapi karena kita butuh MONITOR POSISI terus, kita sleep pendek2 aja
        # Logic: Tidur 10 detik, loop lagi. Tapi Analisa cuma jalan kalau menit % 5 == 0
        
        # Revisi Logic Loop: Tidur pendek agar Telegram & Monitor Posisi responsif
        print("💤 Standby monitor... (Cek chart tiap ganti candle)")
        for _ in range(30): # Tidur 30 detik total, tapi responsive
            time.sleep(1) 

# ==========================================
# 5. JALANKAN THREADING
# ==========================================
if __name__ == "__main__":
    # Thread 1: Telegram Bot
    t_tele = threading.Thread(target=bot.infinity_polling)
    t_tele.start()
    
    # Main Thread: Trading Engine
    try:
        analisa_market_loop()
    except KeyboardInterrupt:
        bot.stop_polling()
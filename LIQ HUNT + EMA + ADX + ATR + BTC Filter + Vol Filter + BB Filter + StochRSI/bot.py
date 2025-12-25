import asyncio
import ccxt.async_support as ccxt
import pandas as pd
import pandas_ta as ta
import time
import requests
import sys
import os
import logging
import config 

# --- LOGGING & GLOBALS ---
last_entry_time = {}
exchange = None
positions_cache = set()
open_orders_cache = set()  # <--- [BARU] Cache untuk menyimpan antrian order
global_btc_trend = "NEUTRAL"
last_btc_check = 0

logging.basicConfig(filename='bot_trading.log', level=logging.INFO, format='%(asctime)s - %(message)s')

async def kirim_tele(pesan, alert=False):
    try:
        prefix = "⚠️ <b>SYSTEM ALERT</b>\n" if alert else ""
        await asyncio.to_thread(requests.post,
                                f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage",
                                data={'chat_id': config.TELEGRAM_CHAT_ID, 'text': f"{prefix}{pesan}", 'parse_mode': 'HTML'})
    except Exception as e: print(f"Tele error: {e}")

# ==========================================
# 0. SETUP AWAL
# ==========================================
async def setup_account_settings():
    print("⚙️ Menerapkan Custom Leverage & Margin Mode...")
    await kirim_tele("⚙️ <b>Setup Awal:</b> Mengatur Custom Config per Koin...")
    
    count = 0
    for koin in config.DAFTAR_KOIN:
        symbol = koin['symbol']
        lev = koin.get('leverage', config.DEFAULT_LEVERAGE)
        marg_type = koin.get('margin_type', config.DEFAULT_MARGIN_TYPE)

        try:
            await exchange.set_leverage(lev, symbol)
            try:
                await exchange.set_margin_mode(marg_type, symbol)
            except Exception:
                pass 
            
            print(f"   🔹 {symbol}: Lev {lev}x | {marg_type}")
            count += 1
            if count % 5 == 0: await asyncio.sleep(0.5) 
        except Exception as e:
            logging.error(f"Gagal seting {symbol}: {e}")
            print(f"❌ Gagal seting {symbol}: {e}")
    
    print("✅ Setup Selesai.")
    await kirim_tele("✅ <b>Setup Selesai.</b> Bot siap berjalan.")

async def update_btc_trend():
    global global_btc_trend, last_btc_check
    now = time.time()
    
    if now - last_btc_check < config.BTC_CHECK_INTERVAL and global_btc_trend != "NEUTRAL":
        return global_btc_trend

    try:
        bars = await exchange.fetch_ohlcv(config.BTC_SYMBOL, config.BTC_TIMEFRAME, limit=100)
        if not bars: return "NEUTRAL"

        df = pd.DataFrame(bars, columns=['time','open','high','low','close','volume'])
        ema_btc = df.ta.ema(length=config.BTC_EMA_PERIOD)
        
        current_price = df['close'].iloc[-1]
        current_ema = ema_btc.iloc[-1]

        prev_trend = global_btc_trend
        if current_price > current_ema:
            global_btc_trend = "BULLISH"
        else:
            global_btc_trend = "BEARISH"
        
        last_btc_check = now
        if prev_trend != global_btc_trend:
            print(f"🔄 BTC TREND CHANGE: {prev_trend} -> {global_btc_trend}")
            
        return global_btc_trend
    except Exception as e:
        logging.error(f"Gagal cek BTC trend: {e}")
        return "NEUTRAL"

# ==========================================
# 1. EKSEKUSI (LIMIT & MARKET SUPPORT)
# ==========================================
async def _async_eksekusi_binance(symbol, side, entry_price, sl_price, tp1, coin_config, order_type='market'):
    print(f"🚀 EXECUTING: {symbol} {side} | Type: {order_type} @ {entry_price}")
    try:
        my_leverage = coin_config.get('leverage', config.DEFAULT_LEVERAGE)
        my_margin_usdt = coin_config.get('amount', config.DEFAULT_AMOUNT_USDT)

        # Hitung jumlah koin
        amount_coin = (my_margin_usdt * my_leverage) / entry_price
        amount_final = exchange.amount_to_precision(symbol, amount_coin)
        price_final = exchange.price_to_precision(symbol, entry_price) 

        notional_value = float(amount_final) * entry_price
        if notional_value < config.MIN_ORDER_USDT:
            print(f"⚠️ Order {symbol} terlalu kecil (${notional_value:.2f}). Skip.")
            return False

        # --- 1. PLACE ENTRY ORDER ---
        if order_type == 'limit':
            # Pasang jaring (Limit Order)
            await exchange.create_order(symbol, 'limit', side, amount_final, price_final)
            print(f"⏳ {symbol} Limit Order placed at {price_final}. Waiting for fill...")
            await asyncio.sleep(1) # Delay sesaat

        else:
            # Market Execution (Normal Mode)
            await exchange.create_order(symbol, 'market', side, amount_final)
        
        # --- 2. PASANG SL/TP (SAFE MODE) ---
        # Note: Untuk Limit Order, order SL/TP ini mungkin gagal jika entry belum filled.
        # Tapi kita tetap coba pasang untuk safety jika market bergerak cepat.
        
        sl_side = 'sell' if side == 'buy' else 'buy'

        for attempt in range(1, config.ORDER_SLTP_RETRIES + 1):
            try:
                # Trigger by MARK PRICE untuk anti-scam wick
                params_sl = {
                    'stopPrice': exchange.price_to_precision(symbol, sl_price),
                    'workingType': 'MARK_PRICE',
                    'reduceOnly': True 
                }
                
                params_tp = {
                    'stopPrice': exchange.price_to_precision(symbol, tp1),
                    'reduceOnly': True
                }

                await exchange.create_order(symbol, 'STOP_MARKET', sl_side, amount_final, params=params_sl)
                await exchange.create_order(symbol, 'TAKE_PROFIT_MARKET', sl_side, amount_final, params=params_tp)
                
                print(f"✅ {symbol} SL/TP Installed.")
                return True
            except Exception as e:
                # Error ini wajar jika order Limit belum ke-fill
                if "Order would trigger immediately" in str(e): 
                     logging.warning(f"SL/TP terlalu dekat: {e}")
                elif "Order does not exist" in str(e) or "Margin is insufficient" in str(e):
                     # Ini biasanya kena kalau Limit belum ke-fill, wajar.
                     logging.warning(f"Pending SL/TP {symbol} (Belum Fill): {e}")
                else:
                     logging.warning(f"Retry SL/TP {symbol}: {e}")
                await asyncio.sleep(config.ORDER_SLTP_RETRY_DELAY)

        return True
    except Exception as e:
        logging.error(f"Error Eksekusi {symbol}: {e}")
        return False

# ==========================================
# 2. ANALISA (LIQUIDITY HUNT SUPPORT)
# ==========================================
def calculate_trade_parameters(signal, df):
    current = df.iloc[-1]
    atr = df.iloc[-2]['ATR']
    current_price = current['close']
    
    # 1. Hitung Logika Retail (Original)
    retail_sl_dist = atr * config.ATR_MULTIPLIER_SL
    retail_tp_dist = atr * config.ATR_MULTIPLIER_TP1
    
    if signal == "LONG":
        retail_sl = current_price - retail_sl_dist
        retail_tp = current_price + retail_tp_dist
        side_api = 'buy'
    else:
        retail_sl = current_price + retail_sl_dist
        retail_tp = current_price - retail_tp_dist
        side_api = 'sell'

    # 2. Cek Mode Liquidity Hunt (Config)
    if getattr(config, 'USE_LIQUIDITY_HUNT', False):
        # Entry di SL Retail (Diskon)
        new_entry = retail_sl 
        # TP di Harga sekarang (High Probability)
        final_tp = retail_tp # Atau current_price jika mau cepat keluar
        
        # Safety SL baru
        safety_sl_dist = atr * getattr(config, 'TRAP_SAFETY_SL', 1.0)
        
        if signal == "LONG":
            final_sl = new_entry - safety_sl_dist
        else:
            final_sl = new_entry + safety_sl_dist
            
        return {"entry_price": new_entry, "sl": final_sl, "tp1": final_tp, "side_api": side_api, "type": "limit"}

    else:
        # Normal Market Mode
        return {"entry_price": current_price, "sl": retail_sl, "tp1": retail_tp, "side_api": side_api, "type": "market"}

async def analisa_market(coin_config, btc_trend_status):
    symbol = coin_config['symbol']
    
    now = time.time()
    # Filter Cooldown
    if symbol in last_entry_time and (now - last_entry_time[symbol] < config.COOLDOWN_PER_SYMBOL_SECONDS): return

    # --- [UPDATE LOGIKA DISINI] ---
    # Cek Posisi Aktif & Pending Order SPESIFIK untuk koin ini saja
    try:
        # 1. Cek apakah sudah punya posisi aktif di koin ini?
        # (Kita cek cache global positions_cache yang diupdate di main)
        base_symbol = symbol.split('/')[0]
        if base_symbol in positions_cache:
            return

        # 2. Cek apakah ada PENDING ORDER (Limit) di koin ini?
        # Kita tanya langsung ke Binance KHUSUS untuk symbol ini (Ringan & Akurat)
        open_orders = await exchange.fetch_open_orders(symbol)
        
        if len(open_orders) > 0:
            # print(f"✋ Skip {symbol}: Masih ada {len(open_orders)} antrian pending.")
            return

    except Exception as e:
        print(f"⚠️ Error cek order {symbol}: {e}")
        return # Skip analisa jika gagal cek order biar gak double entry

    allowed_signal = "BOTH"
    if symbol != config.BTC_SYMBOL:
        if btc_trend_status == "BULLISH": allowed_signal = "LONG_ONLY"
        elif btc_trend_status == "BEARISH": allowed_signal = "SHORT_ONLY"

    try:
        # ... (SISA KODE KE BAWAH SAMA PERSIS SEPERTI SEBELUMNYA) ...
        # Ambil data OHLCV
        bars = await exchange.fetch_ohlcv(symbol, config.TIMEFRAME_EXEC, limit=config.LIMIT_EXEC)
        # ... dst ...
        bars_h1 = await exchange.fetch_ohlcv(symbol, config.TIMEFRAME_TREND, limit=config.LIMIT_TREND)
        if not bars or not bars_h1: return

        df = pd.DataFrame(bars, columns=['time','open','high','low','close','volume'])
        
        # --- INDICATORS ---
        df['EMA_FAST'] = df.ta.ema(length=config.EMA_FAST)
        df['EMA_SLOW'] = df.ta.ema(length=config.EMA_SLOW)
        df['EMA_MAJOR'] = df.ta.ema(length=config.EMA_TREND_MAJOR) 
        df['ATR'] = df.ta.atr(length=config.ATR_PERIOD)
        df['ADX'] = df.ta.adx(length=config.ADX_PERIOD)[f"ADX_{config.ADX_PERIOD}"]
        df['RSI'] = df.ta.rsi(length=14)
        df['VOL_MA'] = df['volume'].rolling(window=config.VOL_MA_PERIOD).mean()
        bb = df.ta.bbands(length=config.BB_LENGTH, std=config.BB_STD)
        df['BBL'] = bb[f'BBL_{config.BB_LENGTH}_{config.BB_STD}']
        df['BBU'] = bb[f'BBU_{config.BB_LENGTH}_{config.BB_STD}']
        stoch = df.ta.stochrsi(length=config.STOCHRSI_LEN, rsi_length=config.STOCHRSI_LEN, k=config.STOCHRSI_K, d=config.STOCHRSI_D)
        df['STOCH_K'] = stoch.iloc[:, 0]
        df['STOCH_D'] = stoch.iloc[:, 1]

        # --- LOGIC ---
        confirm = df.iloc[-2]
        adx_val = confirm['ADX']
        current_price = confirm['close']
        current_rsi = confirm['RSI']
        
        signal = None
        strategy_type = "NONE"

        # TRENDING
        if adx_val > config.ADX_LIMIT_TREND:
            if (allowed_signal in ["LONG_ONLY", "BOTH"]):
                is_perfect_uptrend = (confirm['close'] > confirm['EMA_FAST']) and \
                                     (confirm['EMA_FAST'] > confirm['EMA_SLOW']) and \
                                     (confirm['EMA_SLOW'] > confirm['EMA_MAJOR'])
                if is_perfect_uptrend and (current_price < confirm['BBU']) and (current_rsi < 70):
                    signal = "LONG"
                    strategy_type = "TREND_STRONG"
            
            elif (allowed_signal in ["SHORT_ONLY", "BOTH"]):
                is_perfect_downtrend = (confirm['close'] < confirm['EMA_FAST']) and \
                                       (confirm['EMA_FAST'] < confirm['EMA_SLOW']) and \
                                       (confirm['EMA_SLOW'] < confirm['EMA_MAJOR'])
                if is_perfect_downtrend and (current_price > confirm['BBL']) and (current_rsi > 30):
                    signal = "SHORT"
                    strategy_type = "TREND_STRONG"

        # SIDEWAYS
        else:
            if (allowed_signal in ["LONG_ONLY", "BOTH"]):
                is_at_bottom = current_price <= (confirm['BBL'] * 1.002)
                is_stoch_buy = (confirm['STOCH_K'] > confirm['STOCH_D']) and (confirm['STOCH_K'] < 30)
                if is_at_bottom and is_stoch_buy:
                    signal = "LONG"
                    strategy_type = "SCALP_REVERSAL"

            elif (allowed_signal in ["SHORT_ONLY", "BOTH"]):
                is_at_top = current_price >= (confirm['BBU'] * 0.998)
                is_stoch_sell = (confirm['STOCH_K'] < confirm['STOCH_D']) and (confirm['STOCH_K'] > 70)
                if is_at_top and is_stoch_sell:
                    signal = "SHORT"
                    strategy_type = "SCALP_REVERSAL"

        # --- EXECUTE ---
        if signal:
            print(f"🎯 Sinyal {symbol} {signal} | Type: {strategy_type} | ADX: {adx_val:.2f} | RSI: {current_rsi:.2f}")

            params = calculate_trade_parameters(signal, df)
            
            berhasil = await _async_eksekusi_binance(
                symbol, 
                params['side_api'], 
                params['entry_price'], 
                params['sl'], 
                params['tp1'], 
                coin_config,
                order_type=params.get('type', 'market')
            )
            
            if berhasil:
                lev = coin_config.get('leverage', config.DEFAULT_LEVERAGE)
                msg = f"{'🟢' if signal=='LONG' else '🔴'} <b>{symbol} {signal}</b>\nMode: {strategy_type}\nType: {params.get('type','MARKET')}\nEntry: {params['entry_price']}\nSL: {params['sl']:.4f}"
                await kirim_tele(msg)
                last_entry_time[symbol] = now
                
    except Exception as e:
        logging.error(f"Analisa error {symbol}: {e}")

# ==========================================
# 3. LOOP UTAMA
# ==========================================
async def main():
    global exchange, positions_cache, global_btc_trend
    
    # Init Exchange
    params = {'apiKey': config.API_KEY_DEMO if config.PAKAI_DEMO else config.API_KEY_LIVE,
              'secret': config.SECRET_KEY_DEMO if config.PAKAI_DEMO else config.SECRET_KEY_LIVE,
              'enableRateLimit': True, 'options': {'defaultType': 'future'}}
    exchange = ccxt.binance(params)
    if config.PAKAI_DEMO: exchange.enable_demo_trading(True)

    await kirim_tele("🚀 <b>BOT STARTED</b>\nFitur: Liquidity Hunt Fixed (Per-Symbol Check)")
    
    await setup_account_settings()

    while True:
        try:
            # 1. Update Cache Posisi (Barang yg sudah dibeli)
            pos = await exchange.fetch_positions()
            positions_cache = {p['symbol'].split(':')[0] for p in pos if float(p.get('contracts', 0)) > 0}
            
            # [HAPUS BAGIAN FETCH OPEN ORDERS GLOBAL DISINI KARENA ERROR]
            # Kita sudah memindahkannya ke dalam analisa_market per koin.

            # 2. Update BTC Trend
            btc_trend = await update_btc_trend()
            
            # 3. Jalankan Analisa
            tasks = [analisa_market(k, btc_trend) for k in config.DAFTAR_KOIN]
            await asyncio.gather(*tasks)
            
            print(f"⏳ Loop selesai. Active Pos: {len(positions_cache)}")
            await asyncio.sleep(10)

        except Exception as e:
            print(f"Loop error: {e}")
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
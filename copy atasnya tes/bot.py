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
open_orders_cache = set()
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
# 1. EKSEKUSI (LIMIT FIX)
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
            print(f"⏳ {symbol} Limit Order placed at {price_final}. Menunggu fill...")
            
            # [FIX] JANGAN PASANG SL/TP DISINI UNTUK LIMIT ORDER
            # Karena posisi belum ada, SL/TP reduceOnly akan ditolak/cancel otomatis.
            # SL/TP akan ditangani oleh fungsi 'monitor_positions_safety' nanti.
            return True

        else:
            # Market Execution (Normal Mode)
            await exchange.create_order(symbol, 'market', side, amount_final)
        
        # --- 2. PASANG SL/TP (KHUSUS MARKET ORDER) ---
        # Kalau market order, posisi langsung kebentuk, jadi aman pasang SL/TP reduceOnly sekarang.
        
        sl_side = 'sell' if side == 'buy' else 'buy'

        for attempt in range(1, config.ORDER_SLTP_RETRIES + 1):
            try:
                params_sl = {'stopPrice': exchange.price_to_precision(symbol, sl_price), 'workingType': 'MARK_PRICE', 'reduceOnly': True}
                params_tp = {'stopPrice': exchange.price_to_precision(symbol, tp1), 'reduceOnly': True}

                await exchange.create_order(symbol, 'STOP_MARKET', sl_side, amount_final, params=params_sl)
                await exchange.create_order(symbol, 'TAKE_PROFIT_MARKET', sl_side, amount_final, params=params_tp)
                
                print(f"✅ {symbol} SL/TP Installed.")
                return True
            except Exception as e:
                 logging.warning(f"Retry SL/TP {symbol}: {e}")
                
            await asyncio.sleep(config.ORDER_SLTP_RETRY_DELAY)

        return True
    except Exception as e:
        logging.error(f"Error Eksekusi {symbol}: {e}")
        return False

# ==========================================
# 2. MONITOR & SAFETY (AUTO SL/TP) - ANTI SPAM & CLEANER
# ==========================================
async def monitor_positions_safety():
    """
    Fungsi Satpam: 
    1. Membersihkan order jika numpuk (Anti-Spam).
    2. Memasang SL/TP jika kosong.
    """
    try:
        # Ambil posisi aktif
        pos_raw = await exchange.fetch_positions()
        active_positions = [p for p in pos_raw if float(p.get('contracts', 0)) > 0]
        
        for pos in active_positions:
            symbol = pos['symbol']
            amount = float(pos['contracts'])
            entry_price = float(pos['entryPrice'])
            
            # Gunakan simbol dari posisi langsung agar akurat
            # Contoh: OM/USDT:USDT -> ambil simbol ini untuk fetch order
            
            try:
                open_orders = await exchange.fetch_open_orders(symbol)
            except Exception:
                continue

            # --- 1. LOGIKA ANTI-SPAM (PEMBERSIHAN) ---
            # Jika order antrian lebih dari 2 (artinya ada duplikat SL/TP), HAPUS SEMUA dulu.
            # Nanti di loop berikutnya (10 detik lagi) dia akan pasang ulang 1 pasang yang rapi.
            if len(open_orders) > 2:
                print(f"🧹 CLEANUP: Terdeteksi {len(open_orders)} order numpuk di {symbol}. Resetting...")
                try:
                    await exchange.cancel_all_orders(symbol)
                    await kirim_tele(f"🧹 <b>Auto-Cleanup:</b> Menghapus antrian spam di {symbol}")
                except Exception as e:
                    print(f"Gagal cancel {symbol}: {e}")
                continue # Skip loop ini, tunggu bersih dulu

            # --- 2. LOGIKA DETEKSI YANG LEBIH PINTAR ---
            # Jangan percaya nama "Type". Cek behavior-nya (ReduceOnly & Harga).
            has_sl = False
            has_tp = False

            is_long_pos = float(pos['notional']) > 0

            for o in open_orders:
                # Cek apakah ini order pengaman (ReduceOnly)
                # Note: Kadang reduceOnly ada di 'info' tergantung versi CCXT
                is_reduce = o.get('reduceOnly', False) or (o.get('info', {}).get('reduceOnly') == 'true')
                
                if is_reduce:
                    stop_price = float(o.get('stopPrice', 0) or o.get('info', {}).get('stopPrice', 0) or o.get('price', 0))
                    
                    if stop_price > 0:
                        if is_long_pos:
                            if stop_price < entry_price: has_sl = True # Harga di bawah entry = SL
                            if stop_price > entry_price: has_tp = True # Harga di atas entry = TP
                        else: # Short
                            if stop_price > entry_price: has_sl = True # Harga di atas entry = SL
                            if stop_price < entry_price: has_tp = True # Harga di bawah entry = TP

            # --- 3. PASANG JIKA KOSONG ---
            if not has_sl or not has_tp:
                # Debug print untuk melihat kenapa dia gagal mendeteksi (jika masih terjadi)
                # print(f"DEBUG {symbol}: Orders={len(open_orders)} | SL={has_sl} | TP={has_tp}")

                # Hitung ATR
                bars = await exchange.fetch_ohlcv(symbol, config.TIMEFRAME_EXEC, limit=20)
                df = pd.DataFrame(bars, columns=['time','open','high','low','close','volume'])
                atr = df.ta.atr(length=config.ATR_PERIOD).iloc[-1]
                
                sl_dist = atr * config.ATR_MULTIPLIER_SL
                tp_dist = atr * config.ATR_MULTIPLIER_TP1
                
                if is_long_pos:
                    sl_price = entry_price - sl_dist
                    tp_price = entry_price + tp_dist
                    sl_side = 'sell'
                else:
                    sl_price = entry_price + sl_dist
                    tp_price = entry_price - tp_dist
                    sl_side = 'buy'
                
                amount_final = exchange.amount_to_precision(symbol, amount)

                try:
                    tasks = []
                    # Hanya pasang yang hilang
                    if not has_sl:
                        params_sl = {'stopPrice': exchange.price_to_precision(symbol, sl_price), 'workingType': 'MARK_PRICE', 'reduceOnly': True}
                        tasks.append(exchange.create_order(symbol, 'STOP_MARKET', sl_side, amount_final, params=params_sl))
                        print(f"   ➕ Memasang SL Baru {symbol}")
                        
                    if not has_tp:
                        params_tp = {'stopPrice': exchange.price_to_precision(symbol, tp_price), 'reduceOnly': True}
                        tasks.append(exchange.create_order(symbol, 'TAKE_PROFIT_MARKET', sl_side, amount_final, params=params_tp))
                        print(f"   ➕ Memasang TP Baru {symbol}")
                    
                    if tasks:
                        await asyncio.gather(*tasks)
                        await kirim_tele(f"🛡️ <b>Safety Fixed:</b> SL/TP dipasang untuk {symbol}")

                except Exception as e:
                    print(f"   ❌ Gagal pasang safety {symbol}: {e}")

    except Exception as e:
        print(f"Error Safety Monitor: {e}")

# ==========================================
# 3. ANALISA MARKET
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

    # 2. Cek Mode Liquidity Hunt
    if getattr(config, 'USE_LIQUIDITY_HUNT', False):
        new_entry = retail_sl 
        final_tp = retail_tp 
        safety_sl_dist = atr * getattr(config, 'TRAP_SAFETY_SL', 1.0)
        
        if signal == "LONG":
            final_sl = new_entry - safety_sl_dist
        else:
            final_sl = new_entry + safety_sl_dist
            
        return {"entry_price": new_entry, "sl": final_sl, "tp1": final_tp, "side_api": side_api, "type": "limit"}

    else:
        return {"entry_price": current_price, "sl": retail_sl, "tp1": retail_tp, "side_api": side_api, "type": "market"}

async def analisa_market(coin_config, btc_trend_status):
    symbol = coin_config['symbol']
    now = time.time()
    
    # Filter Cooldown
    if symbol in last_entry_time and (now - last_entry_time[symbol] < config.COOLDOWN_PER_SYMBOL_SECONDS): return

    try:
        # Cek Posisi Aktif
        # [FIX] Gunakan startswith agar AVAX/USDT cocok dengan AVAX/USDT:USDT
        has_position = False
        for pos_sym in positions_cache:
            if pos_sym == symbol or pos_sym.startswith(symbol.split('/')[0]):
                has_position = True
                break
        
        if has_position: return

        # Cek Pending Order (Limit)
        # [FIX] Kita fetch order, jika ada order LIMIT yg 'open', kita skip analisa (biar gak numpuk)
        open_orders = await exchange.fetch_open_orders(symbol)
        limit_orders = [o for o in open_orders if o['type'] == 'limit' and o['status'] == 'open']
        
        if len(limit_orders) > 0:
            # OPTIONAL: Jika limit order numpuk lebih dari 1 (Bug Gambar 1), kita bersihkan sisakan 1 atau cancel semua
            if len(limit_orders) > 1:
                print(f"⚠️ {symbol} kelebihan antrian ({len(limit_orders)} orders). Mereset...")
                await exchange.cancel_all_orders(symbol)
            return # Skip analisa karena sudah ada antrian

    except Exception as e:
        # print(f"Error cek pending {symbol}: {e}") 
        return 

    # ... (LANJUTKAN KE BAWAH SEPERTI KODE LAMA: allowed_signal = "BOTH" dst...)
    allowed_signal = "BOTH"
    # ... dst ...
    if symbol != config.BTC_SYMBOL:
        if btc_trend_status == "BULLISH": allowed_signal = "LONG_ONLY"
        elif btc_trend_status == "BEARISH": allowed_signal = "SHORT_ONLY"

    try:
        bars = await exchange.fetch_ohlcv(symbol, config.TIMEFRAME_EXEC, limit=config.LIMIT_EXEC)
        bars_h1 = await exchange.fetch_ohlcv(symbol, config.TIMEFRAME_TREND, limit=config.LIMIT_TREND)
        if not bars or not bars_h1: return

        df = pd.DataFrame(bars, columns=['time','open','high','low','close','volume'])
        
        # INDICATORS
        df['EMA_FAST'] = df.ta.ema(length=config.EMA_FAST)
        df['EMA_SLOW'] = df.ta.ema(length=config.EMA_SLOW)
        df['EMA_MAJOR'] = df.ta.ema(length=config.EMA_TREND_MAJOR) 
        df['ATR'] = df.ta.atr(length=config.ATR_PERIOD)
        df['ADX'] = df.ta.adx(length=config.ADX_PERIOD)[f"ADX_{config.ADX_PERIOD}"]
        df['RSI'] = df.ta.rsi(length=14)
        bb = df.ta.bbands(length=config.BB_LENGTH, std=config.BB_STD)
        df['BBL'] = bb[f'BBL_{config.BB_LENGTH}_{config.BB_STD}']
        df['BBU'] = bb[f'BBU_{config.BB_LENGTH}_{config.BB_STD}']
        stoch = df.ta.stochrsi(length=config.STOCHRSI_LEN, rsi_length=config.STOCHRSI_LEN, k=config.STOCHRSI_K, d=config.STOCHRSI_D)
        df['STOCH_K'] = stoch.iloc[:, 0]
        df['STOCH_D'] = stoch.iloc[:, 1]

        # LOGIC
        confirm = df.iloc[-2]
        adx_val = confirm['ADX']
        current_price = confirm['close']
        current_rsi = confirm['RSI']
        
        signal = None
        strategy_type = "NONE"

        if adx_val > config.ADX_LIMIT_TREND:
            if (allowed_signal in ["LONG_ONLY", "BOTH"]):
                is_perfect_uptrend = (confirm['close'] > confirm['EMA_FAST']) and (confirm['EMA_FAST'] > confirm['EMA_SLOW']) and (confirm['EMA_SLOW'] > confirm['EMA_MAJOR'])
                if is_perfect_uptrend and (current_price < confirm['BBU']) and (current_rsi < 70):
                    signal = "LONG"; strategy_type = "TREND_STRONG"
            elif (allowed_signal in ["SHORT_ONLY", "BOTH"]):
                is_perfect_downtrend = (confirm['close'] < confirm['EMA_FAST']) and (confirm['EMA_FAST'] < confirm['EMA_SLOW']) and (confirm['EMA_SLOW'] < confirm['EMA_MAJOR'])
                if is_perfect_downtrend and (current_price > confirm['BBL']) and (current_rsi > 30):
                    signal = "SHORT"; strategy_type = "TREND_STRONG"
        else:
            if (allowed_signal in ["LONG_ONLY", "BOTH"]):
                is_at_bottom = current_price <= (confirm['BBL'] * 1.002)
                is_stoch_buy = (confirm['STOCH_K'] > confirm['STOCH_D']) and (confirm['STOCH_K'] < 30)
                if is_at_bottom and is_stoch_buy: signal = "LONG"; strategy_type = "SCALP_REVERSAL"
            elif (allowed_signal in ["SHORT_ONLY", "BOTH"]):
                is_at_top = current_price >= (confirm['BBU'] * 0.998)
                is_stoch_sell = (confirm['STOCH_K'] < confirm['STOCH_D']) and (confirm['STOCH_K'] > 70)
                if is_at_top and is_stoch_sell: signal = "SHORT"; strategy_type = "SCALP_REVERSAL"

        if signal:
            print(f"🎯 Sinyal {symbol} {signal} | Type: {strategy_type}")
            params = calculate_trade_parameters(signal, df)
            berhasil = await _async_eksekusi_binance(symbol, params['side_api'], params['entry_price'], params['sl'], params['tp1'], coin_config, order_type=params.get('type', 'market'))
            
            if berhasil:
                msg = f"{'🟢' if signal=='LONG' else '🔴'} <b>{symbol} {signal}</b>\nMode: {strategy_type}\nType: {params.get('type','MARKET')}\nEntry: {params['entry_price']}"
                await kirim_tele(msg)
                last_entry_time[symbol] = now
                
    except Exception as e:
        logging.error(f"Analisa error {symbol}: {e}")

# ==========================================
# 4. LOOP UTAMA
# ==========================================
async def main():
    global exchange, positions_cache, global_btc_trend
    
    # Init Exchange
    params = {'apiKey': config.API_KEY_DEMO if config.PAKAI_DEMO else config.API_KEY_LIVE,
              'secret': config.SECRET_KEY_DEMO if config.PAKAI_DEMO else config.SECRET_KEY_LIVE,
              'enableRateLimit': True, 'options': {'defaultType': 'future'}}
    exchange = ccxt.binance(params)
    if config.PAKAI_DEMO: exchange.enable_demo_trading(True)

    await kirim_tele("🚀 <b>BOT STARTED</b>\nFitur: Auto-Safety SL/TP for Limit Orders")
    await setup_account_settings()

    while True:
        try:
            # 1. Update Cache Posisi
            pos = await exchange.fetch_positions()
            positions_cache = {p['symbol'].split(':')[0] for p in pos if float(p.get('contracts', 0)) > 0}
            
            # 2. [NEW] JALANKAN SATPAM SL/TP
            # Ini akan mengecek jika Limit Order sudah ke-isi, lalu pasang SL/TP otomatis
            await monitor_positions_safety()

            # 3. Update BTC & Analisa
            btc_trend = await update_btc_trend()
            tasks = [analisa_market(k, btc_trend) for k in config.DAFTAR_KOIN]
            await asyncio.gather(*tasks)
            
            print(f"⏳ Loop selesai. Active Pos: {len(positions_cache)}")
            await asyncio.sleep(10)

        except Exception as e:
            print(f"Loop error: {e}")
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
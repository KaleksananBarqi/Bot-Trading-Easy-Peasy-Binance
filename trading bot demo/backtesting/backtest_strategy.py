from backtesting import Backtest, Strategy
import pandas as pd
import pandas_ta as ta

# --- DEFINISI STRATEGI SESUAI MAIN BOT ---
class StrategiAjiFull(Strategy):
    # Parameter (Bisa diubah kalau mau eksperimen)
    n_ema_fast = 13         # EMA 13 (15m)
    n_ema_slow = 21         # EMA 21 (15m)
    n_ema_trend = 800       # EMA 800 (15m) ≈ EMA 200 (H1) -> Trik Matematika
    
    n_rsi = 14
    n_atr = 14
    sl_ratio = 2.0          # Stop Loss 2x ATR
    tp_ratio = 3.0          # Take Profit 3x ATR

    def init(self):
        # 1. INDIKATOR UTAMA
        close_series = pd.Series(self.data.Close)
        
        # EMA Cross (15m)
        self.ema13 = self.I(ta.ema, close_series, length=self.n_ema_fast)
        self.ema21 = self.I(ta.ema, close_series, length=self.n_ema_slow)
        
        # EMA Trend (H1 Proxy)
        self.ema_trend = self.I(ta.ema, close_series, length=self.n_ema_trend)
        
        # RSI
        self.rsi = self.I(ta.rsi, close_series, length=self.n_rsi)
        
        # ATR
        self.atr = self.I(ta.atr, pd.Series(self.data.High), pd.Series(self.data.Low), close_series, length=self.n_atr)

        # 2. INDIKATOR TAMBAHAN (MACD & VOLUME)
        # MACD (Line, Histogram, Signal)
        macd = ta.macd(close_series, fast=12, slow=26, signal=9)
        # Kita butuh MACD Line (kolom ke-0) dan Signal Line (kolom ke-2)
        self.macd_line = self.I(lambda x: macd.iloc[:, 0], close_series) # Garis Biru
        self.macd_signal = self.I(lambda x: macd.iloc[:, 2], close_series) # Garis Oranye
        
        # Volume MA (Rata-rata 20 candle)
        self.vol_ma = self.I(ta.sma, pd.Series(self.data.Volume), length=20)

        # 3. LIQUIDITY ZONES (SWEEP)
        # Low terendah 20 candle lalu (digeser 1 biar gak intip masa depan)
        self.low_liq = self.I(lambda x: pd.Series(x).rolling(20).min().shift(1), self.data.Low)
        self.high_liq = self.I(lambda x: pd.Series(x).rolling(20).max().shift(1), self.data.High)

    def next(self):
        # Ambil Data Candle Terakhir (-1) dan Sebelumnya (-2)
        # Kenapa -2? Karena sweep terjadi di candle yang BARU SAJA close (confirmed)
        
        # Harga
        close_now = self.data.Close[-1]
        
        # Candle Konfirmasi (Sweep terjadi di sini)
        prev_low = self.data.Low[-2]
        prev_high = self.data.High[-2]
        prev_close = self.data.Close[-2]
        prev_vol = self.data.Volume[-2]
        
        # Support/Resist
        support = self.low_liq[-1]
        resist = self.high_liq[-1]

        # Indikator Sekarang
        ema13 = self.ema13[-1]
        ema21 = self.ema21[-1]
        ema_h1 = self.ema_trend[-1]
        
        macd_line = self.macd_line[-1]
        macd_sig = self.macd_signal[-1]
        
        rsi = self.rsi[-1]
        vol_avg = self.vol_ma[-1]

        # --- LOGIKA ENTRY (PERSIS MAIN BOT) ---

        # 1. FILTER TREN BESAR (H1)
        is_h1_bull = close_now > ema_h1
        is_h1_bear = close_now < ema_h1

        # 2. FILTER VOLUME (Ledakan Volume saat Sweep)
        is_vol_valid = prev_vol > (1.2 * vol_avg)

        # --- SKENARIO BUY / LONG ---
        if is_h1_bull:
            # A. Sweep Support (Low nusuk, Close balik naik)
            is_sweep = (prev_low < support) and (prev_close > support)
            
            # B. EMA Cross/Stack (13 di atas 21)
            is_momentum = ema13 > ema21
            
            # C. MACD Bullish (Biru > Oranye)
            is_macd = macd_line > macd_sig
            
            # D. RSI Murah
            is_rsi = rsi < 60
            
            # GABUNGAN SEMUA SYARAT
            if is_sweep and is_momentum and is_macd and is_rsi and is_vol_valid:
                # Hitung SL/TP Dinamis
                sl_dist = self.sl_ratio * self.atr[-1]
                tp_dist = self.tp_ratio * self.atr[-1]
                
                if not self.position: # Cuma entry kalau belum punya posisi
                    self.buy(sl=close_now - sl_dist, tp=close_now + tp_dist)

        # --- SKENARIO SELL / SHORT ---
        elif is_h1_bear:
            # A. Sweep Resist (High nusuk, Close balik turun)
            is_sweep = (prev_high > resist) and (prev_close < resist)
            
            # B. EMA Cross/Stack (13 di bawah 21)
            is_momentum = ema13 < ema21
            
            # C. MACD Bearish
            is_macd = macd_line < macd_sig
            
            # D. RSI Mahal
            is_rsi = rsi > 40
            
            if is_sweep and is_momentum and is_macd and is_rsi and is_vol_valid:
                sl_dist = self.sl_ratio * self.atr[-1]
                tp_dist = self.tp_ratio * self.atr[-1]
                
                if not self.position:
                    self.sell(sl=close_now + sl_dist, tp=close_now - tp_dist)

# --- JALANKAN ---
if __name__ == "__main__":
    # Pastikan file CSV sudah ada (hasil dari ambil_data_backtest.py)
    NAMA_FILE_DATA = "C:\\Projek\\Bot Trading\\trading bot demo\\backtesting\\data_BTCUSDT_15m_1tahun.csv"
    try:
        df = pd.read_csv(NAMA_FILE_DATA)
        df.columns = [col.capitalize() for col in df.columns]
        df = df.set_index('Time')
        df.index = pd.to_datetime(df.index)

        # Modal 1000, Komisi Binance Futures Taker 0.04%
        bt = Backtest(df, StrategiAjiFull, cash=1000, commission=.0004, exclusive_orders=True)
        
        stats = bt.run()
        print(stats)
        bt.plot()
        
    except FileNotFoundError:
        print(f"❌ File {NAMA_FILE_DATA} tidak ditemukan!")
        print("Jalankan script 'ambil_data_backtest.py' dulu ya.")
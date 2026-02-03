from typing import Dict, Any
import config

def calculate_trade_scenarios(
    price: float, 
    atr: float, 
    side: str, 
    precision: int = 4
) -> Dict[str, Any]:
    """
    Menghitung skenario trade untuk Market (Aggressive) vs Liquidity Hunt (Passive).
    
    Args:
        price (float): Harga saat ini (Current Price).
        atr (float): Nilai ATR saat ini.
        side (str): 'BUY' atau 'SELL'.
        precision (int): Desimal untuk pembulatan harga.
        
    Returns:
        dict: {
            "market": {entry, sl, tp, rr},
            "liquidity_hunt": {entry, sl, tp, rr}
        }
    """
    scenarios = {}
    
    # --- 1. MARKET SCENARIO (Aggressive) ---
    # Entry: Current Price
    # SL: Price - (ATR * SL_Multiplier)
    # TP: Price + (ATR * TP_Multiplier)
    
    m_entry = price
    m_dist_sl = atr * config.ATR_MULTIPLIER_SL
    m_dist_tp = atr * config.ATR_MULTIPLIER_TP1
    
    if side.upper() == 'BUY':
        m_sl = m_entry - m_dist_sl
        m_tp = m_entry + m_dist_tp
    else: # SELL
        m_sl = m_entry + m_dist_sl
        m_tp = m_entry - m_dist_tp
        
    m_rr = m_dist_tp / m_dist_sl if m_dist_sl > 0 else 0
    
    scenarios['market'] = {
        "entry": round(m_entry, precision),
        "sl": round(m_sl, precision),
        "tp": round(m_tp, precision),
        "rr": round(m_rr, 2)
    }
    
    # --- 2. LIQUIDITY HUNT SCENARIO (Passive) ---
    # Entry: Limit Order at Market SL level (Sweeping the stops)
    # SL: Baru (New Entry - Buffer)
    # TP: Balik ke arah tren (Bisa pakai TP Market tadi atau dihitung ulang)
    
    # Logic: Kita pasang antrian jaring di tempat orang lain kena SL.
    # Entry Hunt = SL Market (kurang lebih)
    h_dist_entry_offset = atr * config.ATR_MULTIPLIER_SL # Jarak dari harga skrg ke "SL Orang"
    
    # New Safety for Hunt (Buffer setelah kena sweep)
    # config.TRAP_SAFETY_SL biasanya lebih kecil/ketat karena sudah dapat harga pucuk
    h_dist_sl_safety = atr * config.TRAP_SAFETY_SL 
    h_dist_tp_reward = atr * config.ATR_MULTIPLIER_TP1 # Kita samakan reward distance-nya
    
    if side.upper() == 'BUY':
        # Kita mau BUY di bawah (di harga SL Market Buy orang lain)
        h_entry = price - h_dist_entry_offset 
        h_sl = h_entry - h_dist_sl_safety
        h_tp = h_entry + h_dist_tp_reward
    else:
        # Kita mau SELL di atas (di harga SL Market Sell orang lain)
        h_entry = price + h_dist_entry_offset
        h_sl = h_entry + h_dist_sl_safety
        h_tp = h_entry - h_dist_tp_reward
        
    h_rr = h_dist_tp_reward / h_dist_sl_safety if h_dist_sl_safety > 0 else 0
    
    scenarios['liquidity_hunt'] = {
        "entry": round(h_entry, precision),
        "sl": round(h_sl, precision),
        "tp": round(h_tp, precision),
        "rr": round(h_rr, 2)
    }
    
    return scenarios


def calculate_dual_scenarios(price: float, atr: float, precision: int = 4) -> Dict[str, Any]:
    """
    Menghitung skenario trade untuk KEDUA arah (Long & Short) secara bersamaan.
    Digunakan untuk membuat AI Prompt yang netral (tidak bias ke satu arah).
    
    Args:
        price (float): Harga saat ini.
        atr (float): Nilai ATR saat ini.
        precision (int): Desimal untuk pembulatan harga.
        
    Returns:
        dict: {
            "long": {"market": {...}, "liquidity_hunt": {...}},
            "short": {"market": {...}, "liquidity_hunt": {...}}
        }
    """
    return {
        "long": calculate_trade_scenarios(price, atr, 'BUY', precision),
        "short": calculate_trade_scenarios(price, atr, 'SELL', precision)
    }


def calculate_profit_loss_estimation(
    entry_price: float,
    tp_price: float,
    sl_price: float,
    side: str,
    amount_usdt: float,
    leverage: int
) -> Dict[str, float]:
    """
    Menghitung estimasi profit dan loss dalam USDT dan persentase ROI.
    
    Args:
        entry_price (float): Harga entry.
        tp_price (float): Harga Take Profit.
        sl_price (float): Harga Stop Loss.
        side (str): 'buy' atau 'sell'.
        amount_usdt (float): Margin yang digunakan (USDT).
        leverage (int): Leverage yang dipakai.
        
    Returns:
        dict: {
            "profit_usdt": float,     # Estimasi profit jika TP tercapai
            "loss_usdt": float,       # Estimasi loss jika SL tercapai
            "profit_percent": float,  # ROI jika profit (terhadap margin)
            "loss_percent": float     # ROI jika loss (terhadap margin)
        }
    """
    if entry_price <= 0 or amount_usdt <= 0 or leverage <= 0:
        return {
            "profit_usdt": 0.0,
            "loss_usdt": 0.0,
            "profit_percent": 0.0,
            "loss_percent": 0.0
        }
    
    # Hitung position size dan quantity
    position_size_usdt = amount_usdt * leverage
    qty = position_size_usdt / entry_price
    
    # Hitung jarak ke TP dan SL
    if side.lower() == 'buy':
        # Long position: profit jika harga naik, loss jika turun
        profit_distance = tp_price - entry_price
        loss_distance = entry_price - sl_price
    else:
        # Short position: profit jika harga turun, loss jika naik
        profit_distance = entry_price - tp_price
        loss_distance = sl_price - entry_price
    
    # Hitung profit/loss dalam USDT
    profit_usdt = qty * abs(profit_distance)
    loss_usdt = qty * abs(loss_distance)
    
    # Hitung persentase ROI (terhadap margin, bukan position size)
    profit_percent = (profit_usdt / amount_usdt) * 100 if amount_usdt > 0 else 0
    loss_percent = (loss_usdt / amount_usdt) * 100 if amount_usdt > 0 else 0
    
    return {
        "profit_usdt": round(profit_usdt, 2),
        "loss_usdt": round(loss_usdt, 2),
        "profit_percent": round(profit_percent, 2),
        "loss_percent": round(loss_percent, 2)
    }

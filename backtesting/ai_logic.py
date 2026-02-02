"""
ai_logic.py - Simulasi Keputusan AI untuk Backtesting

Modul ini meniru logika AI (tanpa panggilan API) untuk keperluan backtest.
Strategi yang disimulasikan: LIQUIDITY_REVERSAL_MASTER
"""
import config
from typing import Dict, Optional


class AISimulator:
    """
    Simulates the AI's decision making process based on deterministic logic
    derived from the Liquidity Hunt / S1-R1 Sweep strategy.
    """

    def __init__(self):
        self.strategies = config.AVAILABLE_STRATEGIES

    def analyze_market_simulation(self, tech_data: Dict, sentiment_data: Dict) -> Dict:
        """
        Menganalisis data pasar dan mengembalikan keputusan trading yang meniru AI.

        Args:
            tech_data: Dictionary berisi indikator teknikal termasuk Pivot Points.
                       Expected keys: symbol, price, close, low (wick), high (wick),
                       pivot_P, pivot_S1, pivot_R1, rsi, stoch_k, volume_ratio,
                       btc_trend, btc_correlation
            sentiment_data: Dictionary berisi info sentimen (misal F&G).
                            Expected keys: fng_value

        Returns:
            Dictionary dengan keys: decision, confidence, reason, selected_strategy, execution_mode
        """

        # --- 1. Unpack Data ---
        symbol = tech_data.get('symbol', 'UNKNOWN')
        price_close = tech_data.get('close', 0)  # Harga CLOSE candle saat ini
        price_low = tech_data.get('low', price_close)  # Sumbu bawah (untuk deteksi sweep)
        price_high = tech_data.get('high', price_close)  # Sumbu atas

        # Pivot Points dari timeframe Daily
        pivot_P = tech_data.get('pivot_P', 0)
        pivot_S1 = tech_data.get('pivot_S1', 0)
        pivot_R1 = tech_data.get('pivot_R1', 0)

        # Indikator Standar
        rsi = tech_data.get('rsi', 50)
        stoch_k = tech_data.get('stoch_k', 50)
        volume_ratio = tech_data.get('volume_ratio', 1.0)

        # Filter BTC
        btc_trend = tech_data.get('btc_trend', 'NEUTRAL')
        btc_corr = tech_data.get('btc_correlation', 0.5)

        # Sentimen
        fng_value = sentiment_data.get('fng_value', 50)

        # --- 2. Determine Allowed Direction (Macro Filter - BTC Trend) ---
        allowed_direction = "BOTH"
        is_correlated = btc_corr >= config.CORRELATION_THRESHOLD_BTC

        if config.USE_BTC_CORRELATION and is_correlated:
            if btc_trend == "BULLISH":
                allowed_direction = "LONG_ONLY"
            elif btc_trend == "BEARISH":
                allowed_direction = "SHORT_ONLY"

        # --- 3. Strategy Evaluation: LIQUIDITY_REVERSAL_MASTER ---
        decision = "WAIT"
        confidence = 0
        reason = []
        strategy_name = "NONE"
        exec_mode = "LIQUIDITY_HUNT" if not config.ENABLE_MARKET_ORDERS else "MARKET"

        # Pastikan Pivot valid
        if pivot_S1 == 0 or pivot_R1 == 0 or pivot_P == 0:
            return {
                "decision": "WAIT",
                "confidence": 0,
                "reason": "Pivot levels not available.",
                "selected_strategy": "NONE",
                "execution_mode": exec_mode
            }

        # --- SCENARIO A: LONG (S1 Sweep / Liquidity Grab di Bawah) ---
        # Aturan:
        # 1. Sumbu (Low) menembus S1 tapi Close BERADA DI ATAS S1 (Sweep)
        # 2. RSI menunjukkan kondisi Oversold (< threshold)
        # 3. Volume tinggi (> 1.2x rata-rata)
        if allowed_direction in ["LONG_ONLY", "BOTH"]:
            is_s1_swept = (price_low <= pivot_S1) and (price_close > pivot_S1)
            is_oversold = rsi < config.RSI_OVERSOLD or stoch_k < 20
            has_volume_spike = volume_ratio >= 1.2

            if is_s1_swept:
                confidence = 65
                reason.append(f"S1 Swept (Low breached S1, Close recovered).")

                if is_oversold:
                    confidence += 15
                    reason.append(f"RSI Oversold ({rsi:.1f}).")

                if has_volume_spike:
                    confidence += 10
                    reason.append(f"Volume spike ({volume_ratio:.2f}x avg).")

                if confidence >= config.AI_CONFIDENCE_THRESHOLD:
                    decision = "BUY"
                    strategy_name = "LIQUIDITY_REVERSAL_MASTER"

        # --- SCENARIO B: SHORT (R1 Sweep / Liquidity Grab di Atas) ---
        # Aturan:
        # 1. Sumbu (High) menembus R1 tapi Close BERADA DI BAWAH R1 (Sweep)
        # 2. RSI menunjukkan kondisi Overbought (> threshold)
        # 3. Volume tinggi
        if decision == "WAIT" and allowed_direction in ["SHORT_ONLY", "BOTH"]:
            is_r1_swept = (price_high >= pivot_R1) and (price_close < pivot_R1)
            is_overbought = rsi > config.RSI_OVERBOUGHT or stoch_k > 80
            has_volume_spike = volume_ratio >= 1.2

            if is_r1_swept:
                confidence = 65
                reason.append(f"R1 Swept (High breached R1, Close recovered).")

                if is_overbought:
                    confidence += 15
                    reason.append(f"RSI Overbought ({rsi:.1f}).")

                if has_volume_spike:
                    confidence += 10
                    reason.append(f"Volume spike ({volume_ratio:.2f}x avg).")

                if confidence >= config.AI_CONFIDENCE_THRESHOLD:
                    decision = "SELL"
                    strategy_name = "LIQUIDITY_REVERSAL_MASTER"

        # --- 4. Sentiment Filter (Risk Adjustment) ---
        if decision == "BUY" and fng_value < 15:
            confidence -= 5
            reason.append("Caution: Extreme Fear (F&G < 15).")

        elif decision == "SELL" and fng_value > 85:
            confidence -= 5
            reason.append("Caution: Extreme Greed (F&G > 85).")

        # --- 5. Final Threshold Check ---
        if decision != "WAIT" and confidence < config.AI_CONFIDENCE_THRESHOLD:
            # Confidence turun di bawah threshold setelah adjustment
            original_decision = decision
            decision = "WAIT"
            reason.append(f"Final confidence {confidence}% below threshold ({config.AI_CONFIDENCE_THRESHOLD}%). Demoted from {original_decision}.")
            strategy_name = "NONE"

        return {
            "decision": decision,
            "confidence": confidence,
            "reason": "; ".join(reason) if reason else "No signal conditions met.",
            "selected_strategy": strategy_name,
            "execution_mode": exec_mode
        }

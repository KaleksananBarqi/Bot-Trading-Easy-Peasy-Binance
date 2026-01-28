import io
import base64
import json
import asyncio
import pandas as pd
import mplfinance as mpf
from openai import AsyncOpenAI
import httpx
import config
import matplotlib
matplotlib.use('Agg') # Force non-interactive backend
from src.utils.helper import logger
from src.utils.prompt_builder import build_pattern_recognition_prompt

class PatternRecognizer:
    def __init__(self, market_data_manager):
        self.market_data = market_data_manager
        self.cache = {} # {symbol: {'candle_ts': 12345, 'analysis': "..."}}
        
        # Initialize AI Client for Vision
        if config.USE_PATTERN_RECOGNITION and config.AI_API_KEY:
            self.client = AsyncOpenAI(
                base_url=config.AI_BASE_URL,
                api_key=config.AI_API_KEY,
                http_client=httpx.AsyncClient(),
                default_headers={
                    "HTTP-Referer": config.AI_APP_URL,
                    "X-Title": config.AI_APP_TITLE,
                }
            )
            self.model = config.AI_VISION_MODEL
            logger.info(f"👁️ Pattern Recognizer Initialized: {self.model}")
        else:
            self.client = None
            logger.warning("⚠️ Vision AI Disabled or Key Missing.")

    def get_setup_candles(self, symbol):
        """Retrieve candles for the SETUP timeframe"""
        return self.market_data.market_store.get(symbol, {}).get(config.TIMEFRAME_SETUP, [])

    def generate_chart_image(self, symbol):
        """
        Generate candlestick chart image using mplfinance AND extract raw stats.
        Returns (base64_string, raw_stats_dict).
        """
        candles = self.get_setup_candles(symbol)
        if not candles or len(candles) < config.MACD_SLOW: # Need at least MACD_SLOW
            return None, None
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            # --- MACD Calculation ---
            # append=True adds columns to df: MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
            import pandas_ta as ta
            df.ta.macd(fast=config.MACD_FAST, slow=config.MACD_SLOW, signal=config.MACD_SIGNAL, append=True)
            
            # Clean NaN created by indicators
            df.dropna(inplace=True)

            # --- EXTRACT RAW STATS (For AI Text Context) ---
            last_row = df.iloc[-1]
            macd_col = df.columns[-3] # MACD Line
            hist_col = df.columns[-2] # Histogram
            sig_col  = df.columns[-1] # Signal Line
            
            raw_stats = {
                "close": last_row['close'],
                "open": last_row['open'],
                "high": last_row['high'],
                "low": last_row['low'],
                "volume": last_row['volume'],
                "macd": last_row[macd_col],
                "macd_signal": last_row[sig_col],
                "macd_hist": last_row[hist_col],
                "last_ts": str(df.index[-1])
            }

            # Create Buffer
            buf = io.BytesIO()
            
            # --- MACD Plot Configuration ---
            # Use the same slice for main plot and addplots
            plot_data = df.tail(60)

            # Determine Histogram Colors
            colors = ['#26a69a' if v >= 0 else '#ef5350' for v in plot_data[hist_col]]

            macd_plots = [
                mpf.make_addplot(plot_data[macd_col], panel=2, color='#2962FF', width=1.2, ylabel='MACD'),  # MACD Line
                mpf.make_addplot(plot_data[sig_col],  panel=2, color='#FF6D00', width=1.2),               # Signal Line
                mpf.make_addplot(plot_data[hist_col], panel=2, type='bar', color=colors, alpha=0.5),      # Histogram
            ]

            # Style & Plot
            # rc params for dark mode
            # Custom Market Colors: Up=Green, Down=Red
            mc = mpf.make_marketcolors(
                up='#00ff00', down='#ff0000',
                edge='inherit',
                wick='inherit',
                volume='in',
                ohlc='i'
            )
            s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc, rc={'font.size': 8})
            
            mpf.plot(
                plot_data, # Last 60 candles
                type='candle',
                style=s,
                volume=True,
                addplot=macd_plots,
                panel_ratios=(6,2,2), # Price: 60%, Volume: 20%, MACD: 20%
                savefig=dict(fname=buf, dpi=100, bbox_inches='tight', format='png'),
                axisoff=True, 
                tight_layout=True
            )
            
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            return img_str, raw_stats
            
        except Exception as e:
            logger.error(f"❌ Chart Generation Failed {symbol}: {e}")
            return None, None

    def _is_valid_analysis(self, analysis_text: str) -> bool:
        """
        Validasi apakah output Vision AI cukup lengkap dan tidak terpotong.
        Kriteria:
        1. Panjang minimal sesuai config
        2. Mengandung salah satu keyword bias (BULLISH/BEARISH/NEUTRAL)
        3. Tidak berakhir dengan kata yang terpotong (misal: "bullish" tanpa titik di akhir)
        """
        if not analysis_text:
            return False
        
        # Cek panjang minimal
        if len(analysis_text) < config.PATTERN_MIN_ANALYSIS_LENGTH:
            return False
        
        # Cek keyword bias
        text_upper = analysis_text.upper()
        has_bias = any(kw in text_upper for kw in config.PATTERN_REQUIRED_KEYWORDS)
        if not has_bias:
            return False
        
        # Cek apakah kalimat terpotong (heuristic: tidak diakhiri tanda baca/emoji)
        analysis_stripped = analysis_text.strip()
        if analysis_stripped and analysis_stripped[-1].isalpha():
            # Kemungkinan terpotong mid-word
            return False
        
        return True

    async def analyze_pattern(self, symbol):
        """
        Main function to get pattern analysis.
        Checks cache first. Implements retry if validation fails.
        Returns Dict: {'analysis': "...", 'raw_data': {...}, 'is_valid': bool}
        """
        if not self.client or not config.USE_PATTERN_RECOGNITION:
            return {"analysis": "Vision AI Disabled.", "is_valid": False}

        # Check Cache based on last candle timestamp
        candles = self.get_setup_candles(symbol)
        if not candles: 
            return {"analysis": "Not enough data.", "is_valid": False}
        
        last_ts = candles[-1][0] # Timestamp newest candle
        
        cached = self.cache.get(symbol)
        if cached and cached.get('candle_ts') == last_ts:
            # Return cached analysis
            return cached['result']

        logger.info(f"👁️ Recognizing Pattern for {symbol} ({config.TIMEFRAME_SETUP})...")
        
        # Generate Image & Stats
        # Run in thread executor to not block async loop (mplfinance is blocking)
        result = await asyncio.to_thread(self.generate_chart_image, symbol)
        img_base64, raw_stats = result
        
        if not img_base64:
            return {"analysis": "Failed to generate chart.", "is_valid": False}

        # Retry Loop for AI Call
        for attempt in range(config.PATTERN_MAX_RETRIES + 1):
            try:
                # Pass Raw Stats to Prompt Builder
                prompt_text = build_pattern_recognition_prompt(symbol, config.TIMEFRAME_SETUP, raw_stats)
                
                logger.info(f"📤 Sending chart image to Vision AI for {symbol} (attempt {attempt + 1})...")
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt_text},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{img_base64}",
                                        "detail": "low" # Low detail to save tokens, usually enough for patterns
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=config.AI_VISION_MAX_TOKENS,
                    temperature=config.AI_VISION_TEMPERATURE
                )
                
                analysis_text = response.choices[0].message.content
                
                # VALIDASI OUTPUT
                if self._is_valid_analysis(analysis_text):
                    # Output valid - gunakan
                    final_result = {
                        'analysis': analysis_text,
                        'raw_data': raw_stats,
                        'is_valid': True
                    }
                    
                    # Update Cache
                    self.cache[symbol] = {
                        'candle_ts': last_ts,
                        'result': final_result
                    }
                    logger.info(f"✅ Pattern Analysis Done {symbol} (attempt {attempt + 1}): {analysis_text[:50]}...")
                    return final_result
                else:
                    # Output tidak valid - retry atau skip
                    logger.warning(f"⚠️ Pattern output terpotong {symbol} (attempt {attempt + 1}/{config.PATTERN_MAX_RETRIES + 1}): {analysis_text[:60]}...")
                    if attempt < config.PATTERN_MAX_RETRIES:
                        await asyncio.sleep(1)  # Brief delay sebelum retry
                        continue
                
            except Exception as e:
                logger.error(f"❌ Vision AI Error {symbol} (attempt {attempt + 1}): {e}")
                if attempt < config.PATTERN_MAX_RETRIES:
                    await asyncio.sleep(1)
                    continue
                break
        
        # Semua retry gagal - return dengan flag invalid
        logger.error(f"❌ All pattern retries failed for {symbol}. Skipping.")
        return {
            'analysis': 'Pattern analysis failed after retries.',
            'raw_data': raw_stats if raw_stats else {},
            'is_valid': False
        }


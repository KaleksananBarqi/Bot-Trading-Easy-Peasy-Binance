# 🤖 Easy Peasy Trading Bot: AI Vision & Logic Sniper

<div align="center">
  <img src="https://github.com/user-attachments/assets/6a3f3cc2-9367-4444-9c62-5bfaf7b53e9e" width="45%" alt="Bot Trading Banner" />

  <br />
  
  ![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
  ![Binance](https://img.shields.io/badge/Binance-Futures-yellow?style=for-the-badge&logo=binance)
  ![DeepSeek](https://img.shields.io/badge/Brain-DeepSeek%20V3-blueviolet?style=for-the-badge)
  ![Vision AI](https://img.shields.io/badge/Vision-Llama%20Vision-ff69b4?style=for-the-badge)
  ![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)
  ![License](https://img.shields.io/badge/License-PolyForm%20Noncommercial-5D6D7E?style=for-the-badge)
</div>

---

## 📖 Tentang Easy Peasy Bot (Dual AI Edition)

**Easy Peasy Trading Bot** bukan lagi sekadar bot algoritma biasa. Ini adalah sistem trading **Hybrid AI** yang menggabungkan analisis logika tekstual dengan kemampuan visual (computer vision).

Dibangun di atas arsitektur **Dual AI Core**, bot ini bisa "membaca" berita dan sentimen pasar, sekaligus "melihat" pola chart secara harfiah layaknya trader manusia profesional.

### 🧠 The Dual AI Core
1.  **Strategic Brain (Logic AI)**: Ditenagai oleh **DeepSeek V3**. Menganalisis **Market Structure** (Fractals HH/LL), **Triple Timeframe Confluence** (1H/30m/15m), sentimen berita, dan indikator teknikal untuk menentukan bias pasar yang akurat.
2.  **Visual Cortex (Vision AI)**: Ditenagai oleh **Llama-4-Maverick**. Modul ini menghasilkan chart candlestick real-time (via `mplfinance`) dan mengirimkannya ke AI untuk mendeteksi pola visual murni (Flags, Pennants, Head & Shoulders) yang sering terlewat oleh indikator matematis biasa.

---

## 🚀 Fitur Utama & Keunggulan

### 1. 👁️ Vision AI Pattern Recognition (NEW!)
Bot tidak buta. Sebelum mengeksekusi trade, bot akan:
*   Mencetak chart candlestick 30-menit / 1-jam secara internal.
*   Mengirim gambar chart tersebut ke AI Vision.
*   Mendapatkan analisis visual: *"Terlihat Bullish Pennant valid, potensi breakout tinggi."*

### 2. 🛡️ 5-Mode Adaptive Strategy Engine
Bot ini memiliki 5 kepribadian strategi yang beradaptasi dengan kondisi pasar (dikonfigurasi di `config.py`):
*   **PATTERN_CONFLUENCE_TREND (Conservative)**: Hanya masuk jika Trend Besar, Indikator, dan Pola Visual (Vision AI) semua berkata "YA". Winrate tinggi, frekuensi rendah.
*   **VOLATILITY_BREAKOUT_ADVANCED (Aggressive)**: Memburu ledakan harga dari fase konsolidasi. Mengandalkan ADX tinggi dan lonjakan Volume.
*   **LIQUIDITY_REVERSAL_MASTER (Contrarian)**: Mencari titik balik di area Extreme RSI dan Pivot Points. Melawan arus untuk profit maksimal.
*   **SMART_MONEY_FLOW (Whale Hunter)**: "Follow the Money". Hanya trading jika terdeteksi transaksi paus besar (> $100k) dan arus masuk Stablecoin positif.
*   **STANDARD_MULTI_CONFIRMATION (Balanced)**: Penyeimbang default yang menggunakan konfirmasi indikator standar.

### 3. 🐋 Whale & Flow Radar
Terintegrasi dengan **DefiLlama** dan **Whale Alert**:
*   **Stablecoin Inflow**: Memantau jika ada uang segar (USDT/USDC) masuk ke exchange (tanda beli).
*   **Whale Transactions**: Mendeteksi jika ada pembelian/penjualan masif di detik terakhir.
*   **Smart Money Positioning**: Memantau **Top Trader Long/Short Ratio** untuk membaca posisi pemain besar vs ritel (Contrarian Signal).

### 4. 📰 Global Sentiment Analysis
Mengambil data dari **Fear & Greed Index** dan **RSS Feed Berita Kripto**. Jika sentimen pasar "Extreme Fear", bot akan lebih berhati-hati mengambil posisi Long.

### 5. ⚡ Safety & Sniper Execution
*   **Liquidity Hunt (ATR Traps)**: Memasang Limit Order di area "jebakan" likuiditas retail (dihitung menggunakan ATR) untuk mendapatkan harga diskon terbaik.
*   **Ghost Order Protection**: Tracker lokal (`safety_tracker.json`) memastikan tidak ada order yang "nyangkut" atau terlupakan di exchange.
*   **Auto-Decoupling**: Fitur cerdas yang memisahkan Altcoin dari BTC jika korelasinya melemah (< 0.5), memungkinkan Altcoin pump saat BTC sideways.
*   **Smart Resource Architecture**: Menggunakan *Smart Data Throttling* untuk memisahkan data real-time (Price) dan slow data (Funding Rate/OI) demi efisiensi CPU dan API yang maksimal.

### 6. 🔬 Micro-Structure & Depth Analysis
*   **Order Book Imbalance**: Bot "mengintip" kedalaman pasar (Order Book Depth 2%) untuk mendeteksi tembok supply/demand tersembunyi yang tidak terlihat di chart biasa.
*   **Fractal Market Structure**: Algoritma internal secara otomatis memetakan struktur harga (Higher High, Lower Low, Sideways) untuk validasi trend murni tanpa lag.
---

## 🛠️ Instalasi & Konfigurasi

### Persyaratan
*   **Python 3.10+** (Wajib)
*   Akun Binance Futures
*   API Key dari [OpenRouter](https://openrouter.ai/) (Untuk akses DeepSeek & Llama Vision)

### Langkah 1: Clone Repository
```bash
git clone https://github.com/KaleksananBarqi/Bot-Trading-Easy-Peasy
cd Bot-Trading-Easy-Peasy
```

### Langkah 2: Virtual Environment (Rekomendasi)
```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
.\venv\Scripts\activate
```

### Langkah 3: Install Dependencies
Pastikan menginstall library untuk visualisasi chart (`mplfinance`).
```bash
pip install -r requirements.txt
```

### Langkah 4: Konfigurasi `.env`
Buat file `.env` dari template ini. Pastikan semua variabel terisi!

```ini
# --- BINANCE (Futures) ---
BINANCE_API_KEY=
BINANCE_SECRET_KEY=
BINANCE_TESTNET_KEY=
BINANCE_TESTNET_SECRET=

# --- NOTIFICATIONS (WAJIB) ---
TELEGRAM_TOKEN=
TELEGRAM_CHAT_ID=

# --- AI & EXTERNAL DATA (WAJIB) ---
AI_API_KEY=
CMC_API_KEY=
```

### Langkah 5: Jalankan Bot
```bash
python main.py
```
*Tunggu pesan: "🧠 AI Brain Initialized & 👁️ Pattern Recognizer Ready"*

---

## 📊 Struktur Proyek

```text
📂 Bot-Trading-Easy-Peasy/
 ├── 📂 backtesting/             # ⏳ Sistem Pengujian Backtest
 │    ├── 📊 backtest.py          # Engine utama simulasi trading
 │    ├── 📈 backtest_runner.py   # Script untuk menjalankan batch backtest
 │    ├── 📥 data_fetcher.py      # Pengambil data historis dari exchange
 │    └── 📂 historical_data/     # Database CSV data market masa lalu
 ├── 📂 src/                     # 🚀 Source Code Utama
 │    ├── 📂 modules/            # Modul Logika Inti
 │    │    ├── 🧠 ai_brain.py           # Otak AI (Strategic decision maker)
 │    │    ├── 👁️ pattern_recognizer.py # Vision AI (Analisis pola chart)
 │    │    ├── ⚙️ executor.py           # Eksekusi order & Management posisi
 │    │    ├── � market_data.py        # Pengolah indikator & price action
 │    │    ├── 🔗 onchain.py            # Analisis data whale & flow money
 │    │    └── 🗞️ sentiment.py          # Analisis News & Fear/Greed Index
 │    ├── 📂 utils/              # Fungsi Pembantu (Common Utils)
 │    │    ├── �️ helper.py             # Fungsi bantuan umum & logger
 │    │    └── �📝 prompt_builder.py    # Konstruktor prompt AI yang kompleks
 │    ├── ⚙️ config.py                 # PUSAT KONFIGURASI (Strategi & API)
 │    ├── 🚀 main.py                   # Titik masuk utama Bot (Prod)
 │    └── 📜 .env                      # konfigurasi environment
 ├── 📂 strategies/              # 📚 Dokumentasi & Blueprint Strategi
 ├── 📂 tests/                   # 🧪 Automated Testing (Unit & Integration)
 └── 📦 requirements.txt         # Daftar dependensi Python
```

---

## 🤝 Kontribusi
Ingin berkontribusi bikin bot ini makin "Easy Peasy"? Gas!
Silakan baca [CONTRIBUTING.md](CONTRIBUTING.md) untuk pedoman kontribusi, standar kode, dan cara pull request.
Kita sangat menghargai ide strategi baru, perbaikan bug, atau dokumentasi yang lebih baik.

---

## ⚠️ Disclaimer & Resiko

> **Trading Futures Berisiko Tinggi**
> Bot ini hanyalah alat bantu. Keputusan "Vision AI" dan "Logic AI" berbasis probabilitas, bukan kepastian.
>
> *   **AI Hallucination**: Model AI (bahkan Llama Vision) bisa salah menginterpretasikan gambar.
> *   **Financial Loss**: Gunakan fitur **Risk Management** (`RISK_PERCENT_PER_TRADE`) dengan bijak di `config.py`.
> *   **Latency**: Generate gambar chart membutuhkan waktu 1-3 detik, mungkin tidak cocok untuk HFT (High Frequency Trading) super cepat.

---

**Developed with ☕ & 🤖 by Kaleksanan Barqi Aji Massani**
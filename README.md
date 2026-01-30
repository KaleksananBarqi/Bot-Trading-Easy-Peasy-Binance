# 🤖 Easy Peasy Trading Bot: AI Vision & Logic Sniper

<div align="center">
  <img src="https://github.com/user-attachments/assets/6a3f3cc2-9367-4444-9c62-5bfaf7b53e9e" width="45%" alt="Bot Trading Banner" />

  <br />
  
  ![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
  ![Binance](https://img.shields.io/badge/Binance-Futures-yellow?style=for-the-badge&logo=binance)
  ![DeepSeek](https://img.shields.io/badge/Brain-DeepSeek%20V3.2-blueviolet?style=for-the-badge)
  ![Vision AI](https://img.shields.io/badge/Vision-Llama%20Vision-ff69b4?style=for-the-badge)
  ![Sentiment AI](https://img.shields.io/badge/Sentiment-Xiaomi%20Mimo-orange?style=for-the-badge)
  ![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)
  ![License](https://img.shields.io/badge/License-PolyForm%20Noncommercial-5D6D7E?style=for-the-badge)
</div>

---

## 📖 Tentang Easy Peasy Bot (Multi AI Edition)

**Easy Peasy Trading Bot** adalah sistem trading **Hybrid Multi-AI** tercanggih yang menggabungkan analisis logika, tekstual, dan kemampuan visual (computer vision) untuk menguasai market crypto.

Dibangun di atas arsitektur **Triple AI Core**, bot ini tidak hanya menghitung angka, tapi juga "membaca" narasi berita dan "melihat" struktur market secara visual layaknya trader pro.

### 🧠 The Triple AI Core
1.  **Strategic Brain (Logic AI)**: Ditenagai oleh **DeepSeek V3.2**. Bertugas sebagai eksekutor utama yang mengambil keputusan BUY/SELL/WAIT berdasarkan data teknikal, on-chain, dan sentimen secara holistik.
2.  **Visual Cortex (Vision AI)**: Ditenagai oleh **Llama-4-Maverick**. Modul Vision yang menganalisis chart candlestick real-time untuk mendeteksi pola murni (Flags, Pennants, Divergence) dan validasi struktur market.
3.  **Sentiment Analyst (Text AI)**: Ditenagai oleh **Xiaomi Mimo V2 Flash**. Spesialis narasi yang melakukan scanning berita global, news RSS, dan Fear & Greed index untuk menentukan "Market Vibe" saat ini.

---

## 🚀 Fitur Utama & Keunggulan

### 1. ⚖️ Dual Execution Plan (Anti-Bias AI) - **NEW!**
Bot tidak lagi menebak arah. Untuk setiap koin, bot menghitung dua skenario sekaligus:
*   **Scenario A (Long Case)**: Jika market bullish, di mana titik entry, SL, dan TP terbaik?
*   **Scenario B (Short Case)**: Jika market bearish, di mana titik entry, SL, dan TP terbaik?
AI akan memilih skenario yang memiliki probabilitas tertinggi berdasarkan data, menghilangkan bias subjektif.

### 2. �️ Vision AI Pattern Recognition
Integrasi Computer Vision yang canggih:
*   **Chart Rendering**: Otomatis mencetak chart teknikal lengkap dengan indikator.
*   **Validasi Pola**: AI Vision memvalidasi apakah ada pola reversal atau continuation.
*   **MACD Divergence Detection**: Deteksi visual divergensi harga vs momentum.

### 3. 🛡️ Adaptive Strategy Engine
Fitur strategi yang semakin kaya (dikonfigurasi di `config.py`):
*   **LIQUIDITY_REVERSAL_MASTER**: Mencari titik balik di area "Liquidity Hunt" atau Stop Run.
*   **COUNTER_TREND**: Melawan arus (fade) pada titik RSI/Stochastic ekstrem.
*   **MEAN_REVERSION**: Entry saat harga menyimpang jauh dan berpotensi kembali ke EMA.
*   **BB_BOUNCE**: Spesialis market sideways menggunakan Bollinger Bands.
*   **VOLATILITY_BREAKOUT**: Memburu momentum ledakan harga dari fase konsolidasi.

### 4. 🪙 Smart Per-Coin Configuration - **NEW!**
Setiap koin dalam daftar pantau dapat dikustomisasi secara spesifik:
*   **Specific Keywords**: News filtering yang lebih akurat per aset.
*   **BTC Correlation Toggle**: Opsi untuk mengikuti atau mengabaikan tren Bitcoin.
*   **Custom Leverage & Margin**: Pengaturan risiko berbeda untuk setiap koin.

### 5. 📑 Dynamic Prompt Generation
Sistem prompt AI yang cerdas dan adaptif:
*   **Toggle-able Market Orders**: Jika `ENABLE_MARKET_ORDERS = False`, AI hanya akan diberikan opsi Limit Order (Liquidity Hunt) untuk meminimalkan slippage dan fee.
*   **Contextual Hiding**: Jika korelasi BTC rendah, data BTC akan disembunyikan agar AI fokus pada price action independen koin tersebut.

### 6. 📢 Pro-Grade Notifications with ROI - **NEW!**
Notifikasi Telegram yang mendetail:
*   **ROI Calculation**: Menampilkan persentase keuntungan/kerugian berdasarkan modal dan leverage.
*   **Real-time Updates**: Notifikasi saat order dipasang (Limit), saat terisi (Filled), dan saat menyentuh TP/SL.

---

## 🛠️ Instalasi & Konfigurasi

### Persyaratan
*   **Python 3.10+** (Wajib)
*   Akun Binance Futures
*   API Key dari [OpenRouter](https://openrouter.ai/) (Penyedia model AI)

### Langkah Cepat
1.  **Clone**: `git clone https://github.com/KaleksananBarqi/Bot-Trading-Easy-Peasy.git`
2.  **Install**: `pip install -e .`
3.  **Config**: Salin `.env.example` ke `.env` dan isi semua API Key.
4.  **Run**: `python src/main.py`

---

## 📊 Struktur Proyek

```text
📂 Bot-Trading-Easy-Peasy/
 ├── 📂 src/                     # 🚀 Source Code Utama
 │    ├── 📂 modules/            # Modul Logika Inti
 │    │    ├── 🧠 ai_brain.py           # Otak Utama AI
 │    │    ├── 👁️ pattern_recognizer.py # Vision AI Engine
 │    │    ├── ⚙️ executor.py           # Eksekusi Order & Sync Posisi
 │    │    ├── 📊 market_data.py        # Pengolah Data & Indikator
 │    │    └── 🗞️ sentiment.py          # Analisis Berita & RSS
 │    ├── 📂 utils/              # Fungsi Pembantu
 │    │    ├── 🧮 calc.py               # Kalkulasi Dual Scenarios & Risk
 │    │    ├── 📝 prompt_builder.py     # Konstruktor Prompt AI Dinamis
 │    │    └── 🛠️ helper.py             # Logger & Tele Utils
 │    ├── ⚙️ config.py                 # PUSAT KONFIGURASI
 │    └── 🚀 main.py                   # Titik Masuk Bot
 ├── 📂 backtesting/             # ⏳ Sistem Pengujian Historis
 ├── 📂 tests/                   # 🧪 Automated Testing
 └── 📦 pyproject.toml           # Manajemen Dependensi Modern
```

---

## 🤝 Kontribusi
Kami terbuka untuk perbaikan strategi, optimasi AI, atau dokumentasi. Silakan ajukan **Pull Request** atau buka **Issue** jika menemukan bug.

---

## ⚠️ Disclaimer
**Trading crypto futures melibatkan risiko finansial yang besar.** Bot ini adalah alat bantu berbasis AI, bukan jaminan keuntungan. **AI bisa berhalusinasi** atau salah sinyal. Gunakan modal yang siap hilang dan aktifkan fitur risk management di `config.py`.

---
**Developed with ☕ & 🤖 by [Kaleksanan Barqi Aji Massani](https://github.com/KaleksananBarqi)**
# 🤖 Easy Peasy Trading Bot: Hybrid Sniper Strategy

<img width="1249" height="882" alt="Image" src="https://github.com/user-attachments/assets/9627dc67-76d4-4c80-8904-efe8f8c1d33c" />

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Binance](https://img.shields.io/badge/Binance-Futures-yellow?style=for-the-badge&logo=binance)
![Strategy](https://img.shields.io/badge/Strategy-Hybrid%20Sniper-red?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)

## 📖 Deskripsi Project

**Easy Peasy Trading Bot** adalah bot trading algoritmik otomatis untuk pasar **Binance Futures**. Bot ini dirancang menggunakan Python dengan pendekatan **Hybrid Strategy** yang cerdas: ia mampu beradaptasi pada kondisi pasar yang sedang *Trending* maupun *Sideways* (datar).

Keunggulan utama bot ini adalah fitur **"Liquidity Hunt" (Sniper Mode)**, di mana bot tidak sekadar masuk pasar secara membabi buta, melainkan mencoba melakukan *front-running* pada area di mana *retail trader* biasanya meletakkan Stop Loss mereka, sehingga mendapatkan harga entry yang jauh lebih presisi dan aman.

Bot ini dibangun di atas library `ccxt` untuk eksekusi order yang cepat dan `websockets` untuk pemantauan data pasar secara real-time tanpa delay.

---

## 🚀 Fitur Unggulan

### 1. 🧠 Hybrid Logic Engine
Bot tidak terpaku pada satu indikator. Ia membaca kondisi pasar menggunakan ADX (Average Directional Index):
* **Trend Mode (ADX > 25):** Mengaktifkan strategi *Trend Trap Pullback*. Bot menunggu harga koreksi ke area EMA (Exponential Moving Average) sebelum ikut tren.
* **Sideways Mode (ADX < 20):** Mengaktifkan strategi *BB Bounce Scalp*. Bot melakukan jual-beli cepat di area batas atas/bawah Bollinger Bands saat pasar tenang.

### 2. 👑 BTC King Filter
Bot ini memiliki "hierarki". Sebelum mengeksekusi trade pada Altcoin (seperti SOL, ETH, DOGE), bot akan mengecek tren **Bitcoin (BTC) di Timeframe 1 Jam**.
* Jika BTC Bullish -> Bot hanya mencari posisi **LONG** di Altcoin.
* Jika BTC Bearish -> Bot hanya mencari posisi **SHORT** di Altcoin.
* *Ini mencegah bot melawan arus utama pasar.*

### 3. 🔫 Sniper / Liquidity Hunt
Fitur unik yang membedakan bot ini. Alih-alih masuk di harga sekarang, bot menghitung jarak ATR (Average True Range) untuk memperkirakan di mana "Retail Trader" menaruh Stop Loss. Bot akan memasang **Limit Order** di area tersebut untuk mendapatkan harga diskon terbaik ("Sniper Entry").

### 4. 🛡️ Guardian Safety Monitor
Bot dilengkapi dengan *Safety Monitor* yang berjalan di thread terpisah (Asyncio Event Driven). Tugasnya:
* Mendeteksi "Ghost Orders" (order nyangkut tanpa posisi).
* Memastikan setiap posisi terbuka PASTI memiliki Stop Loss (SL) dan Take Profit (TP).
* Membersihkan Limit Order yang sudah kadaluarsa (Expired).

### 5. 💰 Dynamic Compounding
Manajemen uang otomatis. Bot membaca saldo wallet secara real-time dan menghitung ukuran posisi berdasarkan persentase resiko (default 5%). Jika saldo bertambah, ukuran trading otomatis membesar (Compounding Interest).

### 6. 📱 Telegram Integration
Laporan lengkap dikirim ke HP Anda:
* Notifikasi saat Bot Start/Mati.
* Sinyal Entry lengkap dengan analisa teknikal (RSI, ADX, EMA).
* Laporan Profit/Loss real-time saat posisi ditutup.

---

## 📊 Performa Backtest (Simulasi)

Berdasarkan pengujian data historis (1 - 30 Des 2025):

| Metric | Value |
| :--- | :--- |
| **Modal Awal** | $100.00 |
| **Net Profit** | **+$4,976.46** 🚀 |
| **Total Trade** | 1,206 Trades |
| **Win Rate** | **65.09%** |
| **Profit Factor** | 3.85 |
| **Top Coin** | ZEC/USDT (Champion 🏆) |

> *Disclaimer: Hasil masa lalu tidak menjamin kinerja masa depan. Backtest menggunakan data historis optimal.*

---

## 🛠️ Cara Install (Untuk Pemula)

Ikuti langkah ini satu per satu. Jangan terburu-buru.

### Persiapan
Pastikan komputer/laptop Anda sudah terinstall:
1.  **Python** (Versi 3.10 ke atas). [Download di sini](https://www.python.org/downloads/).
2.  **Git** (Opsional, untuk clone repo).

### Langkah 1: Download / Clone Repository
Buka terminal (CMD atau PowerShell), lalu arahkan ke folder di mana Anda ingin menyimpan bot.
```bash
gh repo clone KaleksananBarqi/Bot-Trading-Easy-Peasy-Binance

```

*(Atau cukup download ZIP dari GitHub dan ekstrak).*

### Langkah 2: Buat Virtual Environment (Wajib)

Ini agar library bot tidak bentrok dengan sistem komputer lain.

```bash
# Untuk Windows
python -m venv venv
.\venv\Scripts\activate

# Untuk Linux/Mac
python3 -m venv venv
source venv/bin/activate

```

*Tanda berhasil: Di terminal akan muncul tulisan `(venv)` di sebelah kiri.*

### Langkah 3: Install Dependencies

Install semua "kebutuhan" bot yang ada di file `requirements.txt`.

```bash
pip install -r requirements.txt

```

### Langkah 4: Konfigurasi API Key

1. Buat file baru bernama `.env` di dalam folder project.
2. Buka file `.env` dengan Notepad/VS Code, lalu isi data berikut (Dapatkan dari Binance & BotFather Telegram):

```env
# Binance API (Pilih mau pakai Testnet atau Live)
BINANCE_API_KEY=masukan_api_key_asli_disini
BINANCE_SECRET_KEY=masukan_secret_key_asli_disini

# Binance Testnet (Untuk latihan/demo)
BINANCE_TESTNET_KEY=masukan_key_testnet_disini
BINANCE_TESTNET_SECRET=masukan_secret_testnet_disini

# Telegram Config
TELEGRAM_TOKEN=123456:ABC-DefGhiJklmNoPqrStu...
TELEGRAM_CHAT_ID=123456789

```

### Langkah 5: Sesuaikan Config (Opsional)

Buka file `config.py`. Anda bisa mengubah:

* `PAKAI_DEMO = True` (Ubah ke `False` jika ingin pakai uang asli).
* `RISK_PERCENT_PER_TRADE = 5.0` (Resiko per trade).
* `DAFTAR_KOIN` (List koin yang ingin ditradingkan).

### Langkah 6: Jalankan Bot 🚀

```bash
python main.py

```

Jika berhasil, akan muncul pesan di terminal:
`✅ WebSocket Connected! System Online.`

---

## ⚠️ Disclaimer (Penting!)

Bot ini adalah alat bantu trading (tools), bukan mesin pencetak uang ajaib.

1. **Resiko Tinggi:** Trading Futures memiliki resiko likuidasi (uang habis).
2. **DYOR (Do Your Own Research):** Penulis tidak bertanggung jawab atas kerugian finansial yang terjadi akibat penggunaan kode ini.
3. **Gunakan Testnet:** Sangat disarankan mencoba di akun DEMO (Testnet) minimal 1 minggu sebelum menggunakan uang asli.

---

## 👨‍💻 Author & Credits

**Developed by Kaleksanan Barqi Aji Massani**
*Customer Success & Tech Enthusiast*

* **Logic Core:** Based on Hybrid Price Action (Trend + Mean Reversion).
* **Special Thanks:** To Open Source Community (CCXT, Pandas TA) & Crypto Analyst Mentors.
```
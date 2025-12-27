# 🤖 Bot Trading Easy Peasy - Liquidity Hunter

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)
![Exchange](https://img.shields.io/badge/Exchange-Binance%20Futures-yellow?style=for-the-badge&logo=binance)
![Status](https://img.shields.io/badge/Status-Aktif-success?style=for-the-badge)

## 📖 Deskripsi

**Bot Trading Easy Peasy** adalah bot trading otomatis untuk **Binance Futures** yang dibangun menggunakan Python. Bot ini dirancang dengan strategi *hybrid* yang cerdas: mengikuti tren (*Trend Following*) saat pasar bergerak kuat, dan mengambil keuntungan tipis (*Scalping*) saat pasar sedang *sideways*.

Fitur kuncinya adalah **"Liquidity Hunt"**, di mana bot tidak sembarangan masuk pasar, melainkan menunggu harga menyentuh area likuiditas (Stop Loss retail) untuk mendapatkan posisi entry terbaik.

## ✨ Fitur Unggulan

* **⚡ Eksekusi Cepat (Asyncio):** Menggunakan teknologi *asynchronous*, bot ini bisa memantau market, mengeksekusi order, dan mengirim notifikasi secara bersamaan tanpa *delay*.
* **🐋 Mode Liquidity Hunt:** Logika entry yang sabar. Bot menunggu harga "menjemput" order di area strategis (Trap Trading), bukan mengejar harga yang sudah lari (FOMO).
* **🛡️ Safety Monitor & Anti-Spam:**
    * **Database Lokal (`safety_tracker.json`):** Mencatat status Stop Loss/Take Profit secara lokal.
    * **Crash-Proof:** Jika bot atau server restart, data trading tidak hilang. Bot akan otomatis melanjutkan pengawalan posisi saat menyala kembali.
    * **Hemat API:** Mencegah *banned* dari Binance karena request yang berlebihan.
* **📊 Analisa Multi-Timeframe:**
    * **Major Trend (H1):** Membaca arah angin utama.
    * **Eksekusi (M15):** Membidik titik tembak yang presisi.
* **💰 Manajemen Risiko Otomatis:** Jarak Stop Loss (SL) dan Take Profit (TP) menyesuaikan volatilitas pasar (ATR), bukan angka tebak-tebakan.
* **🔔 Notifikasi Telegram Lengkap:** Laporan Entry, Target Tercapai, hingga perubahan tren BTC langsung masuk ke HP.

## 🧠 Cara Kerja Strategi

Bot otomatis mendeteksi kondisi pasar menggunakan indikator **ADX**:

1.  **Pasar Trending (ADX Tinggi):**
    * Bot hanya entry searah dengan Tren Utama.
    * Validasi entry menggunakan RSI dan Volume.
    * Mengincar koreksi (*pullback*) untuk entry yang aman.
2.  **Pasar Sideways (ADX Rendah):**
    * Menggunakan Bollinger Bands & Stochastic.
    * Strategi: Beli di Support bawah, Jual di Resistance atas.

## ⚠️ Disclaimer (PENTING)

> **PERHATIAN:** Software ini adalah proyek **Open Source untuk edukasi**. Trading Futures memiliki risiko finansial tinggi.
>
> Penulis tidak bertanggung jawab atas kerugian finansial yang mungkin terjadi. **Gunakan modal yang siap merugi (Uang Dingin) & Do Your Own Research (DYOR).**

## 🛠️ Cara Install & Pakai

1.  **Clone Repository**
    Buka terminal dan jalankan perintah ini:
    ```bash
    git clone [https://github.com/KaleksananBarqi/Bot-Trading-Easy-Peasy-Binance.git](https://github.com/KaleksananBarqi/Bot-Trading-Easy-Peasy-Binance.git)
    cd Bot-Trading-Easy-Peasy-Binance
    ```

2.  **Siapkan Virtual Environment (Wajib)**
    Supaya library tidak bentrok:
    ```bash
    # Untuk Windows
    python -m venv venv
    venv\Scripts\activate

    # Untuk Linux/Mac/VPS
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Library**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Konfigurasi**
    * Rename file `config.example.py` menjadi `config.py`.
    * Isi `API_KEY`, `SECRET_KEY`, dan `TELEGRAM_TOKEN` milik Anda di dalamnya.

5.  **Jalankan Bot**
    ```bash
    python main.py
    ```

---

### 👨‍💻 Author & Credits

Dibuat dengan ☕ dan baris kode oleh **[KaleksananBarqi]**.
*Didukung oleh **Massanigraphics** untuk sentuhan visual.*

---
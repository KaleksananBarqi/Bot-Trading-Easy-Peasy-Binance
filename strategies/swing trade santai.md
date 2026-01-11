# Strategi Daily Swing Trade: "The Daily Trend Trap"

Strategi ini dirancang untuk bot agar beroperasi dengan gaya **Swing Trading**, yang mengutamakan kualitas sinyal daripada kuantitas. Strategi ini memanfaatkan fitur *Trend Trap* dan *Liquidity Hunt* bawaan bot, namun disesuaikan untuk menangkap pergerakan tren besar (Major Trend) dan mengabaikan kebisingan pasar harian (Intraday Noise).

## 1. Konsep Utama: "Daily Trend, Hourly Entry"
Filosofi strategi ini sederhana: **Ikuti Arus Besar, Masuk Saat Diskon.**

*   **Major Context (D1)**: Kita hanya membuka posisi jika Tren Harian (Daily) sudah jelas arahnya.
*   **Execution (H1/H4)**: Kita mencari entri *pullback* (koreksi sementara) di timeframe lebih kecil (1 Jam atau 4 Jam) untuk mendapatkan harga masuk yang optimal.
*   **Target**: High Win Rate & High Risk-to-Reward (R:R).

## 2. Konfigurasi `src/config.py`

Untuk mengaktifkan mode Swing Trade Santai, sesuaikan variabel berikut di dalam file konfigurasi:

| Parameter | Value Lama (Scalping) | **Value Baru (Swing)** | Penjelasan |
| :--- | :--- | :--- | :--- |
| `TIMEFRAME_TREND` | `'1h'` | **`'1d'`** | Analisis tren utama (King Filter) wajib menggunakan candle Daily untuk melihat gambaran besar. |
| `TIMEFRAME_EXEC` | `'5m'` | **`'1h'`** atau **`'4h'`** | Eksekusi entri lebih santai, menunggu konfirmasi candle jam-jaman agar tidak tertipu 'noise'. |
| `ATR_MULTIPLIER_TP1` | `2.2` | **`3.0`** - **`5.0`** | Swing trade mengincar *profit run* yang jauh lebih panjang (bisa berhari-hari). |
| `ATR_MULTIPLIER_SL` | `1.0` | **`1.5`** | Stop Loss sedikit diperlebar untuk memberi ruang "nafas" terhadap volatilitas harian. |
| `COOLDOWN_IF_PROFIT` | `3600` (1 Jam) | **`43200`** (12 Jam) | Jangan *overtrade*. Setelah menang swing besar, istirahat untuk menghindari *giveback profit*. |
| `AI_SYSTEM_ROLE` | *(Default)* | *(Lihat Bawah)* | Menyesuaikan persona AI agar berpikir jangka panjang. |

### Rekomendasi `AI_SYSTEM_ROLE`:
```python
AI_SYSTEM_ROLE = "You are a Swing Trading AI. You perform Multi-Timeframe Analysis. You ONLY enter trades aligned with the Daily (D1) Trend. You prioritize Pullbacks over Breakouts."
```

## 3. Logika & Cara Kerja Bot

Dengan konfigurasi di atas, bot akan mengeksekusi logika berikut (berdasarkan `prompt_builder.py`):

### A. Filter Raja (King Filter) - D1
Bot pertama-tama mengecek indikator `ema_pos` dan `trend_major` pada timeframe **Daily**.
*   **Logika**:
    *   Jika Harga Daily > EMA 50 **DAN** BTC Bullish → **ONLY LONG**.
    *   Jika Harga Daily < EMA 50 **DAN** BTC Bearish → **ONLY SHORT**.
*   **Fungsi**: Filter ini secara otomatis membuang 50% sinyal palsu yang melawan tren utama. Kita tidak akan mencoba menangkap pisau jatuh.

### B. Mode "Trend Trap" (Jebakan Tren)
Pastikan `USE_TREND_TRAP_STRATEGY = True`. Bot akan aktif mendeteksi kondisi ini ketika **ADX Daily > 25** (Tren Sedang Kuat).
*   **Skenario**:
    *   Harga sedang *Uptrend* kuat di Daily.
    *   Namun, di timeframe eksekusi (H1), terjadi koreksi (misal: StochRSI *oversold* atau harga menyentuh EMA support).
*   **Aksi**:
    *   Bot menganggap ini sebagai **"Diskon"** atau peluang *Buy on Dip*, bukan pembalikan arah.

### C. Sniper Entry (Liquidity Hunt)
Pastikan `USE_LIQUIDITY_HUNT = True`.
*   **Mekanisme**:
    *   Bot **TIDAK** melakukan *Market Buy* saat sinyal muncul (menghindari FOMO di pucuk).
    *   Bot akan memasang **Limit Order** antrean di bawah harga sekarang (sejarak `1.0` - `1.5` ATR).
*   **Tujuan**:
    *   Menangkap "ekor" candle (*wick*) saat terjadi *flash dump* kecil atau volatilitas sesaat.
    *   Seringkali harga menyentuh limit order kita lalu memantul kembali sesuai tren. Ini drastis meningkatkan R:R dan Win Rate.

## 4. Keunggulan Strategi Ini

1.  **Anti-Stress**: Tidak perlu memantau grafik 5 menit yang bikin jantungan. Bot hanya bereaksi pada pergerakan signifikan.
2.  **Hemat Fee**: Frekuensi trading rendah (mungkin 1-3 trade per minggu per koin), sehingga biaya komisi sangat minim.
3.  **Akurasi Tinggi**: Kita hanya bertading searah dengan arus sungai yang deras (Tren Harian) namun masuk saat air sedang tenang (Pullback H1).

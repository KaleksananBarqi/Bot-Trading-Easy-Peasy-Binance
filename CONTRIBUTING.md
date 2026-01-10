# Panduan Kontribusi (Contributing Guidelines)

Terima kasih atas ketertarikan Anda untuk berkontribusi pada **Easy Peasy Trading Bot**! 🎉

Proyek ini adalah *open source* dan kami sangat menghargai bantuan dari komunitas, baik itu berupa perbaikan *bug*, penambahan fitur baru, perbaikan dokumentasi, atau sekadar saran. Dokumen ini akan memandu Anda mengenai cara berkontribusi.

## 📜 Kode Etik (Code of Conduct)

Harap dicatat bahwa proyek ini memiliki [Kode Etik](CODE_OF_CONDUCT.md). Dengan berpartisipasi dalam proyek ini, Anda diharapkan untuk mematuhi aturan tersebut. Harap laporkan perilaku yang tidak dapat diterima ke [kaleksanan.bam@gmail.com](mailto:kaleksanan.bam@gmail.com).

## 🐛 Cara Melaporkan Bug

Jika Anda menemukan *bug* atau *error* saat menjalankan bot:

1.  **Cek Issues:** Pastikan *bug* tersebut belum pernah dilaporkan sebelumnya di halaman [Issues](../../issues).
2.  **Buat Issue Baru:** Jika belum ada, buat laporan baru dengan format:
    *   **Judul:** Deskripsi singkat masalah.
    *   **Deskripsi:** Jelaskan apa yang terjadi.
    *   **Langkah Reproduksi:** Bagaimana cara memunculkan *error* tersebut?
    *   **Environment:** OS (Windows/Linux/Mac), versi Python, dan log error jika ada.

## 💡 Menyarankan Fitur Baru

Punya ide strategi trading baru atau integrasi AI yang lebih canggih?

1.  Buka [Issues](../../issues) dan gunakan label `enhancement` atau `feature request`.
2.  Jelaskan secara detail bagaimana fitur tersebut bekerja dan mengapa itu berguna bagi pengguna bot ini.

## 🛠️ Panduan Pengembangan (Development Setup)

Jika Anda ingin mengubah kode, ikuti langkah-langkah berikut untuk mengatur lingkungan kerja lokal Anda agar sesuai dengan standar proyek ini.

### 1. Fork & Clone

Fork repositori ini ke akun GitHub Anda, lalu *clone* ke komputer lokal:

```bash
git clone https://github.com/USERNAME-ANDA/Bot-Trading-Easy-Peasy-Binance.git
cd Bot-Trading-Easy-Peasy-Binance
```

### 2. Siapkan Environment

Proyek ini menggunakan Python 3.10+. Sangat disarankan menggunakan `venv` agar *dependencies* tidak berantakan.

**Windows:**

```bash
python -m venv venv
.\venv\Scripts\activate
```

**Linux/Mac:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

Pastikan Anda menginstal semua paket yang diperlukan seperti `ccxt`, `pandas_ta`, `openai`, dll:

```bash
pip install -r requirements.txt
```

### 4. Konfigurasi Lingkungan (.env)

Anda memerlukan file `.env` untuk menjalankan bot secara lokal. Salin contoh format yang ada di `README.md` dan gunakan API Key *testnet* atau *mock* jika memungkinkan untuk pengujian agar tidak mengambil risiko finansial saat *debugging*.

## 📝 Alur Kerja Pull Request (PR)

1.  **Buat Branch Baru:** Jangan bekerja langsung di branch `main`. Buat branch baru untuk fitur atau perbaikan Anda.

    ```bash
    git checkout -b fitur/nama-fitur-keren
    # atau
    git checkout -b fix/perbaikan-bug-ini
    ```

2.  **Lakukan Perubahan:** Tulis kode Anda. Pastikan kode bersih dan mudah dibaca.

3.  **Tes Kode:** Jalankan bot secara lokal dan pastikan tidak ada error saat inisialisasi (`python main.py`).

4.  **Commit Perubahan:** Gunakan pesan commit yang jelas dan deskriptif.

    ```bash
    git commit -m "Menambahkan fitur deteksi Whale baru via WebSocket"
    ```

5.  **Push ke GitHub:**

    ```bash
    git push origin fitur/nama-fitur-keren
    ```

6.  **Buat Pull Request:** Buka repositori asli dan buat Pull Request dari branch Anda. Jelaskan perubahan apa yang Anda lakukan.

## 🎨 Standar Kode (Style Guide)

*   **Python:** Ikuti panduan gaya PEP 8.
*   **Komentar:** Berikan komentar pada bagian logika yang rumit, terutama pada bagian strategi (`strategies/`) atau logika AI (`src/modules/ai_brain.py`).
*   **Tipe Data:** Gunakan *Type Hinting* jika memungkinkan untuk memudahkan pembacaan kode.

## ⚠️ Disclaimer Tambahan

Ingatlah bahwa ini adalah bot trading finansial. Setiap kontribusi kode yang berkaitan dengan eksekusi order (`executor.py`) harus diuji dengan sangat hati-hati. Jangan pernah meng-*hardcode* API Key atau kredensial pribadi dalam kode yang Anda *commit*.

Terima kasih telah membantu membuat **Easy Peasy Trading Bot** menjadi lebih cerdas dan *profitable*! 🚀

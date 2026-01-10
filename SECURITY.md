# Kebijakan Keamanan (Security Policy)

Kami menganggap serius keamanan **Easy Peasy Trading Bot**, karena proyek ini menyangkut aset finansial dan kunci akses pribadi (*API Keys*).

## 📦 Versi yang Didukung

Saat ini, kami hanya memberikan dukungan pembaruan keamanan untuk versi terbaru dari repositori ini.

| Versi | Didukung? |
| :--- | :--- |
| Latest Release | ✅ |
| < 6.2.0 | ❌ |

## 🐞 Melaporkan Kerentanan (Reporting a Vulnerability)

Jika Anda menemukan celah keamanan, **JANGAN membuka Issue publik**. Hal ini untuk mencegah pihak yang tidak bertanggung jawab memanfaatkan celah tersebut sebelum kami memperbaikinya.

Silakan ikuti langkah-langkah berikut:

1.  **Email Kami:** Kirimkan laporan detail ke **kaleksanan.bam@gmail.com**.
2.  **Isi Laporan:** Sertakan informasi berikut dalam email Anda:
    *   Deskripsi celah keamanan.
    *   Langkah-langkah untuk mereproduksi masalah (*Proof of Concept*).
    *   Dampak potensial (misal: kebocoran *API Key*, eksekusi order tanpa izin, dll).
3.  **Respon:** Kami akan berusaha merespons laporan Anda dalam waktu **48 jam**.

Kami akan memberi tahu Anda setelah celah tersebut diperbaiki dan merilis pembaruan sesegera mungkin.

## 🛡️ Praktik Keamanan untuk Pengguna

Demi keamanan aset Anda, kami mengingatkan seluruh pengguna untuk:

*   **JANGAN PERNAH** membagikan file `.env` Anda kepada siapa pun.
*   **JANGAN** meng-*upload* file `.env` atau `config.py` yang berisi kredensial asli ke GitHub publik. Gunakan `.gitignore`.
*   Batasi izin *API Key* di Binance/Exchange hanya untuk **"Enable Futures Trading"** atau **"Enable Reading"**. Jangan pernah mencentang "Enable Withdrawals".
*   Gunakan *IP Whitelist* pada pengaturan *API Key* di Exchange jika memungkinkan.

---

Terima kasih telah membantu menjaga keamanan komunitas ini!

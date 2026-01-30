# Implementation Plan: Perbaikan Informasi EMA di Prompt Builder

**Tanggal**: 28 Januari 2026  
**Status**: 📋 Menunggu Eksekusi  
**Prioritas**: MEDIUM  
**Estimasi Waktu**: 15-20 menit

---

## 📋 Summary

Memperbaiki penyajian informasi EMA di bagian `[TREND]` pada prompt AI agar lebih jelas dan tidak membingungkan. Saat ini ada dua variabel (`ema_pos` dan `trend_major`) yang seolah-olah kontradiktif sehingga berpotensi menyebabkan AI salah interpretasi atau hallucinate.

**Solusi**: Menggabungkan kedua signal EMA menjadi satu narasi yang jelas (`trend_narrative`) dan merestrukturisasi bagian `[TREND]` di prompt dengan informasi yang lebih eksplisit.

---

## 📂 File Structure (Dampak Perubahan)

```
src/
└── utils/
    └── prompt_builder.py   ← MODIFY (Satu-satunya file yang diubah)
```

**Tidak ada file baru yang perlu dibuat.**
**Tidak ada file yang perlu dihapus.**

---

## 🔧 Step-by-Step Plan

### Step 1: Tambah Helper Function untuk Trend Narrative

**Lokasi**: `src/utils/prompt_builder.py` (setelah fungsi `format_price`, sekitar baris 14)

**Aksi**: Tambahkan fungsi baru `get_trend_narrative()`

**Pseudocode**:
```python
def get_trend_narrative(price, ema_fast, ema_slow):
    """
    Menghasilkan narasi trend yang jelas berdasarkan posisi Price terhadap kedua EMA.
    
    Returns:
        tuple: (trend_narrative: str, ema_alignment: str)
        
    Logic Matrix:
    | Price vs EMA_Fast | Price vs EMA_Slow | Narrative                    |
    |-------------------|-------------------|------------------------------|
    | Above             | Above             | STRONG BULLISH               |
    | Below             | Below             | STRONG BEARISH               |
    | Below             | Above             | BULLISH PULLBACK             |
    | Above             | Below             | BEARISH BOUNCE               |
    """
    
    # Step 1.1: Tentukan posisi price terhadap masing-masing EMA
    price_above_fast = price > ema_fast
    price_above_slow = price > ema_slow
    
    # Step 1.2: Tentukan EMA Alignment (Fast vs Slow)
    if ema_fast > ema_slow:
        ema_alignment = "BULLISH ALIGNMENT (Fast > Slow)"
    else:
        ema_alignment = "BEARISH ALIGNMENT (Fast < Slow)"
    
    # Step 1.3: Tentukan Trend Narrative berdasarkan matrix di atas
    if price_above_fast and price_above_slow:
        trend_narrative = "STRONG BULLISH - Price above both EMAs"
    elif not price_above_fast and not price_above_slow:
        trend_narrative = "STRONG BEARISH - Price below both EMAs"
    elif not price_above_fast and price_above_slow:
        trend_narrative = "BULLISH PULLBACK - Price dipping but still in uptrend"
    elif price_above_fast and not price_above_slow:
        trend_narrative = "BEARISH BOUNCE - Price recovering but still in downtrend"
    else:
        trend_narrative = "UNCLEAR"
    
    return trend_narrative, ema_alignment
```

---

### Step 2: Panggil Helper Function di `build_market_prompt()`

**Lokasi**: `src/utils/prompt_builder.py`, di dalam fungsi `build_market_prompt()`, setelah parsing EMA data (sekitar baris 52, setelah `trend_major = ...`)

**Aksi**: Panggil fungsi `get_trend_narrative()` dan simpan hasilnya

**Pseudocode**:
```python
# Setelah baris: trend_major = tech_data.get('trend_major', 'UNKNOWN')

# [NEW] Generate clear trend narrative
trend_narrative, ema_alignment = get_trend_narrative(price, ema_fast, ema_slow)
```

---

### Step 3: Ubah Bagian [TREND] di Prompt Template

**Lokasi**: `src/utils/prompt_builder.py`, baris 251-254 (di dalam f-string prompt)

**Aksi**: Ganti format lama dengan format baru yang lebih jelas

**SEBELUM** (Baris 251-254):
```python
[TREND]
- Price: {format_price(price)}
- EMA Status: {ema_pos} (Fast: {format_price(ema_fast)} vs Slow: {format_price(ema_slow)})
- Major Trend (EMA {config.EMA_SLOW}): {trend_major}
```

**SESUDAH**:
```python
[TREND]
- Current Price: {format_price(price)}
- Trend Signal: {trend_narrative}
- EMA Details: Fast({config.EMA_FAST})={format_price(ema_fast)} | Slow({config.EMA_SLOW})={format_price(ema_slow)} | {ema_alignment}
```

---

### Step 4: Cleanup Variabel yang Tidak Terpakai

**Lokasi**: `src/utils/prompt_builder.py`

**Aksi**: 
- Variabel `ema_pos` (baris 51) **TETAP DIPERTAHANKAN** karena masih digunakan di `main.py` untuk logic filtering (baris 366, 368, 383)
- Variabel `trend_major` (baris 52) **TETAP DIPERTAHANKAN** karena masih digunakan di `main.py` (baris 446)

⚠️ **PENTING**: Kedua variabel ini TIDAK DIHAPUS dari parsing, hanya tidak ditampilkan lagi di prompt dengan format lama.

---

### Step 5: Verifikasi Output Prompt

**Aksi Manual**: Jalankan bot dan cek output prompt untuk memastikan bagian `[TREND]` sudah berubah

**Expected Output di Prompt**:
```
[TREND]
- Current Price: 89900.00
- Trend Signal: BULLISH PULLBACK - Price dipping but still in uptrend
- EMA Details: Fast(7)=90062.20 | Slow(21)=89787.57 | BULLISH ALIGNMENT (Fast > Slow)
```

---

## 📊 Analisis Dampak

| Modul | Dampak | Keterangan |
|-------|--------|------------|
| `prompt_builder.py` | MODIFIED | Inti perubahan |
| `market_data.py` | NONE | Tidak ada perubahan, logika perhitungan tetap |
| `main.py` | NONE | Tetap menggunakan `ema_pos` dan `trend_major` untuk logic internal |
| AI Response | INDIRECT | AI akan menerima informasi yang lebih jelas, mengurangi potensi hallucination |

---

## 📦 Dependencies

**Tidak ada library atau tool baru yang diperlukan.**

---

## ✅ Checklist Sebelum Produksi

- [ ] Step 1: Helper function `get_trend_narrative()` sudah ditambahkan
- [ ] Step 2: Helper function sudah dipanggil di `build_market_prompt()`
- [ ] Step 3: Bagian `[TREND]` sudah diupdate dengan format baru
- [ ] Step 4: Tidak ada error syntax
- [ ] Step 5: Output prompt sudah diverifikasi secara visual

---

## 🧪 Test Cases (Opsional)

Jika ingin membuat unit test, berikut skenario yang perlu dicakup:

| Test Case | Input (Price, EMA_Fast, EMA_Slow) | Expected Narrative |
|-----------|-----------------------------------|-------------------|
| Strong Bull | (100, 95, 90) | STRONG BULLISH |
| Strong Bear | (80, 90, 95) | STRONG BEARISH |
| Bull Pullback | (92, 95, 90) | BULLISH PULLBACK |
| Bear Bounce | (92, 90, 95) | BEARISH BOUNCE |

# Mini-Aes Implementation - v1 w/ Streamlit

## Kelompok

Nama | NRP
-|-
Nathan Kho Pancras | 5027231002
Amoes Noland | 5027231028
Fico Simhanandi | 5027231030
Rafi' Afnaan Fathurrahman | 5027231040
Dimas Andhika Diputra | 5027231074

## Prerequisites

* Make sure to have UV and Streamlit installed globally pada mesin anda.
* Pastikan untuk menginstal UV dan Streamlit secara global pada mesin anda.

```bash
uv sync
```

**Usage / Pemakaian**:

```bash
streamlit run app.py
```

## Dokumentasi

### Spesifikasi Algoritma Mini-AES

Implementasi Mini-AES ini mengikuti struktur dasar AES namun disederhanakan untuk blok dan kunci 16-bit.

1.  **Parameter Dasar:**
    *   **Ukuran Blok (Plaintext/Ciphertext):** 16 bit (4 nibble hexadesimal, misal "6F6B"). Setiap blok diproses secara individual oleh algoritma inti.
    *   **Ukuran Kunci:** 16 bit (4 nibble hexadesimal, misal "A73B"). Kunci yang sama digunakan untuk semua blok dalam satu pesan (dalam mode ECB atau CBC).
    *   **Jumlah Round:** 3 (`NUM_ROUNDS = 3`). Jumlah iterasi transformasi internal per blok.

2.  **Representasi Data:**
    *   Blok data 16-bit (4 nibble `N0 N1 N2 N3`) direpresentasikan secara internal sebagai matriks state 2x2 (`state_matrix`) untuk pemrosesan round:
        ```
        state_matrix = | N0  N2 |
                       | N1  N3 |
        ```
        Contoh: Plaintext `6F6B` -> `N0=6, N1=F, N2=6, N3=B` -> `[[0x6, 0x6], [0xF, 0xB]]`.

3.  **Key Expansion:**
    *   Proses menghasilkan serangkaian *round key* (RK0 hingga RK3) dari kunci 16-bit awal.
    *   Menggunakan `RotWord`, `SubWord` (dengan S_BOX), dan XOR dengan `RCON` *(Round Constants, hard-coded)* secara iteratif pada *word* (8-bit).
    *   Menghasilkan 4 buah *round key* 16-bit yang masing-masing direpresentasikan sebagai matriks 2x2.

4.  **Operasi Round:**
    Transformasi yang diterapkan secara berulang pada `state_matrix`:
    *   **`SubNibbles`:** Substitusi non-linear setiap nibble menggunakan tabel konstan `S_BOX` yang sudah ditentukan dalam kode *(hard-coded)*. Inversnya (`InvSubNibbles`) menggunakan `INV_S_BOX` untuk dekripsi.
    *   **`ShiftRows`:** Pergeseran siklik baris kedua ke kiri (menukar elemen kolom). Inversnya (`InvShiftRows`) identik untuk matriks 2x2.
    *   **`MixColumns`:** Transformasi linier yang mencampur nibble dalam setiap kolom menggunakan perkalian matriks di GF(2⁴) dengan `MIX_COL_MATRIX`. Inversnya (`InvMixColumns`) menggunakan `INV_MIX_COL_MATRIX`. Kedua tabel tersebut juga merupakan tabel konstan yang sudah ditentukan dalam kode *(hard-coded)*.
    *   **`AddRoundKey`:** Operasi XOR antara `state_matrix` dengan *round key* yang relevan.

5.  **Proses Enkripsi Inti (Per Blok):**
    *   Memiliki urutan: `AddRoundKey(RK0)` -> `[SubNibbles -> ShiftRows -> MixColumns -> AddRoundKey(RK1)]` -> `[SubNibbles -> ShiftRows -> MixColumns -> AddRoundKey(RK2)]` -> `[SubNibbles -> ShiftRows -> AddRoundKey(RK3)]`.

6.  **Proses Dekripsi Inti (Per Blok):**
    *   Merupakan invers dari proses enkripsi, menggunakan operasi invers (`InvSubNibbles`, `InvShiftRows`, `InvMixColumns`) dan urutan *round key* yang dibalik (RK3 hingga RK0).
    *   Memiliki urutan: `AddRoundKey(RK3)` -> `[InvShiftRows -> InvSubNibbles -> AddRoundKey(RK2) -> InvMixColumns]` -> `[InvShiftRows -> InvSubNibbles -> AddRoundKey(RK1) -> InvMixColumns]` -> `[InvShiftRows -> InvSubNibbles -> AddRoundKey(RK0)]`.

7.  **Mode Operasi:**
    *   **ECB (Electronic Codebook):**
        *   Mode operasi paling sederhana.
        *   Setiap blok plaintext 16-bit dienkripsi/didekripsi secara independen menggunakan fungsi enkripsi/dekripsi inti sesuai dengan *Proses Enkripsi/Dekripsi Inti* yang sudah disebutkan, dengan kunci yang sama.
        *   Tidak memerlukan IV.

    *   **CBC (Cipher Block Chaining):**
        *   Mode operasi yang lebih aman, menyembunyikan pola plaintext.
        *   Membutuhkan *Initialization Vector* (IV) 16-bit yang unik (idealnya acak) untuk setiap pesan. Bisa juga dimasukkan IV secara fixed/manual dalam program untuk demonstrasi khusus.
        *   **Enkripsi CBC:**
            1.  Blok plaintext pertama (P1) di-XOR dengan IV.
            2.  Hasil XOR dienkripsi menggunakan algoritma inti untuk menghasilkan blok ciphertext pertama (C1).
            3.  Blok plaintext berikutnya (Pi) di-XOR dengan blok ciphertext sebelumnya (C[i-1]).
            4.  Hasil XOR dienkripsi untuk menghasilkan Ci.
            5.  Proses berlanjut untuk semua blok.
            6.  Output akhir adalah IV diikuti oleh semua blok ciphertext (`IV || C1 || C2 || ... || Cn`).
        *   **Dekripsi CBC:**
            1.  IV diekstrak dari awal ciphertext.
            2.  Blok ciphertext pertama (C1) didekripsi menggunakan algoritma inti.
            3.  Hasil dekripsi di-XOR dengan IV untuk mendapatkan blok plaintext pertama (P1).
            4.  Blok ciphertext berikutnya (Ci) didekripsi menggunakan algoritma inti lagi.
            5.  Hasil dekripsi di-XOR dengan blok ciphertext sebelumnya (C[i-1]) untuk mendapatkan Pi.
            6.  Proses berlanjut untuk semua blok.
            7.  Output akhir adalah gabungan semua blok plaintext (`P1 || P2 || ... || Pn`).

### Flowchart
#### Alur Key Expansion
(WIP)
#### Alur Mini-AES
(WIP)

### Implementasi Program
(WIP, nanti dijelaskan bagian UI dan fitur pendukung yg tidak berhubungan dengan algoritma)

### Penjelasan Testcase
(WIP)

### Analisis
#### Kelebihan Mini-AES
(WIP)
#### Keterbatasan Mini-AES
(WIP)
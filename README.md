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

![Key Expansion](img/keyexp.png)

#### Alur Mini-AES

##### Algoritma ECB (Inti)

![ECB Main](img/ecb.png)

##### Algoritma CBC

![CBC](img/cbc.png)

### Implementasi Program

Mini-AES 16-bit ini diimplementasikan melalui sebuah GUI web-based yang menggunakan Streamlit. Fitur-fitur yang tersedia meliputi:

*   **Input dan Output:**
    *   **Input Pengguna:** Plaintext/Ciphertext dan Key dimasukkan oleh pengguna melalui text input pada interface Streamlit. Input diharapkan dalam format string heksadesimal. Panjang Key divalidasi harus 4 karakter hex (16-bit). Untuk mode CBC, input IV (juga 4 hex char) disediakan.
    *   **Proses Internal:** String heksadesimal input dikonversi menjadi daftar *nibble* (integer 0-15) sebelum diproses oleh algoritma inti.
    *   **Output Hasil:** Hasil akhir (Ciphertext untuk enkripsi, Plaintext untuk dekripsi) ditampilkan kembali sebagai string hex dalam codeblock.
    *   **Output Proses Round:** Setiap fungsi utama (`key_expansion`, `encrypt`, `decrypt`, `encrypt_cbc`, `decrypt_cbc` di `mini_aes.py`) menghasilkan *log* berupa list string yang merinci setiap langkah transformasi (misalnya, hasil `SubNibbles`, `ShiftRows`, `MixColumns`, `AddRoundKey` per round, serta langkah Key Expansion seperti `RotWord`, `SubWord`, XOR dengan `RCON`). Log ini ditampilkan di GUI dalam bagian "Show detailed process log", yang memungkinkan pengguna untuk memeriksa jalannya algoritma secara detail.

*   **Test Case:**
    *   Beberapa contoh test case (termasuk standar 6F6B/A73B, input nol, input FFFF, dan contoh multi-blok CBC) didefinisikan dalam list `TEST_CASES` di `app.py`.
    *   Pengguna dapat memilih test case dari selection box yang ditampilkan dan memasukkannya ke field input menggunakan tombol "Apply Selected Test Case".
    *   Meskipun *expected output* tidak ditampilkan langsung di UI, kebenaran implementasi bisa diverifikasi dengan menjalankan enkripsi lalu dekripsi pada test case yang sama dan memastikan plaintext asli diperoleh kembali.

*   **Antarmuka Pengguna (GUI):**
    *   Antarmuka dibangun menggunakan **Streamlit**, menyediakan pengalaman interaktif berbasis web.
    *   Komponen utama GUI meliputi:
        *   Pilihan mode operasi (Radio button untuk "Encrypt"/"Decrypt").
        *   Pilihan mode cipher (Radio button untuk "ECB"/"CBC").
        *   Field input teks untuk Plaintext/Ciphertext, Key, dan IV (hanya muncul saat CBC dipilih).
        *   Tombol "Process" untuk memulai operasi.
        *   Area output untuk menampilkan hasil dan log proses terperinci (dalam *expander*).
        *   Dropdown dan tombol untuk memilih dan menerapkan test case.
        *   Tabulasi untuk memisahkan fungsionalitas utama dengan fitur Ekspor/Impor.

*   **Mode Operasi Blok:**
    *   **ECB (Electronic Codebook):**
        *   Dipilih via radio button "ECB".
        *   Input (Plaintext/Ciphertext) yang lebih panjang dari 16-bit (4 hex char) secara otomatis dibagi menjadi blok-blok 16-bit. Setiap blok dienkripsi/didekripsi secara independen menggunakan fungsi inti dengan kunci yang sama. Fungsi pembungkus `encrypt`/`decrypt` menangani pembagian blok ini.
        *   Tidak memerlukan IV.
        
    *   **CBC (Cipher Block Chaining):**
        *   Dipilih via radio button "CBC".
        *   Membutuhkan IV 16-bit. Jika input IV kosong saat enkripsi, IV digenerate secara acak dan ditampilkan.
        *   **Enkripsi:** Blok plaintext pertama di-XOR dengan IV sebelum enkripsi inti. Blok plaintext selanjutnya di-XOR dengan blok *ciphertext* sebelumnya sebelum dienkripsi. IV asli ditambahkan di awal output ciphertext akhir.
        *   **Dekripsi:** IV diekstrak dari 4 karakter hex pertama input ciphertext. Blok ciphertext pertama didekripsi, lalu hasilnya di-XOR dengan IV. Blok ciphertext selanjutnya didekripsi, lalu hasilnya di-XOR dengan blok *ciphertext* sebelumnya.

*   **Export dan Import File:**
    *   **Export:**
        *   Diakses melalui tab "Export".
        *   Setelah operasi selesai, pengguna dapat menyimpan detail (Mode Operasi, Mode Cipher, Input, Key, IV (jika CBC), Output, dan Log Proses Lengkap) ke dalam file CSV.
        *   File disimpan di direktori `logs/` dengan nama file berdasarkan timestamp atau input pengguna. Sebuah tombol download juga disediakan pada GUI.
    *   **Import:**
        *   Diakses melalui tab "Import".
        *   Pengguna dapat mengunggah file CSV yang sebelumnya diekspor.
        *   Data yang diimpor (Input, Key, IV, dll.) ditampilkan, dan tombol "Apply imported values" memungkinkan pengguna mengisi field input utama aplikasi dengan nilai-nilai tersebut untuk dianalisis atau diproses ulang.
           
### Penjelasan Testcase
#### 1. ECB (PT = 6F6B, Key = A73B)
##### Encryption
1.  **Input:** Plaintext `6F6B`, Key `A73B`.
2.  **Representasi Awal:**
    *   Plaintext Matrix (State): `[[6, 6], [F, B]]`
    *   Key Matrix: `[[A, 3], [7, B]]`
3.  **Key Expansion:**
    *   Proses menghasilkan kunci-kunci round dari Key `A73B`.
    *   Round Keys yang dihasilkan:
        *   `RK0 = A73B`
        *   `RK1 = 8CB7`
        *   `RK2 = FF48`
        *   `RK3 = D29A`
4.  **Round 0:**
    *   `AddRoundKey(State, RK0)`: State awal di-XOR dengan `RK0`.
        *   `[[6, 6], [F, B]] XOR [[A, 3], [7, B]] = [[C, 5], [8, 0]]` -> `C850`
5.  **Round 1:**
    *   `SubNibbles`: Setiap nibble pada state disubstitusi menggunakan `S_BOX`.
        *   `[[C, 5], [8, 0]]` -> `[[C, 1], [6, 9]]` -> `C619`
    *   `ShiftRows`: Baris kedua state digeser (elemen ditukar).
        *   `[[C, 1], [6, 9]]` -> `[[C, 1], [9, 6]]` -> `C916`
    *   `MixColumns`: Setiap kolom state dicampur menggunakan perkalian matriks di GF(2⁴).
        *   `[[C, 1], [9, 6]]` -> `[[E, A], [C, 2]]` -> `ECA2`
    *   `AddRoundKey(State, RK1)`: State hasil `MixColumns` di-XOR dengan `RK1`.
        *   `[[E, A], [C, 2]] XOR [[8, B], [C, 7]] = [[6, 1], [0, 5]]` -> `6015`
6.  **Round 2:**
    *   `SubNibbles`: Substitusi nibble pada state `6015` menggunakan `S_BOX`.
        *   `[[6, 1], [0, 5]]` -> `[[8, 4], [9, 1]]` -> `8941`
    *   `ShiftRows`: Geser baris kedua state `8941`.
        *   `[[8, 4], [9, 1]]` -> `[[8, 4], [1, 9]]` -> `8149`
    *   `MixColumns`: Campur kolom state `8149`.
        *   `[[8, 4], [1, 9]]` -> `[[C, 6], [7, A]]` -> `C76A`
    *   `AddRoundKey(State, RK2)`: State hasil `MixColumns` di-XOR dengan `RK2`.
        *   `[[C, 6], [7, A]] XOR [[F, 4], [F, 8]] = [[3, 2], [8, 2]]` -> `3822`
7.  **Round 3 (Final):**
    *   `SubNibbles`: Substitusi nibble pada state `3822` menggunakan `S_BOX`.
        *   `[[3, 2], [8, 2]]` -> `[[B, A], [6, A]]` -> `B6AA`
    *   `ShiftRows`: Geser baris kedua state `B6AA`.
        *   `[[B, A], [6, A]]` -> `[[B, A], [A, 6]]` -> `BAA6`
    *   `AddRoundKey(State, RK3)`: State hasil `ShiftRows` di-XOR dengan `RK3` (Tidak ada `MixColumns` di round terakhir).
        *   `[[B, A], [A, 6]] XOR [[D, 9], [2, A]] = [[6, 3], [8, C]]` -> `683C`
8.  **Output:** Ciphertext `683C`.

##### Decryption
1.  **Input:** Ciphertext `683C`, Key `A73B`.
2.  **Representasi Awal:**
    *   Ciphertext Matrix (State): `[[6, 3], [8, C]]`
3.  **Key Expansion:** Sama seperti enkripsi, menghasilkan `RK0=A73B`, `RK1=8CB7`, `RK2=FF48`, `RK3=D29A`.
4.  **Round 0 (Inverse):**
    *   `AddRoundKey(State, RK3)`: State awal (ciphertext) di-XOR dengan `RK3` (kunci round terakhir).
        *   `[[6, 3], [8, C]] XOR [[D, 9], [2, A]] = [[B, A], [A, 6]]` -> `BAA6`
5.  **Round 1 (Inverse):**
    *   `InvShiftRows`: Baris kedua state digeser kembali (identik dengan `ShiftRows` untuk 2x2).
        *   `[[B, A], [A, 6]]` -> `[[B, A], [6, A]]` -> `B6AA`
    *   `InvSubNibbles`: Setiap nibble pada state disubstitusi menggunakan `INV_S_BOX`.
        *   `[[B, A], [6, A]]` -> `[[3, 2], [8, 2]]` -> `3822`
    *   `AddRoundKey(State, RK2)`: State hasil `InvSubNibbles` di-XOR dengan `RK2`.
        *   `[[3, 2], [8, 2]] XOR [[F, 4], [F, 8]] = [[C, 6], [7, A]]` -> `C76A`
6.  **Round 2 (Inverse):**
    *   `InvMixColumns`: Setiap kolom state dicampur menggunakan matriks invers `INV_MIX_COL_MATRIX`.
        *   `[[C, 6], [7, A]]` -> `[[8, 4], [1, 9]]` -> `8149`
    *   `InvShiftRows`: Geser baris kedua state `8149`.
        *   `[[8, 4], [1, 9]]` -> `[[8, 4], [9, 1]]` -> `8941`
    *   `InvSubNibbles`: Substitusi nibble pada state `8941` menggunakan `INV_S_BOX`.
        *   `[[8, 4], [9, 1]]` -> `[[6, 1], [0, 5]]` -> `6015`
    *   `AddRoundKey(State, RK1)`: State hasil `InvSubNibbles` di-XOR dengan `RK1`.
        *   `[[6, 1], [0, 5]] XOR [[8, B], [C, 7]] = [[E, A], [C, 2]]` -> `ECA2`
7.  **Round 3 (Inverse):**
    *   `InvMixColumns`: Campur kolom state `ECA2` menggunakan `INV_MIX_COL_MATRIX`.
        *   `[[E, A], [C, 2]]` -> `[[C, 1], [9, 6]]` -> `C916`
    *   `InvShiftRows`: Geser baris kedua state `C916`.
        *   `[[C, 1], [9, 6]]` -> `[[C, 1], [6, 9]]` -> `C619`
    *   `InvSubNibbles`: Substitusi nibble pada state `C619` menggunakan `INV_S_BOX`.
        *   `[[C, 1], [6, 9]]` -> `[[C, 5], [8, 0]]` -> `C850`
    *   `AddRoundKey(State, RK0)`: State hasil `InvSubNibbles` di-XOR dengan `RK0`.
        *   `[[C, 5], [8, 0]] XOR [[A, 3], [7, B]] = [[6, 6], [F, B]]` -> `6F6B`
8.  **Output:** Plaintext `6F6B`. Hasil dekripsi sesuai dengan plaintext awal.

#### 2. CBC (PT = 6F6B2D3B, Key = A73B, IV = 1234)
##### Encryption
1.  **Input:** Plaintext `6F6B2D3B`, Key `A73B`, IV `1234`.
2.  **Pembagian Blok:** Plaintext dibagi menjadi 2 blok: `P1 = 6F6B`, `P2 = 2D3B`.
3.  **Key Expansion:** Sama seperti ECB, menghasilkan `RK0=A73B`, `RK1=8CB7`, `RK2=FF48`, `RK3=D29A`.
4.  **Proses Blok 1:**
    *   `XOR dengan IV`: Blok plaintext pertama di-XOR dengan IV.
        *   `P1 XOR IV` = `6F6B XOR 1234 = 7D5F`.
    *   **Enkripsi Inti (ECB) pada `7D5F`:** Hasil XOR dienkripsi menggunakan algoritma Mini-AES inti.
        *   Round 0: `AddRoundKey(7D5F, A73B) = DA64`
        *   Round 1: `SubNibbles(DA64)=E08D`, `ShiftRows(E08D)=ED80`, `MixColumns(ED80)=F086`, `AddRoundKey(F086, 8CB7)=7C31`
        *   Round 2: `SubNibbles(7C31)=5CB4`, `ShiftRows(5CB4)=54BC`, `MixColumns(54BC)=63E6`, `AddRoundKey(63E6, FF48)=9CAE`
        *   Round 3: `SubNibbles(9CAE)=2C0F`, `ShiftRows(2C0F)=2F0C`, `AddRoundKey(2F0C, D29A)=FD96`
    *   **Ciphertext Blok 1 (C1):** `FD96`.
5.  **Proses Blok 2:**
    *   `XOR dengan Ciphertext Sebelumnya`: Blok plaintext kedua di-XOR dengan ciphertext blok pertama (C1).
        *   `P2 XOR C1` = `2D3B XOR FD96 = D0AD`.
    *   **Enkripsi Inti (ECB) pada `D0AD`:** Hasil XOR dienkripsi menggunakan algoritma Mini-AES inti.
        *   Round 0: `AddRoundKey(D0AD, A73B) = 7796`
        *   Round 1: `SubNibbles(7796)=5528`, `ShiftRows(5528)=5825`, `MixColumns(5825)=3F5D`, `AddRoundKey(3F5D, 8CB7)=B3EA`
        *   Round 2: `SubNibbles(B3EA)=3BF0`, `ShiftRows(3BF0)=30FB`, `MixColumns(30FB)=3C52`, `AddRoundKey(3C52, FF48)=C31A`
        *   Round 3: `SubNibbles(C31A)=CB40`, `ShiftRows(CB40)=C04B`, `AddRoundKey(C04B, D29A)=12D1`
    *   **Ciphertext Blok 2 (C2):** `12D1`.
6.  **Output:** Gabungan IV dan Ciphertext Blok: `IV || C1 || C2` = `1234FD9612D1`.

##### Decryption
1.  **Input:** Ciphertext `1234FD9612D1`, Key `A73B`.
2.  **Ekstraksi IV dan Pembagian Blok:**
    *   `IV = 1234`.
    *   Ciphertext dibagi menjadi 2 blok: `C1 = FD96`, `C2 = 12D1`.
3.  **Key Expansion:** Sama seperti enkripsi, menghasilkan `RK0=A73B`, `RK1=8CB7`, `RK2=FF48`, `RK3=D29A`.
4.  **Proses Blok 1:**
    *   **Dekripsi Inti (ECB) pada `C1 = FD96`:** Ciphertext blok pertama didekripsi menggunakan algoritma Mini-AES inti invers.
        *   Round 0 (Inv): `AddRoundKey(FD96, D29A) = 2F0C`
        *   Round 1 (Inv): `InvShiftRows(2F0C)=2C0F`, `InvSubNibbles(2C0F)=9CAE`, `AddRoundKey(9CAE, FF48)=63E6`
        *   Round 2 (Inv): `InvMixColumns(63E6)=54BC`, `InvShiftRows(54BC)=5CB4`, `InvSubNibbles(5CB4)=7C31`, `AddRoundKey(7C31, 8CB7)=F086`
        *   Round 3 (Inv): `InvMixColumns(F086)=ED80`, `InvShiftRows(ED80)=E08D`, `InvSubNibbles(E08D)=DA64`, `AddRoundKey(DA64, A73B)=7D5F`
    *   Hasil Dekripsi Inti: `7D5F`.
    *   `XOR dengan IV`: Hasil dekripsi inti di-XOR dengan IV.
        *   `7D5F XOR 1234 = 6F6B`.
    *   **Plaintext Blok 1 (P1):** `6F6B`.
5.  **Proses Blok 2:**
    *   **Dekripsi Inti (ECB) pada `C2 = 12D1`:** Ciphertext blok kedua didekripsi menggunakan algoritma Mini-AES inti invers.
        *   Round 0 (Inv): `AddRoundKey(12D1, D29A) = C04B`
        *   Round 1 (Inv): `InvShiftRows(C04B)=CB40`, `InvSubNibbles(CB40)=C31A`, `AddRoundKey(C31A, FF48)=3C52`
        *   Round 2 (Inv): `InvMixColumns(3C52)=30FB`, `InvShiftRows(30FB)=3BF0`, `InvSubNibbles(3BF0)=B3EA`, `AddRoundKey(B3EA, 8CB7)=3F5D`
        *   Round 3 (Inv): `InvMixColumns(3F5D)=5825`, `InvShiftRows(5825)=5528`, `InvSubNibbles(5528)=7796`, `AddRoundKey(7796, A73B)=D0AD`
    *   Hasil Dekripsi Inti: `D0AD`.
    *   `XOR dengan Ciphertext Sebelumnya (C1)`: Hasil dekripsi inti di-XOR dengan ciphertext blok pertama (C1).
        *   `D0AD XOR FD96 = 2D3B`.
    *   **Plaintext Blok 2 (P2):** `2D3B`.
6.  **Output:** Gabungan Plaintext Blok: `P1 || P2` = `6F6B2D3B`. Hasil dekripsi sesuai dengan plaintext awal.

### Analisis
#### Kelebihan Mini-AES

1.   **Nilai Edukasi Tinggi:** Merupakan keunggulan utama. Ukuran blok (`16-bit`), kunci (`16-bit`), dan *state matrix* (`2x2`) yang kecil membuatnya ideal untuk pembelajaran. Proses enkripsi/dekripsi, termasuk operasi seperti `SubNibbles`, `ShiftRows`, `MixColumns`, dan `Key Expansion`, dapat diikuti dan bahkan dihitung secara manual, jauh lebih mudah dibandingkan AES standar (`128-bit`). Log detail yang dihasilkan oleh program ini juga membantu visualisasi setiap langkah.
2.   **Implementasi Sederhana:** Kode relatif ringkas. Logika operasi, terutama perkalian di `GF(2^4)` (`gf_multiply`), lebih mudah dipahami dan diimplementasikan daripada `GF(2^8)` pada AES asli. Ini memfasilitasi pemahaman bagi pemrogram pemula.
3.   **Demonstrasi Prinsip Kriptografi Modern:** Meskipun sederhana, implementasi ini efektif menunjukkan konsep inti cipher blok modern:
      *   **Confusion:** Dicapai melalui substitusi non-linear `SubNibbles` menggunakan `S_BOX`.
      *   **Diffusion:** Dicapai melalui permutasi `ShiftRows` dan pencampuran linier `MixColumns` untuk menyebarkan pengaruh bit.
      *   **Key Addition:** Penggabungan kunci ronde via `AddRoundKey` (operasi XOR).
      *   **Key Schedule:** Proses derivasi kunci ronde (`RK0` - `RK3`) dari kunci utama melalui `key_expansion`.
      *   **Struktur Ronde:** Pengulangan transformasi (`SubNibbles`, `ShiftRows`, `MixColumns`, `AddRoundKey`) dalam beberapa ronde (`NUM_ROUNDS = 3`).
4.   **Kebutuhan Sumber Daya Rendah:** Operasi yang sederhana dan ukuran data yang kecil membuatnya sangat ringan dalam hal penggunaan memori dan CPU.

#### Keterbatasan Mini-AES

1.   **Keamanan Sangat Rendah:** Ini adalah kelemahan fundamental. Ukuran kunci hanya **16 bit**, menghasilkan ruang kunci yang sangat kecil (`2^16 = 65.536` kemungkinan). Jumlah ini dapat di-*brute-force* dengan sangat cepat menggunakan komputasi modern.
2.   **Ukuran Blok Terlalu Kecil:** Ukuran blok **16-bit** tidak memadai untuk keamanan praktis.
      *   Dalam mode **ECB**, blok plaintext identik akan menghasilkan blok ciphertext identik, membocorkan pola data. Probabilitas pengulangan blok jauh lebih tinggi dibandingkan blok 128-bit.
      *    Meskipun mode **CBC** mengatasi masalah pola ECB, ukuran blok yang kecil secara inheren kurang aman.
3.   **Jumlah Ronde Terbatas:** Hanya **3 ronde** transformasi internal (tidak termasuk `AddRoundKey` awal). Jumlah ronde yang sedikit membatasi tingkat *diffusion* dan *confusion* yang dapat dicapai, tidak cukup untuk mengacak hubungan antara plaintext, ciphertext, dan kunci secara menyeluruh.
4.   **Tidak Praktis untuk Aplikasi Nyata:** Karena kelemahannya yang signifikan, Mini-AES **tidak boleh digunakan** untuk mengamankan data sensitif di dunia nyata. Kegunaannya terbatas pada tujuan edukasi dan demonstrasi.
5.   **Kompleksitas Operasi Terbatas:** Operasi seperti `MixColumns` di `GF(2^4)` dan `ShiftRows` pada matriks 2x2 secara inheren memberikan tingkat difusi yang lebih rendah per ronde dibandingkan operasi serupa di AES asli (`GF(2^8)`, matriks 4x4).

#### Keamanan dan Avalanche Effect

1.   **Keamanan:** Seperti telah dijelaskan, Mini-AES **tidak aman** untuk penggunaan praktis. Kerentanan utamanya adalah serangan **brute-force** pada ruang kunci **16-bit** yang trivial. Analisis kriptografi lain (seperti diferensial atau linear) juga kemungkinan besar jauh lebih mudah diterapkan pada Mini-AES dibandingkan AES standar karena kompleksitasnya yang rendah.

2.   **Avalanche Effect:**
      *   **Konsep:** Avalanche Effect adalah properti di mana perubahan kecil pada input (misalnya, satu bit pada plaintext atau kunci) menyebabkan perubahan besar dan acak pada output (idealnya sekitar 50% bit ciphertext berubah). Ini adalah indikator *diffusion* dan *confusion* yang baik.
      *   **Implementasi pada Mini-AES:** Algoritma kami dibuat secara khusus agar dapat menunjukkan Avalanche Effect. Kombinasi `SubNibbles` (non-linear), `ShiftRows` (permutasi), dan `MixColumns` (pencampuran) yang diulang dalam 3 ronde bertujuan menyebarkan perubahan input ke seluruh *state*. Log detail program dapat digunakan untuk mengamati penyebaran ini pada tiap ronde.
      *   **Efektivitas:** Meskipun Avalanche Effect dapat diamati, kekuatannya **terbatas** oleh **ukuran state yang kecil (16-bit)** dan **jumlah ronde yang sedikit (3)**.
      *   **Kesimpulan:** Mini-AES menunjukkan prinsip Avalanche Effect secara konseptual, namun efek tersebut tidak cukup kuat untuk memberikan jaminan keamanan praktis karena keterbatasan fundamental algoritma (ukuran kunci, ukuran blok, jumlah ronde).

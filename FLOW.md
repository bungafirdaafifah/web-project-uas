# Flow dan Logika Aplikasi KasKu — Manajemen Uang Kas Mahasiswa

Dokumen ini menjelaskan alur kerja (workflow) pengguna, alur data, serta logika otomatisasi sistem aplikasi **KasKu** sesuai dengan implementasi yang berjalan (`app.py`, `models.py`, `routes.py`). Seluruh modul dideskripsikan menggunakan Mermaid Diagram dan penjelasan logika bisnis.

---

## 1. Flow Utama & Autentikasi Pengguna
### A. Alur Pengunjung Umum (Public Guest Flow)
Pengunjung umum dapat mengakses landing page, Informasi Kas (termasuk mengirim pesan ke bendahara), serta Tentang & FAQ tanpa perlu login.

```mermaid
graph TD
    A[Mulai] --> B[Akses Landing Page /]
    B --> C{Pilih Menu?}
    C -->|Informasi Kas| D[Halaman Informasi Kas /informasi-kas]
    D --> D1{Pilih Tab?}
    D1 -->|Pembayaran Kas Mahasiswa| D2[Tabel Status Pembayaran per Semester]
    D1 -->|Ringkasan Keuangan Semester| D3[Total Pendapatan, Pengeluaran, Saldo]
    D1 -->|Hubungi Bendahara| D4[Form Kirim Pesan]
    D4 --> D5[POST /informasi-kas/kirim-pesan]
    D5 --> D6[Simpan ke Tabel PesanMasuk]
    D6 --> D[Flash: 'Pesan berhasil dikirim']
    C -->|Tentang & FAQ| E[Halaman Tentang /tentang]
    C -->|Login Admin| F[Halaman Login /dashboard/login]
    F --> G{Autentikasi Berhasil?}
    G -->|Ya| H[Redirect ke Dashboard Admin /dashboard]
    G -->|Tidak| F
```

### B. Alur Autentikasi & Session Administrator (Admin Session Flow)
Mengamankan seluruh route dashboard di bawah path `/dashboard/*` (kecuali `/dashboard/login`) menggunakan decorator `login_required`.

```mermaid
graph TD
    Start[Akses URL Dashboard] --> CheckSession{Apakah Session 'admin_id' Ada?}
    CheckSession -->|Ya| Allow[Izinkan Akses Halaman]
    CheckSession -->|Tidak| RedirectLogin[Flash: 'Silakan login terlebih dahulu' & Redirect ke /dashboard/login]
```

---

## 2. Alur Kerja Modul Aplikasi (Workflow per Modul)

### 1. Flow Dashboard Admin
Dashboard admin memuat ringkasan eksekutif keuangan kas mahasiswa beserta grafik Chart.js. Seluruh komponen diperbarui ketika admin memilih semester pada filter dropdown.

```mermaid
graph TD
    A[Admin Login Berhasil] --> B[Akses /dashboard]
    B --> C[Sistem Memuat Dashboard Default: Seluruh Semester]
    C --> D[Hitung Stat Cards & Data Grafik untuk Seluruh Semester]
    D --> E[Tampilkan Stat Cards:
           1. Jumlah Mahasiswa Aktif
           2. Total Pendapatan Kas
           3. Total Pengeluaran Kas
           4. Saldo Kas Bersih
           5. Jumlah Mahasiswa Lunas
           6. Jumlah Mahasiswa Belum Lunas]
    E --> E1[Render Grafik Chart.js: Pendapatan vs Pengeluaran per Semester & Status Kelunasan]
    E1 --> F[Tampilkan Dropdown Filter Semester & Quick Access: Kelola Data / Kelola Website / Pesan / Pengaturan]
    F --> G{Admin Memilih Semester dari Dropdown?}
    G -->|Ya| H[Kirim Parameter semester_id via GET]
    H --> I[Sistem Memfilter Transaksi & Data Mahasiswa untuk Semester Terpilih]
    I --> J[Perbarui Stat Cards untuk Semester Terpilih]
    J --> F
    G -->|Tidak / Reset| L[Kembali ke Tampilan Akumulasi Seluruh Semester]
    L --> F
```

### 2. Flow CRUD Mahasiswa
Modul manajemen mahasiswa mencakup pendaftaran data, pembaruan, penghapusan, pencarian, dan navigasi ke detail pembayaran.

```mermaid
graph TD
    A[Mulai] --> B{Pilih Aksi Mahasiswa}

    B -->|Tambah Mahasiswa| C[Buka Form Tambah Mahasiswa]
    C --> D[Admin Input NIM, Nama, Kelas, Status Aktif/Nonaktif]
    D --> E[Klik Simpan]
    E --> F{Validasi: NIM/Nama Kosong atau NIM Duplikat?}
    F -->|Ya| G[Flash: 'NIM/Nama wajib diisi' atau 'NIM sudah terdaftar']
    G --> C
    F -->|Tidak| H[Simpan Data Mahasiswa ke Database]
    H --> I[Flash: 'Mahasiswa berhasil ditambahkan']
    I --> J[Redirect ke Daftar Mahasiswa]

    B -->|Edit Mahasiswa| K[Buka Form Edit Mahasiswa]
    K --> L[Admin Ubah NIM, Nama, Kelas, atau Status]
    L --> M[Klik Simpan]
    M --> N{Validasi NIM/Nama Valid & Tidak Duplikat?}
    N -->|Tidak| O[Flash: 'Validasi gagal!']
    O --> K
    N -->|Ya| P[Update Data di Database]
    P --> Q[Flash: 'Data mahasiswa berhasil diperbarui']
    Q --> J

    B -->|Hapus Mahasiswa| R[Klik Hapus Mahasiswa]
    R --> S{Konfirmasi Hapus?}
    S -->|Ya| T[Hapus Mahasiswa & Seluruh Riwayat Pembayaran Terkait — cascade delete]
    T --> U[Flash: 'Mahasiswa berhasil dihapus']
    U --> J
    S -->|Tidak| J

    B -->|Detail Mahasiswa| V[Akses Detail Mahasiswa /dashboard/pembayaran/detail/id]
    V --> W[Muat Biodata, Dropdown Semester & Bulan, Checkbox Pembayaran, Ringkasan Progress]
    W --> X[Tampilkan Halaman Detail]

    B -->|Pencarian Mahasiswa| Y[Ketik NIM/Nama pada Kolom Pencarian]
    Y --> Z[Sistem Memfilter Daftar Mahasiswa dengan SQL LIKE %query%]
    Z --> AA[Tampilkan Hasil Pencarian]
```

### 3. Flow CRUD Semester
Modul untuk mengelola data semester secara dinamis, termasuk pengaturan daftar bulan pembayaran, nominal per bulan/minggu, dan jumlah minggu per bulan.

```mermaid
graph TD
    A[Mulai] --> B{Pilih Aksi Semester}

    B -->|Tambah Semester| C[Buka Form Tambah Semester]
    C --> D[Admin Input: Nama Semester, Tahun Akademik, Nominal/Bulan, Nominal/Minggu, Jumlah Minggu, & Pilih Daftar Bulan]
    D --> E[Klik Simpan]
    E --> F{Validasi: Kolom Kosong / Nama Semester Duplikat / Bulan Belum Dipilih?}
    F -->|Ya| G[Flash: 'Kolom wajib diisi' / 'Semester sudah terdaftar' / 'Pilih minimal satu bulan']
    G --> C
    F -->|Tidak| H[Simpan Semester & Inisialisasi Daftar Bulan Terurut ke Database]
    H --> I[Flash: 'Semester berhasil dibuat']
    I --> J[Redirect ke Daftar Semester]

    B -->|Edit Semester| K[Buka Form Edit Semester]
    K --> L[Admin Ubah Tahun Akademik dan/atau Status Aktif]
    L --> M[Klik Simpan]
    M --> N{Tahun Akademik Diisi?}
    N -->|Tidak| O[Flash: 'Tahun akademik wajib diisi']
    O --> K
    N -->|Ya| P[Update Tahun Akademik & Status Aktif di Database]
    P --> Q[Flash: 'Semester berhasil diperbarui']
    Q --> J

    B -->|Hapus Semester| R[Klik Hapus Semester]
    R --> S{Apakah Semester Memiliki Riwayat Pembayaran?}
    S -->|Ya| T[Tolak Penghapusan & Flash: 'Semester tidak dapat dihapus karena memiliki riwayat transaksi pembayaran']
    T --> J
    S -->|Tidak| U[Hapus Semester beserta Data Bulan Terkait — cascade delete]
    U --> V[Flash: 'Semester berhasil dihapus']
    V --> J
```

### 4. Flow Pembayaran Kas Mahasiswa & Rekap Pembayaran
Pembayaran uang kas dilakukan lewat Detail Mahasiswa: pilih semester, lalu pilih bulan, barulah sistem merender checkbox mingguan. Seluruh transaksi dapat dipantau ringkas di menu Kelola Pembayaran, dan ditelusuri detail di Rekap Pembayaran.

```mermaid
graph TD
    subgraph Landing & Kelola Pembayaran
    L1[Akses Pembayaran Kas /dashboard/pembayaran] --> L2{Pilih: Kelola atau Rekap?}
    L2 -->|Kelola| K1[Pilih Semester]
    K1 --> K2[Tampilkan Progress & Status Belum/Dicicil/Lunas Tiap Mahasiswa Aktif]
    K2 --> K3[Klik Mahasiswa untuk Buka Detail]
    end

    subgraph Pembayaran Mahasiswa
    P1[Detail Mahasiswa /dashboard/pembayaran/detail/id] --> P2[Admin Memilih Semester]
    P2 --> P3[Admin Memilih Bulan Pembayaran]
    P3 --> P4[Tampilkan Checkbox Mingguan sesuai Jumlah Minggu Semester]
    P4 --> P5[Admin Centang/Hapus Centang Checkbox Mingguan]
    P5 --> P6[Klik Simpan Pembayaran — POST /dashboard/pembayaran/simpan/id]
    P6 --> P7[Untuk Tiap Minggu: Simpan Jika Dicentang & Belum Ada, Hapus Jika Tidak Dicentang & Sudah Ada]
    P7 --> P8[Flash: 'Pembayaran berhasil disimpan']
    P8 --> P9[Redirect ke Detail dengan Ringkasan Target, Terbayar, Sisa, Status, Persentase Terbaru]
    end

    subgraph Rekap Pembayaran
    L2 -->|Rekap| R1[Akses /dashboard/rekap-pembayaran]
    R1 --> R2[Tampilkan Riwayat Seluruh Transaksi Pembayaran]
    R2 --> R3[Admin Pilih Filter Dropdown: Semester dan/atau Mahasiswa]
    R3 --> R4[Sistem Memfilter Transaksi & Menghitung Total Nominal Terfilter]
    R4 --> R5[Perbarui Tampilan Tabel]
    end

    P8 -->|Menambah Data| R2
```

### 5. Flow Pendapatan Kas (Otomatis, Tanpa Form)
Pendapatan kas murni berasal dari agregasi transaksi Pembayaran. Tidak ada halaman atau form khusus untuk menambah, mengedit, maupun menghapus pendapatan secara manual.

> [!WARNING]
> **PENTING**: Tidak ada route atau tombol CRUD untuk modul Pendapatan. Nilainya selalu dihitung otomatis (`SUM(Pembayaran.nominal)`) dan ditampilkan di Dashboard, Informasi Kas (tab Ringkasan Keuangan Semester), dan Rekap Pembayaran — demi menjaga integritas data keuangan.

```mermaid
graph TD
    A[Pembayaran Kas Disimpan via Checkbox Mingguan] --> B[Sistem Menghitung Total Pendapatan: SUM nominal Pembayaran]
    B --> C[Hasil Agregasi Tersedia Real-Time]
    C --> D[Ditampilkan di Dashboard /dashboard]
    C --> E[Ditampilkan di Informasi Kas /informasi-kas — Tab Ringkasan Keuangan Semester]
    C --> F[Ditampilkan di Rekap Pembayaran /dashboard/rekap-pembayaran]
```

### 6. Flow Pengeluaran Kas (Landing, Riwayat, & CRUD dengan Validasi Saldo)
Pencatatan pengeluaran kas dilakukan admin dengan validasi saldo yang mencegah nominal pengeluaran melebihi saldo kas bersih (Total Pendapatan − Total Pengeluaran), baik untuk penambahan maupun pembaruan data.

```mermaid
graph TD
    L1[Akses Pengeluaran Kas /dashboard/pengeluaran] --> L2{Pilih: Kelola atau Riwayat?}
    L2 -->|Riwayat| RW1[Filter Riwayat Pengeluaran per Semester]
    RW1 --> RW2[Tampilkan Daftar & Total Nominal Terfilter]

    L2 -->|Kelola| B{Pilih Aksi Pengeluaran}

    B -->|Tambah Pengeluaran| C[Admin Mengisi Form Tambah Pengeluaran]
    C --> D[Klik Simpan Pengeluaran]
    D --> E[Hitung Saldo Kas Terkini: Total Pendapatan - Total Pengeluaran]
    E --> F{Apakah Nominal Pengeluaran <= Saldo Kas?}
    F -->|Ya| G[Simpan ke Database]
    G --> H[Saldo Kas Otomatis Berkurang di Dashboard]
    G --> I[Flash: 'Pengeluaran berhasil ditambahkan']
    G --> Z[Redirect ke Kelola Pengeluaran]
    F -->|Tidak| J[Tolak Transaksi & Flash Error: 'Saldo kas tidak mencukupi!']
    J --> C

    B -->|Edit Pengeluaran| K[Buka Form Edit Pengeluaran]
    K --> L[Admin Mengubah Data Pengeluaran]
    L --> M[Klik Simpan]
    M --> N[Hitung Saldo Kas Penyesuaian: Saldo Saat Ini + Nominal Pengeluaran Lama]
    N --> O{Apakah Nominal Edit <= Saldo Kas Penyesuaian?}
    O -->|Ya| P[Simpan Pembaruan ke Database]
    P --> Q[Flash: 'Pengeluaran berhasil diperbarui']
    Q --> Z
    O -->|Tidak| R[Tolak Transaksi & Flash Error: 'Saldo kas tidak mencukupi untuk penyesuaian!']
    R --> K

    B -->|Hapus Pengeluaran| S[Klik Hapus Pengeluaran]
    S --> T{Konfirmasi Hapus?}
    T -->|Ya| U[Hapus Pengeluaran dari Database]
    U --> V[Saldo Kas Otomatis Bertambah Kembali]
    V --> W[Flash: 'Pengeluaran berhasil dihapus. Saldo kas telah dipulihkan']
    W --> Z
    T -->|Tidak| Z
```

### 7. Flow Kelola Website (Beranda & Tentang/FAQ)
Admin mengelola konten dinamis yang ditampilkan di halaman publik (Landing Page dan Tentang & FAQ) tanpa perlu mengubah kode.

```mermaid
graph TD
    A[Akses Kelola Website /dashboard/kelola-website] --> B{Pilih: Beranda atau Tentang?}

    B -->|Beranda| C[Form Judul & Deskripsi Hero + Upload Logo]
    C --> D[Klik Simpan]
    D --> E{Judul & Deskripsi Terisi?}
    E -->|Tidak| F[Flash: 'Judul dan deskripsi wajib diisi']
    F --> C
    E -->|Ya| G[Simpan ke Pengaturan hero_judul/hero_deskripsi, Simpan Logo Baru Jika Diunggah]
    G --> H[Flash: 'Konten Beranda berhasil diperbarui']
    H --> C
    C --> I[Kelola Fitur Unggulan: Tambah / Edit / Hapus Icon & Teks]
    I --> C

    B -->|Tentang| J[Form Deskripsi, Tujuan, Cara Kerja]
    J --> K[Klik Simpan]
    K --> L{Seluruh Kolom Terisi?}
    L -->|Tidak| M[Flash: 'Seluruh kolom konten Tentang wajib diisi']
    M --> J
    L -->|Ya| N[Simpan ke KontenTentang]
    N --> O[Flash: 'Konten Tentang berhasil diperbarui']
    O --> J
    J --> P[Kelola FAQ: Tambah / Edit / Hapus Pertanyaan & Jawaban]
    P --> J
```

### 8. Flow Pesan Masuk (Hubungi Bendahara)
Menampilkan dan mengelola pesan yang dikirim pengunjung lewat tab "Hubungi Bendahara" di halaman Informasi Kas.

```mermaid
graph TD
    A[Pengunjung Kirim Pesan di /informasi-kas] --> B[Tersimpan ke Tabel PesanMasuk, Status: Belum Dibaca]
    B --> C[Admin Akses Pesan /dashboard/pesan]
    C --> D[Tampilkan Daftar Pesan & Jumlah Belum Dibaca]
    D --> E{Aksi Admin}
    E -->|Lihat Detail| F[Buka Detail Pesan]
    F --> G[Status Otomatis Berubah Menjadi 'Sudah Dibaca']
    G --> D
    E -->|Tandai| H[Toggle Status Belum Dibaca <-> Sudah Dibaca]
    H --> D
    E -->|Hapus| I[Hapus Pesan dari Database]
    I --> D
```

### 9. Flow Pengaturan Sistem (Dinamis & Historis)
Admin dapat mengatur parameter kas default serta kredensial akunnya sendiri dalam satu halaman dengan dua formulir terpisah.

```mermaid
graph TD
    A[Akses Pengaturan /dashboard/pengaturan] --> B{Form Mana yang Disimpan?}

    B -->|Pengaturan Umum| C[Form: Nama Organisasi, Logo, Nominal/Bulan, Nominal/Minggu, Jumlah Minggu, Deskripsi]
    C --> D[Klik Simpan]
    D --> E{Kolom Wajib Terisi?}
    E -->|Tidak| F[Flash: 'Seluruh kolom wajib diisi']
    F --> C
    E -->|Ya| G{Ada Upload Logo Baru?}
    G -->|Ya| H{Format .png/.jpg Valid?}
    H -->|Tidak| I[Flash: 'Format file logo tidak valid!']
    I --> C
    H -->|Ya| J[Simpan File Logo ke static/img]
    G -->|Tidak| K[Lewati Upload Logo]
    J --> L[Simpan Pengaturan ke Database]
    K --> L
    L --> M[Flash: 'Pengaturan sistem berhasil diperbarui. Berlaku untuk semester baru']
    M --> C

    B -->|Kredensial Admin| N[Form: Username, Password Lama, Password Baru, Konfirmasi]
    N --> O[Klik Simpan]
    O --> P{Username Kosong / Sudah Dipakai Admin Lain?}
    P -->|Ya| Q[Flash Error & Batalkan]
    Q --> N
    P -->|Tidak| R{Password Baru Diisi?}
    R -->|Ya| S{Password Lama Cocok & Konfirmasi Sama?}
    S -->|Tidak| T[Flash: 'Password lama salah' / 'Konfirmasi tidak cocok']
    T --> N
    S -->|Ya| U[Hash Password Baru — werkzeug.security]
    R -->|Tidak| V[Lewati Perubahan Password]
    U --> W[Simpan Username & Password ke Database]
    V --> W
    W --> X[Flash: 'Kredensial admin berhasil diperbarui']
    X --> N
```

### 10. Flow Logout
Mengakhiri sesi admin secara aman dan membersihkan seluruh state otentikasi.

```mermaid
graph TD
    A[Admin di Dashboard] --> B[Klik Tombol Logout]
    B --> C[Sistem Memproses Request Logout]
    C --> D[session.clear — Hapus admin_id, admin_username, admin_nama]
    D --> E[Flash: 'Anda berhasil logout. Sampai jumpa!']
    E --> F[Redirect ke Halaman Login /dashboard/login]
    F --> G[Seluruh URL /dashboard/* Kembali Terkunci dari Akses Tanpa Login]
```

---

## 3. Flow Keseluruhan Sistem (Main System Architecture)

Diagram berikut menjelaskan hubungan antarmuka, proses CRUD, perhitungan dinamis saldo, hingga sistem konten yang melingkupi seluruh modul aplikasi:

```mermaid
graph TD
    %% Public
    LP[Landing Page /] -->|Akses| IK[Informasi Kas /informasi-kas]
    LP -->|Akses| TT[Tentang & FAQ /tentang]
    LP -->|Akses Login| LG[Login Admin /dashboard/login]
    IK -->|Kirim Pesan| PSM[(Tabel PesanMasuk)]

    LG -->|Autentikasi Berhasil| DB[Dashboard Admin /dashboard]

    %% Dashboard Quick Access
    DB -->|Navigasi| KD[Kelola Data]
    DB -->|Navigasi| KW[Kelola Website]
    DB -->|Navigasi| PSN[Pesan]
    DB -->|Navigasi| SET[Pengaturan]
    DB -->|Keluar| LGO[Logout]

    %% Kelola Data
    KD -->|Kartu| MHS[Manajemen Mahasiswa CRUD]
    KD -->|Kartu| SEM[Manajemen Semester CRUD]
    KD -->|Kartu| PMB[Pembayaran Kas: Kelola & Rekap]
    KD -->|Kartu| PGL[Pengeluaran Kas: Kelola & Riwayat]

    %% Kelola Website
    KW -->|Kartu| BRD[Beranda: Hero & Fitur Unggulan]
    KW -->|Kartu| TTG[Tentang: Deskripsi & FAQ]
    BRD -->|Update Konten| LP
    TTG -->|Update Konten| TT

    %% Relationships & Automations
    MHS -->|Lihat Detail| DTL[Detail Mahasiswa]
    DTL -->|Pilih Semester & Bulan| SEM
    SEM -->|Memiliki Relasi| BUL[Daftar Bulan Pembayaran]
    BUL -->|Centang Checkbox Mingguan| TRX[(Tabel Pembayaran)]

    TRX -->|Otomatis Hitung Pendapatan| SAL[(Saldo Kas = Pendapatan - Pengeluaran)]
    PGL -->|Simpan Pengeluaran, Validasi Saldo| SAL
    SAL -->|Ditampilkan| DB
    SAL -->|Ditampilkan| IK

    TRX -->|Sumber Data| PMB
    PSM -->|Sumber Data| PSN

    SET -->|Setelan Default Berlaku untuk| SEM
    SET -->|Ubah Kredensial| LG

    LGO -->|Hapus Session & Redirect| LG
```

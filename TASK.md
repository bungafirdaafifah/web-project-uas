# Panduan Instalasi, Menjalankan Aplikasi & Checklist Fitur

Dokumen ini berisi daftar dependensi (library), panduan menyiapkan virtual environment (venv) Python, instruksi menjalankan aplikasi, serta checklist fitur yang sudah terpasang di aplikasi **KasKu**, mengikuti urutan: **UI Depan Publik -> Autentikasi -> Dashboard Admin -> Kelola Data & Website -> Sentuhan Akhir**.

---

## 1. Spesifikasi Dependensi & Library

Dependensi berikut tercantum di file `requirements.txt`:
* **Flask** — Framework utama
* **Flask-SQLAlchemy** — ORM untuk interaksi database Supabase (PostgreSQL)
* **psycopg2-binary** — Driver PostgreSQL untuk koneksi ke Supabase
* **Werkzeug** — Keamanan password hash & upload file (bagian dari Flask)
* **Pillow** — Untuk pengelolaan/validasi file gambar (logo, dsb.)
* **python-dotenv** — Memuat environment variables dari file `.env` (`SECRET_KEY`, `DATABASE_URL`)

---

## 2. Panduan Setup & Cara Menjalankan Aplikasi

Ikuti langkah-langkah berikut di terminal (PowerShell / Command Prompt) untuk menjalankan aplikasi secara lokal:

### Langkah 1: Buat Virtual Environment (venv)
```bash
python -m venv venv
```

### Langkah 2: Aktifkan Virtual Environment
* **Windows (PowerShell)**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
* **Windows (Command Prompt)**:
  ```cmd
  .\venv\Scripts\activate.bat
  ```
* **Linux/macOS**:
  ```bash
  source venv/bin/activate
  ```

### Langkah 3: Install Dependensi
```bash
pip install -r requirements.txt
```

### Langkah 4: Konfigurasi Supabase
Salin `.env.example` menjadi `.env`, lalu isi `DATABASE_URL` dengan connection string **Connection pooling** Supabase (Transaction mode, port `6543`) dan `SECRET_KEY` dengan string acak:
```bash
cp .env.example .env
```
Tanpa `DATABASE_URL`, aplikasi jatuh ke SQLite lokal untuk pengembangan cepat.

### Langkah 5: Inisialisasi Tabel (Pertama kali running)
Saat pertama dijalankan, aplikasi otomatis membuat seluruh tabel di database Supabase, akun admin bawaan, serta konten publik awal (Fitur Unggulan, Tentang, FAQ):
* Username Default: `admin`
* Password Default: `admin123`

### Langkah 6: Jalankan Aplikasi
```bash
python app.py
```
Aplikasi akan berjalan di `http://127.0.0.1:5000/`.

---

## 3. Checklist Fitur Aplikasi

### Fase 1: Persiapan Awal
- [x] Buat file `requirements.txt` dengan daftar dependensi.
- [x] Buat file `config.py` untuk setup konfigurasi Flask, secret key, database URI, dan folder upload.
- [x] Implementasikan seluruh model database SQLAlchemy dalam satu file `models.py`, dengan relasi **Semester → Bulan → Pembayaran** yang jelas:
  - [x] `Admin` (kredensial & login)
  - [x] `Mahasiswa`
  - [x] `Semester` (status aktif, nominal per bulan/minggu, jumlah minggu pembayaran)
  - [x] `Bulan` (relasi FK ke Semester)
  - [x] `Pembayaran` (relasi FK ke Mahasiswa, Semester, dan Bulan; unique constraint per minggu)
  - [x] `Pengeluaran`
  - [x] `PesanMasuk` (form "Hubungi Bendahara")
  - [x] `FiturUnggulan`, `KontenTentang`, `FAQ`, `Pengaturan` (konten dinamis halaman publik)
- [x] Implementasikan seluruh route/blueprint Flask dalam satu file `routes.py`.

### Fase 2: UI Depan (Public Interface)
Halaman depan menampilkan data yang dapat disesuaikan secara dinamis oleh admin melalui menu Kelola Website & Pengaturan di Dashboard.
- [x] Buat template utama `templates/base.html` dengan navbar responsif, footer, integrasi Bootstrap 5, dan flash message.
- [x] **Landing Page (`templates/public/home.html`)** — nama organisasi, logo, judul & deskripsi hero, dan daftar Fitur Unggulan (data dinamis dari `Pengaturan` & `FiturUnggulan`).
- [x] **Informasi Kas (`templates/public/informasi_kas.html`)** — 3 tab:
  - [x] Tab Pembayaran Kas Mahasiswa (status pembayaran read-only per semester).
  - [x] Tab Ringkasan Keuangan Semester (total pendapatan, pengeluaran, saldo, rincian pengeluaran).
  - [x] Tab Hubungi Bendahara (form kontak tersimpan ke tabel `PesanMasuk`).
- [x] **Tentang & FAQ (`templates/public/tentang.html`)** — deskripsi, tujuan, cara kerja, dan FAQ interaktif (data dinamis dari `KontenTentang` & `FAQ`).
- [x] **Desain & Aset**:
  - [x] File stylesheet `static/css/style.css` untuk estetika UI publik & dashboard (premium, modern, dark mode).
  - [x] Gambar default (`logo.png`, `background.jpg`, `default-profile.png`) di folder `static/img/`.

### Fase 3: Autentikasi Admin & Logout
- [x] **Halaman Login Admin (`templates/login.html`)** — form login dengan validasi input.
- [x] Blueprint Auth (`routes.py — auth_bp`):
  - [x] Login menggunakan Session Flask (`session['admin_id']`).
  - [x] Penyimpanan & verifikasi password menggunakan hashing (`werkzeug.security`).
  - [x] Decorator `@login_required` untuk melindungi seluruh route dashboard `/dashboard/*`.
- [x] **Fungsi Logout**:
  - [x] Hapus session admin (`session.clear()`).
  - [x] Tampilkan flash message sukses logout.
  - [x] Redirect kembali ke halaman login admin.

### Fase 4: Dashboard Admin
- [x] **Dashboard Index (`templates/dashboard/index.html`)**:
  - [x] Filter ringkasan berdasarkan semester lewat dropdown.
  - [x] Stat cards: Jumlah Mahasiswa Aktif, Total Pendapatan Kas, Total Pengeluaran Kas, Saldo Kas Bersih, Jumlah Mahasiswa Lunas, Jumlah Mahasiswa Belum Lunas (akumulasi / per semester terfilter).
  - [x] Grafik pendapatan vs pengeluaran & grafik status kelunasan mahasiswa (integrasi Chart.js langsung di halaman dashboard).
  - [x] Menu Quick Access: Kelola Data, Kelola Website, Pesan, Pengaturan.
- [x] **Manajemen Semester (`templates/pengaturan/semester.html` & CRUD)**:
  - [x] Tambah semester: nama, tahun akademik, nominal per bulan, nominal per minggu, jumlah minggu, serta daftar bulan pembayaran (checklist dinamis).
  - [x] Validasi: nama semester tidak boleh duplikat, minimal satu bulan pembayaran dipilih.
  - [x] Edit semester: tahun akademik & status aktif.
  - [x] Hapus semester: ditolak apabila semester sudah memiliki riwayat transaksi pembayaran.
- [x] **Manajemen Mahasiswa (`templates/mahasiswa/mahasiswa.html` & CRUD)**:
  - [x] Tambah mahasiswa (NIM, Nama, Kelas, Status Aktif/Nonaktif).
  - [x] Lihat & edit data mahasiswa (validasi NIM tidak boleh duplikat).
  - [x] Hapus data mahasiswa (beserta riwayat pembayaran terkait, `cascade delete`).
  - [x] Fitur pencarian berdasarkan NIM atau Nama.
- [x] **Pembayaran Kas (`templates/keuangan/pembayaran_landing.html`, `pembayaran_kelola.html`)**:
  - [x] Landing dengan 2 pilihan: Kelola atau Rekap Pembayaran.
  - [x] Kelola: pilih semester → tampilkan progress & status (Belum/Dicicil/Lunas) tiap mahasiswa aktif.
- [x] **Detail & Pembayaran Mahasiswa (`templates/mahasiswa/detail_mahasiswa.html`)**:
  - [x] Biodata mahasiswa & dropdown pilihan semester.
  - [x] Dropdown pilihan bulan — checkbox pembayaran mingguan dirender setelah bulan dipilih.
  - [x] Checkbox mingguan (nominal default Rp5.000/minggu, 3 minggu/bulan = Rp15.000/bulan), tersimpan/terhapus otomatis sesuai centang.
  - [x] Ringkasan pembayaran (Target, Total terbayar, Sisa, Status, Persentase progress).
- [x] **Rekap Pembayaran Kas (`templates/keuangan/rekap_pembayaran.html`)**:
  - [x] Riwayat seluruh transaksi pembayaran (mahasiswa, semester, bulan, minggu, tanggal, nominal).
  - [x] Filter berdasarkan semester dan/atau mahasiswa.
- [x] **Pengeluaran Kas (`templates/keuangan/pengeluaran_landing.html`, `pengeluaran.html`, `pengeluaran_riwayat.html` & CRUD)**:
  - [x] Landing dengan 2 pilihan: Kelola atau Riwayat.
  - [x] Tambah pengeluaran: tanggal, kategori, keperluan, nominal, keterangan — dengan **validasi saldo** (nominal ≤ saldo kas bersih).
  - [x] Edit pengeluaran — validasi saldo kas penyesuaian.
  - [x] Hapus pengeluaran — saldo kas otomatis pulih kembali.
  - [x] Riwayat pengeluaran dengan filter semester.
- [x] **Pendapatan Kas** — tidak memiliki halaman/form tersendiri; dihitung otomatis dari seluruh transaksi `Pembayaran` dan ditampilkan pada Dashboard, Informasi Kas, dan Rekap Pembayaran demi menjaga integritas data keuangan.

### Fase 5: Kelola Data, Kelola Website & Pesan
- [x] **Kelola Data (`templates/website/kelola_data.html`)** — landing 4 kartu navigasi cepat: Mahasiswa, Semester, Pembayaran Kas, Pengeluaran Kas.
- [x] **Kelola Website (`templates/website/website_index.html`)** — landing 2 kartu:
  - [x] **Beranda (`website_beranda.html`)** — ubah judul & deskripsi hero, unggah logo, serta CRUD daftar Fitur Unggulan (icon emoji + teks).
  - [x] **Tentang (`website_tentang.html`)** — ubah deskripsi, tujuan, cara kerja, serta CRUD daftar FAQ.
- [x] **Pesan (`templates/pesan/pesan_masuk.html`, `detail_pesan.html`)**:
  - [x] Daftar pesan masuk dari form "Hubungi Bendahara" beserta jumlah yang belum dibaca.
  - [x] Lihat detail pesan (otomatis menandai "Sudah Dibaca").
  - [x] Toggle status Belum/Sudah Dibaca.
  - [x] Hapus pesan.
- [x] **Pengaturan (`templates/pengaturan/pengaturan.html`)**:
  - [x] Form Pengaturan Umum — nama organisasi, logo (upload file), nominal kas per bulan/minggu default, jumlah minggu, deskripsi. Perubahan hanya berlaku untuk semester baru; semester lama tetap mempertahankan konfigurasi historisnya.
  - [x] Form Kredensial Admin — ubah username & password (password baru wajib verifikasi password lama, disimpan dalam bentuk hash).

### Fase 6: Sentuhan Akhir & Validasi
- [x] Validasi input form client-side menggunakan JavaScript (`static/js/validasi.js`).
- [x] Validasi server-side pada seluruh route Flask.
- [x] Integrasi Flash Message Bootstrap untuk semua aksi sukses/gagal.
- [x] Penanganan halaman error 404 (`templates/404.html`).

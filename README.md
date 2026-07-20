# KasKu — Aplikasi Manajemen Uang Kas Mahasiswa Berbasis Web

Nama: Bunga Firda Afifah 
NIM : 301250024
Kelas : 2B

KasKu adalah sistem informasi berbasis web untuk mengelola, mencatat, dan menyajikan laporan keuangan kas mahasiswa. Aplikasi ini memiliki halaman publik (landing page, informasi kas, tentang & FAQ) yang kontennya dapat diatur secara dinamis oleh admin, serta dashboard administrator yang dilindungi autentikasi berbasis session.

---

## 🚀 Fitur Utama

### 1. Halaman Depan (Public UI)
* **Landing Page (`/`)** — Beranda menampilkan nama organisasi, logo, judul & deskripsi hero, serta daftar fitur unggulan. Seluruh konten ini diambil dari data yang diatur admin lewat menu **Kelola Website**.
* **Informasi Kas (`/informasi-kas`)** — Halaman publik dengan 3 tab:
  1. **Pembayaran Kas Mahasiswa** — tabel status pembayaran mingguan tiap mahasiswa aktif untuk semester terpilih (read-only).
  2. **Ringkasan Keuangan Semester** — total pendapatan, total pengeluaran, saldo kas, dan rincian pengeluaran per semester.
  3. **Hubungi Bendahara** — formulir kontak yang tersimpan ke database dan bisa dibaca admin lewat menu Pesan.
* **Tentang & FAQ (`/tentang`)** — deskripsi aplikasi, tujuan, cara kerja, dan daftar FAQ (semuanya konten dinamis, dapat diedit admin).
* **Login Admin (`/dashboard/login`)** — akses masuk administrator menggunakan username dan password.
* **Halaman 404** — ditampilkan otomatis untuk URL yang tidak ditemukan.

### 2. Dashboard Admin (`/dashboard`)
* **Ringkasan Kas (Stat Cards)** — jumlah mahasiswa aktif, total pendapatan, total pengeluaran, saldo kas bersih, jumlah mahasiswa lunas, dan jumlah mahasiswa belum lunas. Semua angka bisa difilter per semester lewat dropdown, atau ditampilkan akumulasi seluruh semester.
* **Grafik (Chart.js)** — grafik perbandingan pendapatan vs pengeluaran per semester, dan grafik status kelunasan mahasiswa, langsung terintegrasi di halaman dashboard.
* **Kelola Data** (landing 4 kartu) — pintu masuk ke:
  * **Manajemen Mahasiswa (CRUD)** — tambah, edit, hapus, detail, dan cari mahasiswa berdasarkan NIM/Nama.
  * **Manajemen Semester (CRUD)** — tambah semester baru (nama, tahun akademik, nominal per bulan, nominal per minggu, jumlah minggu, daftar bulan pembayaran); edit hanya tahun akademik & status aktif; hapus ditolak jika semester sudah memiliki riwayat pembayaran.
  * **Pembayaran Kas** — landing dengan pilihan **Kelola** (pilih semester → lihat progress & status tiap mahasiswa) atau **Rekap Pembayaran** (riwayat transaksi dengan filter semester & mahasiswa).
  * **Pengeluaran Kas** — landing dengan pilihan **Kelola** (CRUD pengeluaran dengan validasi agar nominal tidak melebihi saldo kas) atau **Riwayat** (daftar pengeluaran dengan filter semester).
* **Detail & Pembayaran Mahasiswa** — biodata, dropdown pilihan semester lalu bulan, checkbox pembayaran mingguan dinamis (nominal default Rp5.000/minggu, 3 minggu/bulan), serta ringkasan target, total terbayar, sisa, status, dan persentase progress.
* **Kelola Website** (landing 2 kartu) — mengatur konten publik:
  * **Beranda** — judul & deskripsi hero, logo, dan daftar Fitur Unggulan (tambah/edit/hapus).
  * **Tentang** — deskripsi, tujuan, cara kerja, dan daftar FAQ (tambah/edit/hapus).
* **Pesan** — daftar pesan masuk dari form "Hubungi Bendahara", lihat detail, tandai sudah/belum dibaca, hapus.
* **Pengaturan** — dua formulir dalam satu halaman:
  * Pengaturan umum: nama organisasi, logo, nominal kas per bulan/minggu default, jumlah minggu, deskripsi (berlaku untuk semester baru; semester lama tetap memakai konfigurasi historisnya).
  * Kredensial admin: ubah username dan password (password baru wajib verifikasi password lama).
* **Logout** — menghapus session admin sehingga seluruh halaman dashboard kembali terkunci.

---

## 🛠️ Teknologi yang Digunakan

* **Bahasa Pemrograman**: Python 3.x
* **Web Framework**: Flask (struktur Blueprint)
* **Database**: SQLite (Relasional)
* **ORM**: Flask-SQLAlchemy
* **Autentikasi**: Flask Session + Password hashing (`werkzeug.security`)
* **Frontend**: HTML5, CSS3 (Custom Vanilla CSS), JavaScript (Vanilla ES6), Bootstrap 5, Bootstrap Icons, Chart.js

---

## 📁 Struktur Proyek

Struktur folder berikut sesuai dengan kondisi proyek saat ini (model & route sudah digabung menjadi satu file masing-masing, dan template dikelompokkan per modul):

```text
Web_Project_UAS/
│
├── app.py                     # Entry point aplikasi Flask (factory, seed data awal, error handler 404)
├── config.py                  # Konfigurasi aplikasi (secret key, database URI, folder upload)
├── models.py                  # Seluruh model database SQLAlchemy (Admin, Mahasiswa, Semester, Bulan,
│                               #   Pembayaran, Pengeluaran, PesanMasuk, FiturUnggulan, KontenTentang, FAQ, Pengaturan)
├── routes.py                  # Seluruh blueprint & route Flask (public, auth, dashboard, semester,
│                               #   mahasiswa, pembayaran, rekap, pengeluaran, pengaturan, pesan,
│                               #   kelola_data, website)
├── requirements.txt           # Daftar dependensi Python
├── README.md                  # Dokumentasi aplikasi
├── TASK.md                    # Checklist pengerjaan proyek
├── FLOW.md                    # Alur kerja & logika bisnis aplikasi
├── .gitignore                 # File yang diabaikan Git
├── kas_management.db          # Database SQLite (terbuat otomatis saat pertama run)
│
├── templates/
│   ├── base.html               # Template utama (navbar, footer, flash message)
│   ├── base_dashboard.html     # Template dashboard (sidebar + area konten)
│   ├── login.html              # Halaman login admin
│   ├── 404.html                # Halaman error 404
│   │
│   ├── dashboard/
│   │   └── index.html          # Dashboard utama (stat cards, grafik, quick access)
│   │
│   ├── public/
│   │   ├── home.html           # Landing Page
│   │   ├── informasi_kas.html  # Informasi Kas (3 tab)
│   │   └── tentang.html        # Tentang & FAQ
│   │
│   ├── mahasiswa/
│   │   ├── mahasiswa.html          # Daftar & pencarian mahasiswa
│   │   ├── tambah_mahasiswa.html
│   │   ├── edit_mahasiswa.html
│   │   └── detail_mahasiswa.html   # Detail + checkbox pembayaran mingguan
│   │
│   ├── keuangan/
│   │   ├── pembayaran_landing.html   # Pilihan: Kelola / Rekap
│   │   ├── pembayaran_kelola.html    # Progress pembayaran per mahasiswa per semester
│   │   ├── rekap_pembayaran.html     # Riwayat transaksi pembayaran (filter semester/mahasiswa)
│   │   ├── pengeluaran_landing.html  # Pilihan: Kelola / Riwayat
│   │   ├── pengeluaran.html          # Kelola pengeluaran (list + saldo)
│   │   ├── pengeluaran_riwayat.html  # Riwayat pengeluaran (filter semester)
│   │   ├── tambah_pengeluaran.html
│   │   └── edit_pengeluaran.html
│   │
│   ├── pengaturan/
│   │   ├── semester.html         # Daftar semester
│   │   ├── tambah_semester.html
│   │   ├── edit_semester.html
│   │   └── pengaturan.html       # Pengaturan umum + kredensial admin
│   │
│   ├── pesan/
│   │   ├── pesan_masuk.html      # Daftar pesan "Hubungi Bendahara"
│   │   └── detail_pesan.html
│   │
│   └── website/
│       ├── kelola_data.html        # Landing Kelola Data (4 kartu)
│       ├── website_index.html      # Landing Kelola Website (2 kartu)
│       ├── website_beranda.html    # Edit konten hero & Fitur Unggulan
│       └── website_tentang.html    # Edit konten Tentang & FAQ
│
└── static/
    ├── css/
    │   └── style.css           # Styling seluruh halaman (publik & dashboard)
    │
    ├── js/
    │   └── validasi.js         # Validasi form sisi client (login, mahasiswa, semester, pengeluaran, dll.)
    │
    ├── img/
    │   ├── logo.png             # Logo default organisasi
    │   ├── background.jpg       # Background hero Landing Page
    │   └── default-profile.png  # Gambar profil default
    │
    └── uploads/
        └── profile/             # Folder penyimpanan unggahan terkait profil
```

---

## ⚙️ Petunjuk Instalasi & Cara Menjalankan

Ikuti langkah-langkah di bawah ini untuk menginstal Flask, dependensi, dan menjalankan aplikasi secara lokal.

### 1. Prasyarat (Prerequisites)
Pastikan Anda sudah menginstal Python 3 di komputer Anda. Anda bisa memverifikasinya melalui command prompt/terminal:
```bash
python --version
```

### 2. Membuat Virtual Environment (venv)
Membuat lingkungan virtual terisolasi untuk menghindari konflik paket antar-proyek:
```bash
python -m venv venv
```

### 3. Mengaktifkan Virtual Environment
* **Windows (PowerShell)**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
* **Windows (Command Prompt)**:
  ```cmd
  .\venv\Scripts\activate.bat
  ```
* **Linux / macOS**:
  ```bash
  source venv/bin/activate
  ```

### 4. Mengunduh & Menginstal Flask serta Dependensi
Setelah venv aktif, Anda dapat menginstal dependensi dengan dua cara:

* **Cara A (Menggunakan pip install langsung)**:
  ```bash
  pip install Flask Flask-SQLAlchemy Pillow python-dotenv
  ```
* **Cara B (Menggunakan requirements.txt)**:
  ```bash
  pip install -r requirements.txt
  ```

### 5. Inisialisasi Database & Menjalankan Aplikasi
Jalankan aplikasi utama Flask. Database SQLite `kas_management.db` akan dibuat secara otomatis jika belum ada, lengkap dengan akun admin bawaan dan konten publik awal (Fitur Unggulan, Tentang, FAQ):
```bash
python app.py
```
Akses aplikasi melalui browser Anda pada URL: **`http://127.0.0.1:5000/`**

### 6. Akun Administrator Bawaan (Default Seed Admin)
Untuk masuk ke dashboard pertama kali, silakan gunakan kredensial berikut:
* **Username**: `admin`
* **Password**: `admin123`

*(Sangat disarankan untuk mengganti password bawaan ini melalui menu **Pengaturan → Kredensial Admin** setelah berhasil masuk).*

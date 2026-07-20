"""
models.py
Semua model database (SQLAlchemy) untuk aplikasi Kas Management.
File ini menggabungkan seluruh model yang sebelumnya terpisah di folder models/.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ─── Admin ─────────────────────────────────────────────────────────────────
class Admin(db.Model):
    __tablename__ = 'admin'

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    foto_profil = db.Column(db.String(255), nullable=True, default='default-profile.png')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Admin {self.username}>"


# ─── Mahasiswa ─────────────────────────────────────────────────────────────
class Mahasiswa(db.Model):
    __tablename__ = 'mahasiswa'

    id = db.Column(db.Integer, primary_key=True)
    nim = db.Column(db.String(50), unique=True, nullable=False)
    nama = db.Column(db.String(100), nullable=False)
    kelas = db.Column(db.String(50), nullable=False)
    status_mahasiswa = db.Column(db.String(20), nullable=False, default='Aktif')  # 'Aktif' / 'Nonaktif'

    # Relationships
    pembayaran = db.relationship('Pembayaran', backref='mahasiswa', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Mahasiswa {self.nim} - {self.nama}>"


# ─── Semester ──────────────────────────────────────────────────────────────
class Semester(db.Model):
    __tablename__ = 'semester'

    id = db.Column(db.Integer, primary_key=True)
    nama_semester = db.Column(db.String(100), unique=True, nullable=False)  # Contoh: "Ganjil 2023/2024"
    tahun_akademik = db.Column(db.String(50), nullable=False)               # Contoh: "2023/2024"
    nominal_per_bulan = db.Column(db.Integer, nullable=False, default=15000)
    nominal_per_minggu = db.Column(db.Integer, nullable=False, default=5000)
    jumlah_minggu = db.Column(db.Integer, nullable=False, default=3)
    status_aktif = db.Column(db.Boolean, nullable=False, default=True)

    # Relationships
    bulan = db.relationship('Bulan', backref='semester', lazy=True, cascade='all, delete-orphan')
    pembayaran = db.relationship('Pembayaran', backref='semester', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Semester {self.nama_semester}>"


# ─── Bulan ─────────────────────────────────────────────────────────────────
class Bulan(db.Model):
    __tablename__ = 'bulan'

    id = db.Column(db.Integer, primary_key=True)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id', ondelete='CASCADE'), nullable=False)
    nama_bulan = db.Column(db.String(50), nullable=False)  # Contoh: "September"
    urutan = db.Column(db.Integer, nullable=False, default=1)  # Untuk mengurutkan bulan dalam semester

    # Relationships
    pembayaran = db.relationship('Pembayaran', backref='bulan', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Bulan {self.nama_bulan} (Semester ID: {self.semester_id})>"


# ─── Pembayaran ────────────────────────────────────────────────────────────
class Pembayaran(db.Model):
    __tablename__ = 'pembayaran'

    id = db.Column(db.Integer, primary_key=True)
    mahasiswa_id = db.Column(db.Integer, db.ForeignKey('mahasiswa.id', ondelete='CASCADE'), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id', ondelete='CASCADE'), nullable=False)
    bulan_id = db.Column(db.Integer, db.ForeignKey('bulan.id', ondelete='CASCADE'), nullable=False)
    minggu_ke = db.Column(db.Integer, nullable=False)  # Contoh: 1, 2, atau 3
    tanggal_bayar = db.Column(db.DateTime, nullable=False, default=datetime.now)
    nominal = db.Column(db.Integer, nullable=False, default=5000)

    # Unique constraint to prevent duplicate payments for the same week
    __table_args__ = (
        db.UniqueConstraint('mahasiswa_id', 'semester_id', 'bulan_id', 'minggu_ke', name='_mahasiswa_week_pay_uc'),
    )

    def __repr__(self):
        return f"<Pembayaran Mhs ID: {self.mahasiswa_id}, Sem ID: {self.semester_id}, Bulan ID: {self.bulan_id}, Minggu: {self.minggu_ke}>"


# ─── Pengeluaran ───────────────────────────────────────────────────────────
class Pengeluaran(db.Model):
    __tablename__ = 'pengeluaran'

    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.Date, nullable=False, default=lambda: datetime.now().date())
    kategori = db.Column(db.String(100), nullable=False)
    keperluan = db.Column(db.String(255), nullable=False)
    nominal = db.Column(db.Integer, nullable=False)
    keterangan = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Pengeluaran {self.keperluan} - Rp{self.nominal}>"


# ─── Pesan Masuk (Hubungi Bendahara) ────────────────────────────────────────
class PesanMasuk(db.Model):
    __tablename__ = 'pesan_masuk'

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    nim = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    subjek = db.Column(db.String(200), nullable=False)
    isi_pesan = db.Column(db.Text, nullable=False)
    tanggal = db.Column(db.DateTime, nullable=False, default=datetime.now)
    status = db.Column(db.String(20), nullable=False, default='Belum Dibaca')  # 'Belum Dibaca' / 'Sudah Dibaca'

    def __repr__(self):
        return f"<PesanMasuk {self.nama} - {self.subjek}>"


# ─── Fitur Unggulan (konten dinamis Beranda) ────────────────────────────────
class FiturUnggulan(db.Model):
    __tablename__ = 'fitur_unggulan'

    id = db.Column(db.Integer, primary_key=True)
    icon = db.Column(db.String(10), nullable=False, default='⭐')
    teks = db.Column(db.String(150), nullable=False)
    urutan = db.Column(db.Integer, nullable=False, default=1)

    def __repr__(self):
        return f"<FiturUnggulan {self.teks}>"


# ─── Konten Tentang (konten dinamis halaman Tentang & FAQ) ──────────────────
class KontenTentang(db.Model):
    __tablename__ = 'konten_tentang'

    id = db.Column(db.Integer, primary_key=True)
    deskripsi_tentang = db.Column(db.Text, nullable=False, default='')
    tujuan = db.Column(db.Text, nullable=False, default='')
    cara_kerja = db.Column(db.Text, nullable=False, default='')

    def __repr__(self):
        return f"<KontenTentang id={self.id}>"


# ─── FAQ (konten dinamis halaman Tentang & FAQ) ─────────────────────────────
class FAQ(db.Model):
    __tablename__ = 'faq'

    id = db.Column(db.Integer, primary_key=True)
    pertanyaan = db.Column(db.String(255), nullable=False)
    jawaban = db.Column(db.Text, nullable=False)
    urutan = db.Column(db.Integer, nullable=False, default=1)

    def __repr__(self):
        return f"<FAQ {self.pertanyaan}>"


# ─── Pengaturan ────────────────────────────────────────────────────────────
class Pengaturan(db.Model):
    """Konfigurasi sistem aplikasi yang bersifat global, termasuk konten
    hero Beranda. Perubahan nominal kas default hanya berlaku untuk semester baru.
    """
    __tablename__ = 'pengaturan'

    id = db.Column(db.Integer, primary_key=True)
    nama_organisasi = db.Column(db.String(200), nullable=False, default='Organisasi Mahasiswa')
    logo_filename = db.Column(db.String(255), nullable=True, default='logo.png')
    nominal_per_bulan = db.Column(db.Integer, nullable=False, default=15000)
    nominal_per_minggu = db.Column(db.Integer, nullable=False, default=5000)
    jumlah_minggu = db.Column(db.Integer, nullable=False, default=3)
    deskripsi = db.Column(db.Text, nullable=True, default='')

    # Konten Hero Beranda (dikelola lewat Kelola Website)
    hero_judul = db.Column(db.String(200), nullable=False, default='Kelola Uang Kas Mahasiswa dengan Mudah')
    hero_deskripsi = db.Column(db.Text, nullable=False, default=(
        'Aplikasi berbasis web yang membantu pengelolaan pembayaran uang kas mahasiswa '
        'secara lebih mudah, transparan, dan terorganisir.'
    ))

    def __repr__(self):
        return f'<Pengaturan {self.nama_organisasi}>'

import logging
import os
from flask import Flask, render_template
from models import db, Admin, FiturUnggulan, KontenTentang, FAQ
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("kasku")

def create_app():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "templates"),
        static_folder=os.path.join(base_dir, "static"),
    )

    # ===== DEBUG SEMENTARA — hapus setelah fix =====
    tpl_dir = app.template_folder
    log.info("TEMPLATE_FOLDER = %s", tpl_dir)
    if os.path.isdir(tpl_dir):
        log.info("ISI templates/ = %s", os.listdir(tpl_dir))
        depan_dir = os.path.join(tpl_dir, "depan")
        if os.path.isdir(depan_dir):
            log.info("ISI templates/depan/ = %s", os.listdir(depan_dir))
        else:
            log.warning("templates/depan/ TIDAK ADA! Cek: %s", os.listdir(tpl_dir))
    else:
        log.warning("TEMPLATE FOLDER TIDAK ADA: %s", tpl_dir)
    # ===== END DEBUG =====

    app.config.from_object(Config)
    Config.init_app(app)

    db.init_app(app)
    # Register all blueprints (models & routes are now single consolidated files)
    from routes import (
        public_bp, auth_bp, dashboard_bp, semester_bp, mahasiswa_bp,
        pembayaran_bp, rekap_bp, pengeluaran_bp,
        pengaturan_bp, pesan_bp,
        kelola_data_bp, website_bp
    )
    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(semester_bp)
    app.register_blueprint(mahasiswa_bp)
    app.register_blueprint(pembayaran_bp)
    app.register_blueprint(rekap_bp)
    app.register_blueprint(pengeluaran_bp)
    app.register_blueprint(pengaturan_bp)
    app.register_blueprint(pesan_bp)
    app.register_blueprint(kelola_data_bp)
    app.register_blueprint(website_bp)

    @app.context_processor
    def inject_site_settings():
        from models import Pengaturan
        settings = Pengaturan.query.first()
        return {'site_logo': settings.logo_filename if settings and settings.logo_filename else 'logo.png'}

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('404.html'), 404

    return app


def _seed_admin():
    """Create default admin account if none exists."""
    if not Admin.query.first():
        admin = Admin(
            nama='Administrator',
            email='admin@kasmanagement.id',
            username='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        log.info('Seed admin default dibuat: admin / admin123')


def _seed_konten_situs():
    """Isi konten default Fitur Unggulan & Tentang agar halaman publik tidak
    kosong saat pertama kali dijalankan. Ini konten statis awal, bukan data
    transaksi dummy — semuanya dapat diedit admin lewat Kelola Website."""
    if not FiturUnggulan.query.first():
        default_fitur = [
            ('👨‍🎓', 'Manajemen Mahasiswa'),
            ('💳', 'Pembayaran Kas'),
            ('📅', 'Manajemen Semester'),
            ('💰', 'Keuangan Otomatis'),
            ('📊', 'Laporan Semester'),
            ('🔒', 'Login Admin Aman'),
        ]
        for i, (icon, teks) in enumerate(default_fitur, start=1):
            db.session.add(FiturUnggulan(icon=icon, teks=teks, urutan=i))
        db.session.commit()
        log.info('Seed konten Fitur Unggulan dibuat.')

    if not KontenTentang.query.first():
        konten = KontenTentang(
            deskripsi_tentang=(
                'KasKu adalah aplikasi manajemen uang kas mahasiswa berbasis web yang dibangun '
                'menggunakan Python 3, Flask, dan Supabase (PostgreSQL). Aplikasi ini dirancang untuk menggantikan '
                'sistem pencatatan kas manual yang rentan terhadap kesalahan dan ketidaktransparanan.'
            ),
            tujuan=(
                'Membantu organisasi mahasiswa mengelola pembayaran kas secara transparan, efisien, '
                'dan mudah diakses oleh seluruh anggota maupun pengurus.'
            ),
            cara_kerja=(
                'Admin login ke dashboard, memilih semester aktif, lalu mencatat pembayaran mingguan '
                'setiap mahasiswa. Sistem otomatis menghitung status pembayaran, saldo kas, dan '
                'menampilkan ringkasannya secara real-time di halaman publik Informasi Kas.'
            )
        )
        db.session.add(konten)
        db.session.commit()
        log.info('Seed konten Tentang dibuat.')

    if not FAQ.query.first():
        default_faqs = [
            ('Apa itu KasKu?',
             'KasKu adalah aplikasi manajemen uang kas mahasiswa berbasis web yang membantu mencatat pembayaran, mengelola semester, memantau saldo, dan membuat laporan keuangan secara otomatis.'),
            ('Siapa yang dapat mengakses dashboard?',
             'Hanya administrator yang telah login yang dapat mengakses dashboard. Pengunjung umum hanya dapat melihat halaman publik (Beranda, Informasi Kas, Tentang & FAQ).'),
            ('Apa arti status Belum, Dicicil, dan Lunas?',
             'Belum = belum ada pembayaran sama sekali; Dicicil = sudah ada pembayaran namun belum mencapai target; Lunas = total pembayaran telah mencapai atau melebihi target.'),
            ('Bagaimana cara menghubungi bendahara?',
             'Gunakan form "Hubungi Bendahara" pada tab ketiga halaman Informasi Kas. Pesan akan tersimpan dan dapat dibalas oleh admin.'),
        ]
        for i, (q, a) in enumerate(default_faqs, start=1):
            db.session.add(FAQ(pertanyaan=q, jawaban=a, urutan=i))
        db.session.commit()
        log.info('Seed konten FAQ dibuat.')

def init_database(app):
    with app.app_context():
        log.info("Inisialisasi database...")
        db.create_all()
        _seed_admin()
        _seed_konten_situs()
        log.info("Database siap.")


app = create_app()

# Jalankan init sekali. Lewati proses parent reloader dev (WERKZEUG_RUN_MAIN
# belum di-set) supaya tak jalan 2x; gunicorn/Vercel & child reloader tetap init.
if not (__name__ == '__main__' and not os.environ.get('WERKZEUG_RUN_MAIN')):
    init_database(app)

if __name__ == '__main__':
    app.run(debug=True)



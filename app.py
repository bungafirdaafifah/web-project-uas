import os
from flask import Flask, render_template
from models import db, Admin, FiturUnggulan, KontenTentang, FAQ
from config import Config

def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )

    print("Template folder =", app.template_folder)
    print("Jinja search path =", app.jinja_loader.searchpath)

    # ===== DEBUG =====
    print("========== DEBUG ==========")
    print("BASE_DIR =", os.path.dirname(os.path.abspath(__file__)))
    print("CURRENT =", os.getcwd())
    print("TEMPLATE FOLDER =", app.template_folder)

    print("ISI ROOT =", os.listdir(os.path.dirname(os.path.abspath(__file__))))

    if os.path.exists("templates"):
        print("ISI templates =", os.listdir("templates"))

    if os.path.exists("templates/public"):
        print("ISI templates/public =", os.listdir("templates/public"))

    print("===========================")
    # ===== END DEBUG =====

    app.config.from_object(Config)

    print("=" * 50)
    print("DATABASE =", app.config["SQLALCHEMY_DATABASE_URI"])
    print("=" * 50)

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

    # Create tables and seed default admin on first run
    with app.app_context():
        try:
            print("=== MEMULAI INISIALISASI DATABASE ===")

            db.create_all()
            print("✓ db.create_all() berhasil")

            _seed_admin()
            print("✓ _seed_admin() berhasil")

            _seed_konten_situs()
            print("✓ _seed_konten_situs() berhasil")

        except Exception:
            import traceback
            traceback.print_exc()
            raise

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
        print('[Seed] Default admin account created: admin / admin123')


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
        print('[Seed] Konten Fitur Unggulan default dibuat.')

    if not KontenTentang.query.first():
        konten = KontenTentang(
            deskripsi_tentang=(
                'KasKu adalah aplikasi manajemen uang kas mahasiswa berbasis web yang dibangun '
                'menggunakan Python 3, Flask, dan SQLite. Aplikasi ini dirancang untuk menggantikan '
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
        print('[Seed] Konten Tentang default dibuat.')

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
        print('[Seed] Konten FAQ default dibuat.')

app = create_app()

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)



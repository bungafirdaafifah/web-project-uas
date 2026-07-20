"""
routes.py
Semua route/blueprint Flask untuk aplikasi Kas Management.
File ini menggabungkan seluruh route yang sebelumnya terpisah di folder routes/.
"""

import os
import re
from datetime import datetime, date
from functools import wraps

from flask import (
    Blueprint, render_template, request, redirect, url_for,
    session, flash, jsonify, current_app
)
from sqlalchemy import func, or_
from werkzeug.utils import secure_filename

from models import db, Admin, Mahasiswa, Semester, Bulan, Pembayaran, Pengeluaran, Pengaturan, PesanMasuk, FiturUnggulan, KontenTentang, FAQ

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

INDONESIAN_MONTHS = {
    'Januari': 1, 'Februari': 2, 'Maret': 3, 'April': 4, 'Mei': 5, 'Juni': 6,
    'Juli': 7, 'Agustus': 8, 'September': 9, 'Oktober': 10, 'November': 11, 'Desember': 12
}


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ─── Login-Required Decorator ────────────────────────────────────────────────
def login_required(f):
    """Decorator that protects all /dashboard/* routes.

    Per FLOW.MD §1.B: If 'admin_id' is absent from the session, flash an error
    and redirect to the login page.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Silakan login terlebih dahulu.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC
# ═══════════════════════════════════════════════════════════════════════════
public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def home():
    settings = Pengaturan.query.first()
    if not settings:
        settings = Pengaturan()
        db.session.add(settings)
        db.session.commit()
    fitur_list = FiturUnggulan.query.order_by(FiturUnggulan.urutan.asc()).all()
    return render_template('public/home.html', settings=settings, fitur_list=fitur_list)


@public_bp.route('/informasi-kas')
def informasi_kas():
    """Halaman publik 'Informasi Kas' — tiga tab:
    1. Pembayaran Kas Mahasiswa: tabel status pembayaran mahasiswa per semester (read-only)
    2. Ringkasan Keuangan Semester: total pendapatan/pengeluaran/saldo + detail pengeluaran per semester
    3. Hubungi Bendahara: form kontak yang tersimpan ke database
    """
    active_tab = request.args.get('tab', 'kas')
    semesters = Semester.query.order_by(Semester.id.desc()).all()

    # ── Tab 1: Pembayaran Kas Mahasiswa ───────────────────────────────────
    sem_kas_id = request.args.get('sem_kas', type=int)
    semester_kas = None
    if sem_kas_id:
        semester_kas = Semester.query.get(sem_kas_id)
    elif semesters:
        aktif = [s for s in semesters if s.status_aktif]
        semester_kas = aktif[0] if aktif else semesters[0]

    months_kas = []
    student_rows = []

    if semester_kas:
        months_kas = Bulan.query.filter_by(semester_id=semester_kas.id).order_by(Bulan.urutan.asc()).all()
        students = Mahasiswa.query.filter_by(status_mahasiswa='Aktif').order_by(Mahasiswa.nama.asc()).all()
        target_total = semester_kas.nominal_per_minggu * semester_kas.jumlah_minggu * len(months_kas)

        for mhs in students:
            bulan_status = []
            total_paid = 0
            for b in months_kas:
                paid_records = Pembayaran.query.filter_by(
                    mahasiswa_id=mhs.id, semester_id=semester_kas.id, bulan_id=b.id
                ).all()
                paid_weeks = {p.minggu_ke for p in paid_records}
                total_paid += sum(p.nominal for p in paid_records)
                weeks = [(wk in paid_weeks) for wk in range(1, semester_kas.jumlah_minggu + 1)]
                bulan_status.append(weeks)

            persentase = min(100, int((total_paid / target_total) * 100)) if target_total > 0 else 0

            student_rows.append({
                'nama': mhs.nama,
                'nim': mhs.nim,
                'bulan_status': bulan_status,
                'jumlah_pembayaran': total_paid,
                'persentase': persentase
            })

    # ── Tab 2: Ringkasan Keuangan Semester ────────────────────────────────
    sem_ringkasan_id = request.args.get('sem_ringkasan', type=int)
    semester_ringkasan = None
    if sem_ringkasan_id:
        semester_ringkasan = Semester.query.get(sem_ringkasan_id)
    elif semesters:
        aktif = [s for s in semesters if s.status_aktif]
        semester_ringkasan = aktif[0] if aktif else semesters[0]

    total_pendapatan = 0
    total_pengeluaran = 0
    saldo_kas = 0
    detail_pengeluaran = []

    if semester_ringkasan:
        total_pendapatan = db.session.query(func.sum(Pembayaran.nominal)).filter_by(
            semester_id=semester_ringkasan.id
        ).scalar() or 0

        all_expenses = Pengeluaran.query.order_by(Pengeluaran.tanggal.asc()).all()
        detail_pengeluaran = [e for e in all_expenses if is_expense_in_semester(e.tanggal, semester_ringkasan)]
        total_pengeluaran = sum(e.nominal for e in detail_pengeluaran)
        saldo_kas = total_pendapatan - total_pengeluaran

    return render_template(
        'public/informasi_kas.html',
        active_tab=active_tab,
        semesters=semesters,
        semester_kas=semester_kas,
        months_kas=months_kas,
        student_rows=student_rows,
        semester_ringkasan=semester_ringkasan,
        total_pendapatan=total_pendapatan,
        total_pengeluaran=total_pengeluaran,
        saldo_kas=saldo_kas,
        detail_pengeluaran=detail_pengeluaran
    )


@public_bp.route('/informasi-kas/kirim-pesan', methods=['POST'])
def kirim_pesan():
    """Tab 3 — Hubungi Bendahara: simpan pesan pengunjung ke database."""
    nama = request.form.get('nama', '').strip()
    nim = request.form.get('nim', '').strip()
    email = request.form.get('email', '').strip()
    subjek = request.form.get('subjek', '').strip()
    isi_pesan = request.form.get('isi_pesan', '').strip()

    if not nama or not subjek or not isi_pesan:
        flash('Nama, Subjek, dan Pesan wajib diisi.', 'danger')
        return redirect(url_for('public.informasi_kas', tab='kontak'))

    try:
        pesan = PesanMasuk(
            nama=nama,
            nim=nim if nim else None,
            email=email if email else None,
            subjek=subjek,
            isi_pesan=isi_pesan,
            status='Belum Dibaca'
        )
        db.session.add(pesan)
        db.session.commit()
        flash('Pesan berhasil dikirim. Terima kasih telah menghubungi kami!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal mengirim pesan: {str(e)}', 'danger')

    return redirect(url_for('public.informasi_kas', tab='kontak'))


@public_bp.route('/tentang')
def tentang():
    konten = KontenTentang.query.first()
    faq_list = FAQ.query.order_by(FAQ.urutan.asc()).all()
    return render_template('public/tentang.html', konten=konten, faq_list=faq_list)


# ═══════════════════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════════════════
auth_bp = Blueprint('auth', __name__, url_prefix='/dashboard')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Show login form (GET) or authenticate admin (POST).

    Per FLOW.MD §1.A:
    - Autentikasi Berhasil → redirect ke /dashboard
    - Autentikasi Gagal   → kembali ke /dashboard/login dengan flash error
    """
    if 'admin_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Username dan password wajib diisi.', 'danger')
            return render_template('login.html')

        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.check_password(password):
            session.clear()
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            session['admin_nama'] = admin.nama
            flash(f'Selamat datang, {admin.nama}! Anda berhasil masuk.', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Username atau password salah. Silakan coba lagi.', 'danger')
            return render_template('login.html')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Clear the admin session and redirect to login.

    Per FLOW.MD §11 (Flow Logout):
    1. Hapus session admin (session.clear())
    2. Tampilkan flash message sukses logout
    3. Redirect kembali ke halaman login admin
    """
    session.clear()
    flash('Anda berhasil logout. Sampai jumpa!', 'success')
    return redirect(url_for('auth.login'))


# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


def get_semester_years(tahun_akademik):
    """Parse academic year like '2023/2024' into (2023, 2024)."""
    parts = tahun_akademik.split('/')
    if len(parts) == 2:
        try:
            return int(parts[0]), int(parts[1])
        except ValueError:
            pass
    try:
        y1 = int(tahun_akademik[:4])
        return y1, y1 + 1
    except:
        curr_year = datetime.now().year
        return curr_year, curr_year + 1


def is_expense_in_semester(expense_date, semester):
    """Determine if an expense belongs to a semester based on date.

    Bug fix: tahun untuk tiap bulan pada semester sebelumnya ditebak dengan
    aturan tetap (bulan >= Juli -> year1, selain itu -> year2). Aturan itu
    hanya benar jika bulan semester persis terbagi di batas Juli, sehingga
    pengeluaran pada semester yang susunan bulannya melewati batas tsb
    (mis. Genap yang mencakup Juli, atau Ganjil yang berlanjut ke
    Januari/Februari) salah dipetakan ke tahun yang keliru dan tidak pernah
    cocok -> Total Pengeluaran & Saldo Kas di Informasi Kas tidak berubah.

    Perbaikan: tahun ditentukan secara kronologis mengikuti urutan bulan
    yang sebenarnya dipilih admin (Bulan.urutan). Tahun hanya bertambah saat
    urutan bulan berputar mundur (mis. dari Desember ke Januari), bukan
    berdasarkan angka bulan tetap.
    """
    year1, year2 = get_semester_years(semester.tahun_akademik)

    bulan_urut = sorted(semester.bulan, key=lambda b: b.urutan)

    current_year = None
    prev_m_num = None
    for b in bulan_urut:
        m_num = INDONESIAN_MONTHS.get(b.nama_bulan)
        if not m_num:
            continue
        if current_year is None:
            # Anchor tahun bulan pertama menggunakan aturan lama (tetap
            # kompatibel untuk semester yang sudah terbagi rapi di Juli).
            current_year = year1 if m_num >= 7 else year2
        elif m_num < prev_m_num:
            # Urutan bulan berputar dari akhir tahun ke awal tahun.
            current_year += 1
        prev_m_num = m_num

        if expense_date.month == m_num and expense_date.year == current_year:
            return True
    return False


@dashboard_bp.route('/')
@login_required
def index():
    semesters = Semester.query.all()

    selected_sem_id = request.args.get('semester_id', type=int)

    selected_semester = None
    if selected_sem_id:
        selected_semester = Semester.query.get(selected_sem_id)

    total_mahasiswa = Mahasiswa.query.filter_by(status_mahasiswa='Aktif').count()

    if selected_semester:
        total_pendapatan = db.session.query(func.sum(Pembayaran.nominal)).filter_by(semester_id=selected_semester.id).scalar() or 0
    else:
        total_pendapatan = db.session.query(func.sum(Pembayaran.nominal)).scalar() or 0

    all_expenses = Pengeluaran.query.all()
    if selected_semester:
        total_pengeluaran = sum(exp.nominal for exp in all_expenses if is_expense_in_semester(exp.tanggal, selected_semester))
    else:
        total_pengeluaran = sum(exp.nominal for exp in all_expenses)

    saldo_kas = total_pendapatan - total_pengeluaran

    mahasiswa_lunas = 0
    mahasiswa_belum_lunas = 0
    active_students = Mahasiswa.query.filter_by(status_mahasiswa='Aktif').all()

    if selected_semester:
        target_semester = selected_semester.nominal_per_minggu * selected_semester.jumlah_minggu * len(selected_semester.bulan)
        for mhs in active_students:
            total_bayar_sem = db.session.query(func.sum(Pembayaran.nominal)).filter_by(mahasiswa_id=mhs.id, semester_id=selected_semester.id).scalar() or 0
            if total_bayar_sem >= target_semester and target_semester > 0:
                mahasiswa_lunas += 1
            else:
                mahasiswa_belum_lunas += 1
    else:
        for mhs in active_students:
            is_lunas_all = True
            if not semesters:
                is_lunas_all = False
            for sem in semesters:
                target_sem = sem.nominal_per_minggu * sem.jumlah_minggu * len(sem.bulan)
                total_bayar_sem = db.session.query(func.sum(Pembayaran.nominal)).filter_by(mahasiswa_id=mhs.id, semester_id=sem.id).scalar() or 0
                if total_bayar_sem < target_sem:
                    is_lunas_all = False
                    break
            if is_lunas_all and semesters:
                mahasiswa_lunas += 1
            else:
                mahasiswa_belum_lunas += 1

    semester_labels = [sem.nama_semester for sem in semesters]
    income_data = []
    expense_data = []

    for sem in semesters:
        inc = db.session.query(func.sum(Pembayaran.nominal)).filter_by(semester_id=sem.id).scalar() or 0
        exp = sum(e.nominal for e in all_expenses if is_expense_in_semester(e.tanggal, sem))
        income_data.append(inc)
        expense_data.append(exp)

    return render_template(
        'dashboard/index.html',
        semesters=semesters,
        selected_semester=selected_semester,
        total_mahasiswa=total_mahasiswa,
        total_pendapatan=total_pendapatan,
        total_pengeluaran=total_pengeluaran,
        saldo_kas=saldo_kas,
        mahasiswa_lunas=mahasiswa_lunas,
        mahasiswa_belum_lunas=mahasiswa_belum_lunas,
        semester_labels=semester_labels,
        income_data=income_data,
        expense_data=expense_data
    )


# ═══════════════════════════════════════════════════════════════════════════
# SEMESTER
# ═══════════════════════════════════════════════════════════════════════════
semester_bp = Blueprint('semester', __name__, url_prefix='/dashboard/semester')


@semester_bp.route('/')
@login_required
def index():
    semesters = Semester.query.order_by(Semester.id.desc()).all()
    return render_template('pengaturan/semester.html', semesters=semesters)


@semester_bp.route('/tambah', methods=['GET', 'POST'])
@login_required
def tambah():
    if request.method == 'POST':
        nama_semester = request.form.get('nama_semester', '').strip()
        tahun_akademik = request.form.get('tahun_akademik', '').strip()
        nominal_per_bulan = request.form.get('nominal_per_bulan', type=int)
        nominal_per_minggu = request.form.get('nominal_per_minggu', type=int)
        jumlah_minggu = request.form.get('jumlah_minggu', type=int)

        selected_months = request.form.getlist('months')

        if not nama_semester or not tahun_akademik or not nominal_per_bulan or not nominal_per_minggu or not jumlah_minggu:
            flash('Seluruh kolom konfigurasi wajib diisi.', 'danger')
            return render_template('pengaturan/tambah_semester.html')

        if not selected_months:
            flash('Pilih minimal satu bulan pembayaran untuk semester ini.', 'danger')
            return render_template('pengaturan/tambah_semester.html')

        existing = Semester.query.filter_by(nama_semester=nama_semester).first()
        if existing:
            flash(f'Semester "{nama_semester}" sudah terdaftar.', 'danger')
            return render_template('pengaturan/tambah_semester.html')

        try:
            sem = Semester(
                nama_semester=nama_semester,
                tahun_akademik=tahun_akademik,
                nominal_per_bulan=nominal_per_bulan,
                nominal_per_minggu=nominal_per_minggu,
                jumlah_minggu=jumlah_minggu,
                status_aktif=True
            )
            db.session.add(sem)
            db.session.commit()

            for index, m_name in enumerate(selected_months):
                bulan = Bulan(
                    semester_id=sem.id,
                    nama_bulan=m_name,
                    urutan=index + 1
                )
                db.session.add(bulan)

            db.session.commit()
            flash(f'Semester {nama_semester} berhasil dibuat.', 'success')
            return redirect(url_for('semester.index'))

        except Exception as e:
            db.session.rollback()
            flash(f'Gagal menambahkan semester: {str(e)}', 'danger')
            return render_template('pengaturan/tambah_semester.html')

    return render_template('pengaturan/tambah_semester.html')


@semester_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    sem = Semester.query.get_or_404(id)
    if request.method == 'POST':
        tahun_akademik = request.form.get('tahun_akademik', '').strip()
        status_aktif_val = request.form.get('status_aktif') == '1'

        if not tahun_akademik:
            flash('Tahun akademik wajib diisi.', 'danger')
            return render_template('pengaturan/edit_semester.html', semester=sem)

        try:
            sem.tahun_akademik = tahun_akademik
            sem.status_aktif = status_aktif_val
            db.session.commit()
            flash(f'Semester {sem.nama_semester} berhasil diperbarui.', 'success')
            return redirect(url_for('semester.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal memperbarui semester: {str(e)}', 'danger')
            return render_template('pengaturan/edit_semester.html', semester=sem)

    return render_template('pengaturan/edit_semester.html', semester=sem)


@semester_bp.route('/hapus/<int:id>', methods=['POST'])
@login_required
def hapus(id):
    sem = Semester.query.get_or_404(id)

    has_payments = Pembayaran.query.filter_by(semester_id=sem.id).first()
    if has_payments:
        flash(f'Semester {sem.nama_semester} tidak dapat dihapus karena memiliki riwayat transaksi pembayaran kas.', 'danger')
        return redirect(url_for('semester.index'))

    try:
        db.session.delete(sem)
        db.session.commit()
        flash(f'Semester {sem.nama_semester} berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menghapus semester: {str(e)}', 'danger')

    return redirect(url_for('semester.index'))


# ═══════════════════════════════════════════════════════════════════════════
# MAHASISWA
# ═══════════════════════════════════════════════════════════════════════════
mahasiswa_bp = Blueprint('mahasiswa', __name__, url_prefix='/dashboard/mahasiswa')


@mahasiswa_bp.route('/')
@login_required
def index():
    q = request.args.get('q', '').strip()
    if q:
        students = Mahasiswa.query.filter(
            or_(
                Mahasiswa.nama.like(f"%{q}%"),
                Mahasiswa.nim.like(f"%{q}%")
            )
        ).all()
    else:
        students = Mahasiswa.query.order_by(Mahasiswa.nama.asc()).all()
    return render_template('mahasiswa/mahasiswa.html', students=students, query=q)


@mahasiswa_bp.route('/tambah', methods=['GET', 'POST'])
@login_required
def tambah():
    if request.method == 'POST':
        nim = request.form.get('nim', '').strip()
        nama = request.form.get('nama', '').strip()
        kelas = request.form.get('kelas', '').strip()
        status_mahasiswa = request.form.get('status_mahasiswa', 'Aktif').strip()

        if not nim or not nama or not kelas:
            flash('NIM, Nama, dan Kelas wajib diisi.', 'danger')
            return render_template('mahasiswa/tambah_mahasiswa.html')

        existing = Mahasiswa.query.filter_by(nim=nim).first()
        if existing:
            flash(f'Mahasiswa dengan NIM {nim} sudah terdaftar.', 'danger')
            return render_template('mahasiswa/tambah_mahasiswa.html')

        try:
            mhs = Mahasiswa(
                nim=nim,
                nama=nama,
                kelas=kelas,
                status_mahasiswa=status_mahasiswa
            )
            db.session.add(mhs)
            db.session.commit()
            flash(f'Mahasiswa {nama} berhasil ditambahkan.', 'success')
            return redirect(url_for('mahasiswa.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal menambahkan mahasiswa: {str(e)}', 'danger')
            return render_template('mahasiswa/tambah_mahasiswa.html')

    return render_template('mahasiswa/tambah_mahasiswa.html')


@mahasiswa_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    mhs = Mahasiswa.query.get_or_404(id)
    if request.method == 'POST':
        nim = request.form.get('nim', '').strip()
        nama = request.form.get('nama', '').strip()
        kelas = request.form.get('kelas', '').strip()
        status_mahasiswa = request.form.get('status_mahasiswa', 'Aktif').strip()

        if not nim or not nama or not kelas:
            flash('NIM, Nama, dan Kelas wajib diisi.', 'danger')
            return render_template('mahasiswa/edit_mahasiswa.html', mahasiswa=mhs)

        existing = Mahasiswa.query.filter(Mahasiswa.nim == nim, Mahasiswa.id != id).first()
        if existing:
            flash(f'Mahasiswa dengan NIM {nim} sudah terdaftar.', 'danger')
            return render_template('mahasiswa/edit_mahasiswa.html', mahasiswa=mhs)

        try:
            mhs.nim = nim
            mhs.nama = nama
            mhs.kelas = kelas
            mhs.status_mahasiswa = status_mahasiswa
            db.session.commit()
            flash(f'Data mahasiswa {nama} berhasil diperbarui.', 'success')
            return redirect(url_for('mahasiswa.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal memperbarui data mahasiswa: {str(e)}', 'danger')
            return render_template('mahasiswa/edit_mahasiswa.html', mahasiswa=mhs)

    return render_template('mahasiswa/edit_mahasiswa.html', mahasiswa=mhs)


@mahasiswa_bp.route('/hapus/<int:id>', methods=['POST'])
@login_required
def hapus(id):
    mhs = Mahasiswa.query.get_or_404(id)
    try:
        nama = mhs.nama
        db.session.delete(mhs)
        db.session.commit()
        flash(f'Mahasiswa {nama} berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menghapus mahasiswa: {str(e)}', 'danger')

    return redirect(url_for('mahasiswa.index'))


# ═══════════════════════════════════════════════════════════════════════════
# PEMBAYARAN
# ═══════════════════════════════════════════════════════════════════════════
pembayaran_bp = Blueprint('pembayaran', __name__, url_prefix='/dashboard/pembayaran')


@pembayaran_bp.route('/')
@login_required
def index():
    """Landing Pembayaran Kas — 2 pilihan: Kelola atau Riwayat."""
    return render_template('keuangan/pembayaran_landing.html')


@pembayaran_bp.route('/kelola')
@login_required
def kelola():
    """Pilih semester → tampilkan seluruh mahasiswa aktif beserta progress pembayaran."""
    semesters = Semester.query.order_by(Semester.id.desc()).all()
    selected_sem_id = request.args.get('semester_id', type=int)

    selected_semester = None
    if selected_sem_id:
        selected_semester = Semester.query.get(selected_sem_id)
    elif semesters:
        aktif = [s for s in semesters if s.status_aktif]
        selected_semester = aktif[0] if aktif else semesters[0]

    rows = []
    if selected_semester:
        months = Bulan.query.filter_by(semester_id=selected_semester.id).all()
        target = selected_semester.nominal_per_minggu * selected_semester.jumlah_minggu * len(months)
        students = Mahasiswa.query.filter_by(status_mahasiswa='Aktif').order_by(Mahasiswa.nama.asc()).all()

        for mhs in students:
            total_paid = db.session.query(func.sum(Pembayaran.nominal)).filter_by(
                mahasiswa_id=mhs.id, semester_id=selected_semester.id
            ).scalar() or 0
            progress = min(100, int((total_paid / target) * 100)) if target > 0 else 0

            if target > 0 and total_paid >= target:
                status = 'Lunas'
            elif total_paid > 0:
                status = 'Dicicil'
            else:
                status = 'Belum'

            rows.append({'mahasiswa': mhs, 'progress': progress, 'status': status})

    return render_template(
        'keuangan/pembayaran_kelola.html',
        semesters=semesters,
        selected_semester=selected_semester,
        rows=rows
    )


@pembayaran_bp.route('/detail/<int:id>')
@login_required
def detail(id):
    mhs = Mahasiswa.query.get_or_404(id)
    semesters = Semester.query.all()

    selected_sem_id = request.args.get('semester_id', type=int)
    selected_semester = None
    if selected_sem_id:
        selected_semester = Semester.query.get(selected_sem_id)
    elif semesters:
        active_sems = [s for s in semesters if s.status_aktif]
        selected_semester = active_sems[0] if active_sems else semesters[0]

    months = []
    selected_bulan = None
    weeks_payment_status = {}
    summary = {
        'target': 0,
        'paid': 0,
        'remaining': 0,
        'status': 'Belum Lunas',
        'percentage': 0
    }

    if selected_semester:
        months = Bulan.query.filter_by(semester_id=selected_semester.id).order_by(Bulan.urutan.asc()).all()

        selected_bulan_id = request.args.get('bulan_id', type=int)
        if selected_bulan_id:
            selected_bulan = Bulan.query.get(selected_bulan_id)
        elif months:
            selected_bulan = months[0]

        if selected_bulan:
            paid_records = Pembayaran.query.filter_by(
                mahasiswa_id=mhs.id,
                semester_id=selected_semester.id,
                bulan_id=selected_bulan.id
            ).all()
            paid_weeks = {p.minggu_ke for p in paid_records}

            for wk in range(1, selected_semester.jumlah_minggu + 1):
                weeks_payment_status[wk] = (wk in paid_weeks)

        total_months = len(months)
        summary['target'] = selected_semester.nominal_per_minggu * selected_semester.jumlah_minggu * total_months
        summary['paid'] = db.session.query(func.sum(Pembayaran.nominal)).filter_by(
            mahasiswa_id=mhs.id,
            semester_id=selected_semester.id
        ).scalar() or 0
        summary['remaining'] = max(0, summary['target'] - summary['paid'])

        is_semester_lunas = True
        if total_months == 0:
            is_semester_lunas = False

        for m in months:
            month_paid = db.session.query(func.sum(Pembayaran.nominal)).filter_by(
                mahasiswa_id=mhs.id,
                semester_id=selected_semester.id,
                bulan_id=m.id
            ).scalar() or 0
            month_target = selected_semester.nominal_per_minggu * selected_semester.jumlah_minggu
            if month_paid < month_target:
                is_semester_lunas = False
                break

        summary['status'] = 'Lunas' if is_semester_lunas else 'Belum Lunas'
        if summary['target'] > 0:
            summary['percentage'] = min(100, int((summary['paid'] / summary['target']) * 100))

    return render_template(
        'mahasiswa/detail_mahasiswa.html',
        mahasiswa=mhs,
        semesters=semesters,
        selected_semester=selected_semester,
        months=months,
        selected_bulan=selected_bulan,
        weeks_payment_status=weeks_payment_status,
        summary=summary
    )


@pembayaran_bp.route('/simpan/<int:id>', methods=['POST'])
@login_required
def simpan(id):
    mhs = Mahasiswa.query.get_or_404(id)
    sem_id = request.form.get('semester_id', type=int)
    bulan_id = request.form.get('bulan_id', type=int)

    sem = Semester.query.get_or_404(sem_id)
    bulan = Bulan.query.get_or_404(bulan_id)

    checked_weeks = request.form.getlist('weeks')
    checked_weeks = [int(w) for w in checked_weeks]

    try:
        for wk in range(1, sem.jumlah_minggu + 1):
            existing_pay = Pembayaran.query.filter_by(
                mahasiswa_id=mhs.id,
                semester_id=sem.id,
                bulan_id=bulan.id,
                minggu_ke=wk
            ).first()

            if wk in checked_weeks:
                if not existing_pay:
                    pay = Pembayaran(
                        mahasiswa_id=mhs.id,
                        semester_id=sem.id,
                        bulan_id=bulan.id,
                        minggu_ke=wk,
                        nominal=sem.nominal_per_minggu
                    )
                    db.session.add(pay)
            else:
                if existing_pay:
                    db.session.delete(existing_pay)

        db.session.commit()
        flash('Pembayaran berhasil disimpan.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menyimpan pembayaran: {str(e)}', 'danger')

    return redirect(url_for('pembayaran.detail', id=mhs.id, semester_id=sem.id, bulan_id=bulan.id))


# ═══════════════════════════════════════════════════════════════════════════
# REKAP
# ═══════════════════════════════════════════════════════════════════════════
rekap_bp = Blueprint('rekap', __name__, url_prefix='/dashboard/rekap-pembayaran')


@rekap_bp.route('/')
@login_required
def index():
    """Rekap pembayaran dengan filter semester dan mahasiswa."""
    semesters = Semester.query.all()
    mahasiswas = Mahasiswa.query.order_by(Mahasiswa.nama.asc()).all()

    selected_sem_id = request.args.get('semester_id', type=int)
    selected_mhs_id = request.args.get('mahasiswa_id', type=int)

    query = db.session.query(Pembayaran).join(Mahasiswa).join(Semester).join(Bulan)

    if selected_sem_id:
        query = query.filter(Pembayaran.semester_id == selected_sem_id)
    if selected_mhs_id:
        query = query.filter(Pembayaran.mahasiswa_id == selected_mhs_id)

    payments = query.order_by(Pembayaran.id.desc()).all()

    total_nominal = sum(p.nominal for p in payments)

    selected_semester = Semester.query.get(selected_sem_id) if selected_sem_id else None
    selected_mahasiswa = Mahasiswa.query.get(selected_mhs_id) if selected_mhs_id else None

    return render_template(
        'keuangan/rekap_pembayaran.html',
        payments=payments,
        semesters=semesters,
        mahasiswas=mahasiswas,
        selected_semester=selected_semester,
        selected_mahasiswa=selected_mahasiswa,
        total_nominal=total_nominal
    )


# ═══════════════════════════════════════════════════════════════════════════
# PENGELUARAN
# ═══════════════════════════════════════════════════════════════════════════
pengeluaran_bp = Blueprint('pengeluaran', __name__, url_prefix='/dashboard/pengeluaran')


def _get_saldo():
    """Hitung saldo kas bersih terkini: Total Pendapatan - Total Pengeluaran."""
    total_inc = db.session.query(func.sum(Pembayaran.nominal)).scalar() or 0
    total_exp = db.session.query(func.sum(Pengeluaran.nominal)).scalar() or 0
    return total_inc - total_exp


@pengeluaran_bp.route('/')
@login_required
def index():
    """Landing Pengeluaran Kas — 2 pilihan: Kelola atau Riwayat."""
    return render_template('keuangan/pengeluaran_landing.html')


@pengeluaran_bp.route('/kelola')
@login_required
def kelola():
    expenses = Pengeluaran.query.order_by(Pengeluaran.tanggal.desc()).all()
    saldo = _get_saldo()
    return render_template('keuangan/pengeluaran.html', expenses=expenses, saldo=saldo)


@pengeluaran_bp.route('/riwayat')
@login_required
def riwayat():
    """Riwayat pengeluaran, dapat difilter per semester."""
    semesters = Semester.query.order_by(Semester.id.desc()).all()
    selected_sem_id = request.args.get('semester_id', type=int)
    selected_semester = Semester.query.get(selected_sem_id) if selected_sem_id else None

    all_expenses = Pengeluaran.query.order_by(Pengeluaran.tanggal.desc()).all()
    if selected_semester:
        expenses = [e for e in all_expenses if is_expense_in_semester(e.tanggal, selected_semester)]
    else:
        expenses = all_expenses

    total_nominal = sum(e.nominal for e in expenses)

    return render_template(
        'keuangan/pengeluaran_riwayat.html',
        expenses=expenses,
        semesters=semesters,
        selected_semester=selected_semester,
        total_nominal=total_nominal
    )


@pengeluaran_bp.route('/tambah', methods=['GET', 'POST'])
@login_required
def tambah():
    saldo = _get_saldo()
    if request.method == 'POST':
        tanggal_str = request.form.get('tanggal', '').strip()
        kategori = request.form.get('kategori', '').strip()
        keperluan = request.form.get('keperluan', '').strip()
        nominal = request.form.get('nominal', type=int)
        keterangan = request.form.get('keterangan', '').strip()

        if not tanggal_str or not kategori or not keperluan or not nominal:
            flash('Seluruh kolom wajib diisi.', 'danger')
            return render_template('keuangan/tambah_pengeluaran.html', saldo=saldo, today=date.today().isoformat())

        if nominal > saldo:
            flash(f'Saldo kas tidak mencukupi! Saldo saat ini: Rp {saldo:,}'.replace(',', '.'), 'danger')
            return render_template('keuangan/tambah_pengeluaran.html', saldo=saldo, today=date.today().isoformat())

        try:
            tanggal = datetime.strptime(tanggal_str, '%Y-%m-%d').date()
            exp = Pengeluaran(tanggal=tanggal, kategori=kategori, keperluan=keperluan,
                              nominal=nominal, keterangan=keterangan)
            db.session.add(exp)
            db.session.commit()
            flash('Pengeluaran berhasil ditambahkan.', 'success')
            return redirect(url_for('pengeluaran.kelola'))
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal menambahkan pengeluaran: {str(e)}', 'danger')
            return render_template('keuangan/tambah_pengeluaran.html', saldo=saldo, today=date.today().isoformat())

    return render_template('keuangan/tambah_pengeluaran.html', saldo=saldo, today=date.today().isoformat())


@pengeluaran_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    exp = Pengeluaran.query.get_or_404(id)
    saldo_adj = _get_saldo() + exp.nominal

    if request.method == 'POST':
        tanggal_str = request.form.get('tanggal', '').strip()
        kategori = request.form.get('kategori', '').strip()
        keperluan = request.form.get('keperluan', '').strip()
        nominal = request.form.get('nominal', type=int)
        keterangan = request.form.get('keterangan', '').strip()

        if not tanggal_str or not kategori or not keperluan or not nominal:
            flash('Seluruh kolom wajib diisi.', 'danger')
            return render_template('keuangan/edit_pengeluaran.html', expense=exp, saldo=saldo_adj)

        if nominal > saldo_adj:
            flash(f'Saldo kas tidak mencukupi untuk penyesuaian! Tersedia: Rp {saldo_adj:,}'.replace(',', '.'), 'danger')
            return render_template('keuangan/edit_pengeluaran.html', expense=exp, saldo=saldo_adj)

        try:
            exp.tanggal = datetime.strptime(tanggal_str, '%Y-%m-%d').date()
            exp.kategori = kategori
            exp.keperluan = keperluan
            exp.nominal = nominal
            exp.keterangan = keterangan
            db.session.commit()
            flash('Pengeluaran berhasil diperbarui.', 'success')
            return redirect(url_for('pengeluaran.kelola'))
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal memperbarui pengeluaran: {str(e)}', 'danger')
            return render_template('keuangan/edit_pengeluaran.html', expense=exp, saldo=saldo_adj)

    return render_template('keuangan/edit_pengeluaran.html', expense=exp, saldo=saldo_adj)


@pengeluaran_bp.route('/hapus/<int:id>', methods=['POST'])
@login_required
def hapus(id):
    exp = Pengeluaran.query.get_or_404(id)
    try:
        keperluan = exp.keperluan
        db.session.delete(exp)
        db.session.commit()
        flash(f'Pengeluaran "{keperluan}" berhasil dihapus. Saldo kas telah dipulihkan.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menghapus pengeluaran: {str(e)}', 'danger')
    return redirect(url_for('pengeluaran.kelola'))


# ═══════════════════════════════════════════════════════════════════════════
# PENGATURAN
# ═══════════════════════════════════════════════════════════════════════════
pengaturan_bp = Blueprint('pengaturan', __name__, url_prefix='/dashboard/pengaturan')


def _get_or_create_settings():
    settings = Pengaturan.query.first()
    if not settings:
        settings = Pengaturan()
        db.session.add(settings)
        db.session.commit()
    return settings


@pengaturan_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    settings = _get_or_create_settings()
    admin = Admin.query.get(session['admin_id'])

    if request.method == 'POST':
        form_type = request.form.get('form_type', 'umum')

        # ── Form Kredensial Admin (Username & Password) ──
        if form_type == 'kredensial':
            username = request.form.get('username', '').strip()
            password_lama = request.form.get('password_lama', '').strip()
            password_baru = request.form.get('password_baru', '').strip()
            password_konfirmasi = request.form.get('password_konfirmasi', '').strip()

            if not username:
                flash('Username wajib diisi.', 'danger')
                return redirect(url_for('pengaturan.index'))

            existing = Admin.query.filter(Admin.username == username, Admin.id != admin.id).first()
            if existing:
                flash('Username sudah digunakan oleh admin lain.', 'danger')
                return redirect(url_for('pengaturan.index'))

            if password_baru:
                if not password_lama or not admin.check_password(password_lama):
                    flash('Password lama salah atau belum diisi.', 'danger')
                    return redirect(url_for('pengaturan.index'))
                if password_baru != password_konfirmasi:
                    flash('Password baru dan konfirmasi tidak cocok.', 'danger')
                    return redirect(url_for('pengaturan.index'))
                admin.set_password(password_baru)

            admin.username = username
            try:
                db.session.commit()
                session['admin_username'] = admin.username
                flash('Kredensial admin berhasil diperbarui.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Gagal memperbarui kredensial: {str(e)}', 'danger')

            return redirect(url_for('pengaturan.index'))

        # ── Form Pengaturan Umum (Organisasi, Logo, Nominal Default) ──
        nama_organisasi = request.form.get('nama_organisasi', '').strip()
        nominal_per_bulan = request.form.get('nominal_per_bulan', type=int)
        nominal_per_minggu = request.form.get('nominal_per_minggu', type=int)
        jumlah_minggu = request.form.get('jumlah_minggu', type=int)
        deskripsi = request.form.get('deskripsi', '').strip()

        if not nama_organisasi or not nominal_per_bulan or not nominal_per_minggu or not jumlah_minggu:
            flash('Seluruh kolom wajib diisi.', 'danger')
            return render_template('pengaturan/pengaturan.html', settings=settings, admin=admin)

        logo_file = request.files.get('logo')
        if logo_file and logo_file.filename:
            if not _allowed_file(logo_file.filename):
                flash('Format file logo tidak valid! Gunakan .png atau .jpg.', 'danger')
                return render_template('pengaturan/pengaturan.html', settings=settings, admin=admin)
            filename = secure_filename(logo_file.filename)
            upload_path = os.path.join(current_app.root_path, 'static', 'img', filename)
            logo_file.save(upload_path)
            settings.logo_filename = filename

        settings.nama_organisasi = nama_organisasi
        settings.nominal_per_bulan = nominal_per_bulan
        settings.nominal_per_minggu = nominal_per_minggu
        settings.jumlah_minggu = jumlah_minggu
        settings.deskripsi = deskripsi

        try:
            db.session.commit()
            flash('Pengaturan sistem berhasil diperbarui. Perubahan akan berlaku pada semester baru.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal menyimpan pengaturan: {str(e)}', 'danger')

        return redirect(url_for('pengaturan.index'))

    return render_template('pengaturan/pengaturan.html', settings=settings, admin=admin)


# ═══════════════════════════════════════════════════════════════════════════
# PESAN MASUK (Admin — hasil dari form "Hubungi Bendahara" di halaman publik)
# ═══════════════════════════════════════════════════════════════════════════
pesan_bp = Blueprint('pesan', __name__, url_prefix='/dashboard/pesan')


@pesan_bp.route('/')
@login_required
def index():
    pesan_list = PesanMasuk.query.order_by(PesanMasuk.tanggal.desc()).all()
    jumlah_belum_dibaca = PesanMasuk.query.filter_by(status='Belum Dibaca').count()
    return render_template('pesan/pesan_masuk.html', pesan_list=pesan_list, jumlah_belum_dibaca=jumlah_belum_dibaca)


@pesan_bp.route('/detail/<int:id>')
@login_required
def detail(id):
    pesan = PesanMasuk.query.get_or_404(id)
    if pesan.status == 'Belum Dibaca':
        pesan.status = 'Sudah Dibaca'
        db.session.commit()
    return render_template('pesan/detail_pesan.html', pesan=pesan)


@pesan_bp.route('/tandai/<int:id>', methods=['POST'])
@login_required
def tandai(id):
    """Toggle status pesan: Belum Dibaca <-> Sudah Dibaca."""
    pesan = PesanMasuk.query.get_or_404(id)
    try:
        pesan.status = 'Sudah Dibaca' if pesan.status == 'Belum Dibaca' else 'Belum Dibaca'
        db.session.commit()
        flash(f'Status pesan ditandai sebagai "{pesan.status}".', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal mengubah status pesan: {str(e)}', 'danger')
    return redirect(url_for('pesan.index'))


@pesan_bp.route('/hapus/<int:id>', methods=['POST'])
@login_required
def hapus(id):
    pesan = PesanMasuk.query.get_or_404(id)
    try:
        db.session.delete(pesan)
        db.session.commit()
        flash('Pesan berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menghapus pesan: {str(e)}', 'danger')
    return redirect(url_for('pesan.index'))


# ═══════════════════════════════════════════════════════════════════════════
# KELOLA DATA (Landing — 4 kartu: Mahasiswa, Semester, Pembayaran, Pengeluaran)
# ═══════════════════════════════════════════════════════════════════════════
kelola_data_bp = Blueprint('kelola_data', __name__, url_prefix='/dashboard/kelola-data')


@kelola_data_bp.route('/')
@login_required
def index():
    return render_template('website/kelola_data.html')


# ═══════════════════════════════════════════════════════════════════════════
# KELOLA WEBSITE (Beranda & Tentang/FAQ — konten dinamis halaman publik)
# ═══════════════════════════════════════════════════════════════════════════
website_bp = Blueprint('website', __name__, url_prefix='/dashboard/kelola-website')


@website_bp.route('/')
@login_required
def index():
    return render_template('website/website_index.html')


@website_bp.route('/beranda', methods=['GET', 'POST'])
@login_required
def beranda():
    settings = Pengaturan.query.first()
    if not settings:
        settings = Pengaturan()
        db.session.add(settings)
        db.session.commit()

    if request.method == 'POST':
        hero_judul = request.form.get('hero_judul', '').strip()
        hero_deskripsi = request.form.get('hero_deskripsi', '').strip()

        if not hero_judul or not hero_deskripsi:
            flash('Judul dan deskripsi wajib diisi.', 'danger')
            return redirect(url_for('website.beranda'))

        logo_file = request.files.get('logo')
        if logo_file and logo_file.filename:
            if not _allowed_file(logo_file.filename):
                flash('Format file logo tidak valid! Gunakan .png atau .jpg.', 'danger')
                return redirect(url_for('website.beranda'))
            filename = secure_filename(logo_file.filename)
            upload_path = os.path.join(current_app.root_path, 'static', 'img', filename)
            logo_file.save(upload_path)
            settings.logo_filename = filename

        settings.hero_judul = hero_judul
        settings.hero_deskripsi = hero_deskripsi

        try:
            db.session.commit()
            flash('Konten Beranda berhasil diperbarui.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal menyimpan konten Beranda: {str(e)}', 'danger')

        return redirect(url_for('website.beranda'))

    fitur_list = FiturUnggulan.query.order_by(FiturUnggulan.urutan.asc()).all()
    return render_template('website/website_beranda.html', settings=settings, fitur_list=fitur_list)


@website_bp.route('/beranda/fitur/tambah', methods=['POST'])
@login_required
def fitur_tambah():
    icon = request.form.get('icon', '⭐').strip() or '⭐'
    teks = request.form.get('teks', '').strip()
    if not teks:
        flash('Teks fitur wajib diisi.', 'danger')
        return redirect(url_for('website.beranda'))
    try:
        urutan_max = db.session.query(func.max(FiturUnggulan.urutan)).scalar() or 0
        fitur = FiturUnggulan(icon=icon, teks=teks, urutan=urutan_max + 1)
        db.session.add(fitur)
        db.session.commit()
        flash('Fitur unggulan berhasil ditambahkan.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menambahkan fitur: {str(e)}', 'danger')
    return redirect(url_for('website.beranda'))


@website_bp.route('/beranda/fitur/edit/<int:id>', methods=['POST'])
@login_required
def fitur_edit(id):
    fitur = FiturUnggulan.query.get_or_404(id)
    icon = request.form.get('icon', '⭐').strip() or '⭐'
    teks = request.form.get('teks', '').strip()
    if not teks:
        flash('Teks fitur wajib diisi.', 'danger')
        return redirect(url_for('website.beranda'))
    try:
        fitur.icon = icon
        fitur.teks = teks
        db.session.commit()
        flash('Fitur unggulan berhasil diperbarui.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal memperbarui fitur: {str(e)}', 'danger')
    return redirect(url_for('website.beranda'))


@website_bp.route('/beranda/fitur/hapus/<int:id>', methods=['POST'])
@login_required
def fitur_hapus(id):
    fitur = FiturUnggulan.query.get_or_404(id)
    try:
        db.session.delete(fitur)
        db.session.commit()
        flash('Fitur unggulan berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menghapus fitur: {str(e)}', 'danger')
    return redirect(url_for('website.beranda'))


def _get_or_create_konten_tentang():
    konten = KontenTentang.query.first()
    if not konten:
        konten = KontenTentang()
        db.session.add(konten)
        db.session.commit()
    return konten


@website_bp.route('/tentang', methods=['GET', 'POST'])
@login_required
def tentang():
    konten = _get_or_create_konten_tentang()

    if request.method == 'POST':
        deskripsi_tentang = request.form.get('deskripsi_tentang', '').strip()
        tujuan = request.form.get('tujuan', '').strip()
        cara_kerja = request.form.get('cara_kerja', '').strip()

        if not deskripsi_tentang or not tujuan or not cara_kerja:
            flash('Seluruh kolom konten Tentang wajib diisi.', 'danger')
            return redirect(url_for('website.tentang'))

        try:
            konten.deskripsi_tentang = deskripsi_tentang
            konten.tujuan = tujuan
            konten.cara_kerja = cara_kerja
            db.session.commit()
            flash('Konten Tentang berhasil diperbarui.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal menyimpan konten Tentang: {str(e)}', 'danger')

        return redirect(url_for('website.tentang'))

    faq_list = FAQ.query.order_by(FAQ.urutan.asc()).all()
    return render_template('website/website_tentang.html', konten=konten, faq_list=faq_list)


@website_bp.route('/tentang/faq/tambah', methods=['POST'])
@login_required
def faq_tambah():
    pertanyaan = request.form.get('pertanyaan', '').strip()
    jawaban = request.form.get('jawaban', '').strip()
    if not pertanyaan or not jawaban:
        flash('Pertanyaan dan jawaban FAQ wajib diisi.', 'danger')
        return redirect(url_for('website.tentang'))
    try:
        urutan_max = db.session.query(func.max(FAQ.urutan)).scalar() or 0
        faq = FAQ(pertanyaan=pertanyaan, jawaban=jawaban, urutan=urutan_max + 1)
        db.session.add(faq)
        db.session.commit()
        flash('FAQ berhasil ditambahkan.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menambahkan FAQ: {str(e)}', 'danger')
    return redirect(url_for('website.tentang'))


@website_bp.route('/tentang/faq/edit/<int:id>', methods=['POST'])
@login_required
def faq_edit(id):
    faq = FAQ.query.get_or_404(id)
    pertanyaan = request.form.get('pertanyaan', '').strip()
    jawaban = request.form.get('jawaban', '').strip()
    if not pertanyaan or not jawaban:
        flash('Pertanyaan dan jawaban FAQ wajib diisi.', 'danger')
        return redirect(url_for('website.tentang'))
    try:
        faq.pertanyaan = pertanyaan
        faq.jawaban = jawaban
        db.session.commit()
        flash('FAQ berhasil diperbarui.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal memperbarui FAQ: {str(e)}', 'danger')
    return redirect(url_for('website.tentang'))


@website_bp.route('/tentang/faq/hapus/<int:id>', methods=['POST'])
@login_required
def faq_hapus(id):
    faq = FAQ.query.get_or_404(id)
    try:
        db.session.delete(faq)
        db.session.commit()
        flash('FAQ berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menghapus FAQ: {str(e)}', 'danger')
    return redirect(url_for('website.tentang'))

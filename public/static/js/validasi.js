/**
 * validasi.js
 * KasKu — Sistem Manajemen Uang Kas Mahasiswa
 * =============================================
 * Client-side validation untuk seluruh form dashboard.
 * Mencakup: Login, Tambah/Edit Mahasiswa, Tambah/Edit Semester,
 *           Tambah/Edit Pengeluaran, Pengaturan Sistem, Profil Admin.
 */

"use strict";

// ──────────────────────────────────────────────────────────
// HELPERS
// ──────────────────────────────────────────────────────────

/**
 * Tampilkan pesan error di bawah sebuah input.
 * @param {HTMLElement} input
 * @param {string} message
 */
function _showError(input, message) {
  input.classList.add('is-invalid');
  input.classList.remove('is-valid');
  let fb = input.nextElementSibling;
  if (!fb || !fb.classList.contains('invalid-feedback')) {
    fb = document.createElement('div');
    fb.classList.add('invalid-feedback');
    input.parentNode.insertBefore(fb, input.nextSibling);
  }
  fb.textContent = message;
}

/**
 * Tandai input sebagai valid.
 * @param {HTMLElement} input
 */
function _clearError(input) {
  input.classList.remove('is-invalid');
  input.classList.add('is-valid');
  const fb = input.nextElementSibling;
  if (fb && fb.classList.contains('invalid-feedback')) {
    fb.textContent = '';
  }
}

/**
 * Validasi satu field: tidak kosong.
 */
function _required(input, label) {
  if (!input.value.trim()) {
    _showError(input, `${label} tidak boleh kosong.`);
    return false;
  }
  _clearError(input);
  return true;
}

/**
 * Validasi angka positif.
 */
function _positiveNumber(input, label) {
  const v = parseInt(input.value, 10);
  if (isNaN(v) || v <= 0) {
    _showError(input, `${label} harus berupa angka lebih dari 0.`);
    return false;
  }
  _clearError(input);
  return true;
}

/**
 * Validasi format email sederhana.
 */
function _email(input) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!re.test(input.value.trim())) {
    _showError(input, 'Format email tidak valid.');
    return false;
  }
  _clearError(input);
  return true;
}

/**
 * Validasi ekstensi file upload.
 * @param {HTMLElement} input
 * @param {string[]} allowed - contoh: ['png', 'jpg', 'jpeg']
 */
function _fileExtension(input, allowed) {
  if (!input.value) return true; // file kosong = opsional, lewati
  const ext = input.value.split('.').pop().toLowerCase();
  if (!allowed.includes(ext)) {
    _showError(input, `Format file tidak valid. Gunakan: ${allowed.join(', ')}.`);
    return false;
  }
  _clearError(input);
  return true;
}


// ──────────────────────────────────────────────────────────
// FORM VALIDASI: LOGIN
// ──────────────────────────────────────────────────────────
function _validateLogin(form) {
  const username = form.querySelector('[name="username"]');
  const password = form.querySelector('[name="password"]');
  let ok = true;
  if (!_required(username, 'Username')) ok = false;
  if (!_required(password, 'Password')) ok = false;
  if (password && password.value.length < 6) {
    _showError(password, 'Password minimal 6 karakter.');
    ok = false;
  }
  return ok;
}


// ──────────────────────────────────────────────────────────
// FORM VALIDASI: MAHASISWA (Tambah & Edit)
// ──────────────────────────────────────────────────────────
function _validateMahasiswa(form) {
  let ok = true;
  const nim = form.querySelector('[name="nim"]');
  const nama = form.querySelector('[name="nama"]');
  const kelas = form.querySelector('[name="kelas"]');
  const status = form.querySelector('[name="status_mahasiswa"]');

  if (nim && !_required(nim, 'NIM')) ok = false;
  if (nim && nim.value.trim().length < 5) {
    _showError(nim, 'NIM minimal 5 karakter.');
    ok = false;
  } else if (nim) {
    _clearError(nim);
  }
  if (nama && !_required(nama, 'Nama')) ok = false;
  if (kelas && !_required(kelas, 'Kelas')) ok = false;
  if (status && !_required(status, 'Status')) ok = false;

  return ok;
}


// ──────────────────────────────────────────────────────────
// FORM VALIDASI: SEMESTER (Tambah & Edit)
// ──────────────────────────────────────────────────────────
function _validateSemester(form) {
  let ok = true;
  const nama = form.querySelector('[name="nama_semester"]');
  const tahun = form.querySelector('[name="tahun_akademik"]');
  const nom_bln = form.querySelector('[name="nominal_per_bulan"]');
  const nom_mgg = form.querySelector('[name="nominal_per_minggu"]');
  const jml_mgg = form.querySelector('[name="jumlah_minggu"]');

  if (nama && !_required(nama, 'Nama Semester')) ok = false;
  if (tahun && !_required(tahun, 'Tahun Akademik')) ok = false;
  if (nom_bln && !_positiveNumber(nom_bln, 'Nominal per Bulan')) ok = false;
  if (nom_mgg && !_positiveNumber(nom_mgg, 'Nominal per Minggu')) ok = false;
  if (jml_mgg && !_positiveNumber(jml_mgg, 'Jumlah Minggu')) ok = false;

  // Validasi minimal 1 bulan dipilih
  const bulanCheckboxes = form.querySelectorAll('[name="months"]:checked');
  if (bulanCheckboxes.length === 0) {
    const bulanGroup = form.querySelector('.bulan-group');
    if (bulanGroup) {
      let errDiv = bulanGroup.querySelector('.bulan-error');
      if (!errDiv) {
        errDiv = document.createElement('div');
        errDiv.classList.add('bulan-error', 'text-danger', 'mt-1');
        errDiv.style.fontSize = '0.83rem';
        bulanGroup.appendChild(errDiv);
      }
      errDiv.textContent = 'Pilih minimal satu bulan pembayaran.';
    }
    ok = false;
  } else {
    const errDiv = form.querySelector('.bulan-error');
    if (errDiv) errDiv.textContent = '';
  }

  return ok;
}


// ──────────────────────────────────────────────────────────
// FORM VALIDASI: PENGELUARAN (Tambah & Edit)
// ──────────────────────────────────────────────────────────
function _validatePengeluaran(form) {
  let ok = true;
  const tanggal = form.querySelector('[name="tanggal"]');
  const kategori = form.querySelector('[name="kategori"]');
  const keperluan = form.querySelector('[name="keperluan"]');
  const nominal = form.querySelector('[name="nominal"]');

  if (tanggal && !_required(tanggal, 'Tanggal')) ok = false;
  if (kategori && !_required(kategori, 'Kategori')) ok = false;
  if (keperluan && !_required(keperluan, 'Keperluan')) ok = false;
  if (nominal && !_positiveNumber(nominal, 'Nominal')) ok = false;

  // Validasi nominal tidak melebihi saldo (dari data-saldo attribute)
  if (nominal) {
    const saldo = parseInt(form.dataset.saldo || '0', 10);
    const val = parseInt(nominal.value, 10);
    if (!isNaN(val) && saldo > 0 && val > saldo) {
      const saldoFormatted = saldo.toLocaleString('id-ID');
      _showError(nominal, `Nominal melebihi saldo kas tersedia (Rp ${saldoFormatted}).`);
      ok = false;
    }
  }

  return ok;
}


// ──────────────────────────────────────────────────────────
// FORM VALIDASI: PENGATURAN SISTEM
// ──────────────────────────────────────────────────────────
function _validatePengaturan(form) {
  let ok = true;
  const nama = form.querySelector('[name="nama_organisasi"]');
  const nom_bln = form.querySelector('[name="nominal_per_bulan"]');
  const nom_mgg = form.querySelector('[name="nominal_per_minggu"]');
  const jml_mgg = form.querySelector('[name="jumlah_minggu"]');
  const logo = form.querySelector('[name="logo"]');

  if (nama && !_required(nama, 'Nama Organisasi')) ok = false;
  if (nom_bln && !_positiveNumber(nom_bln, 'Nominal per Bulan')) ok = false;
  if (nom_mgg && !_positiveNumber(nom_mgg, 'Nominal per Minggu')) ok = false;
  if (jml_mgg && !_positiveNumber(jml_mgg, 'Jumlah Minggu')) ok = false;
  if (logo && !_fileExtension(logo, ['png', 'jpg', 'jpeg'])) ok = false;

  return ok;
}


// ──────────────────────────────────────────────────────────
// FORM VALIDASI: PROFIL ADMIN
// ──────────────────────────────────────────────────────────
function _validateProfil(form) {
  let ok = true;
  const nama = form.querySelector('[name="nama"]');
  const email = form.querySelector('[name="email"]');
  const username = form.querySelector('[name="username"]');
  const pwLama = form.querySelector('[name="password_lama"]');
  const pwBaru = form.querySelector('[name="password_baru"]');
  const pwKonfirmasi = form.querySelector('[name="password_konfirmasi"]');
  const foto = form.querySelector('[name="foto_profil"]');

  if (nama && !_required(nama, 'Nama Lengkap')) ok = false;
  if (email && !_email(email)) ok = false;
  if (username && !_required(username, 'Username')) ok = false;
  if (foto && !_fileExtension(foto, ['png', 'jpg', 'jpeg'])) ok = false;

  // Jika password baru diisi → wajib password lama & konfirmasi cocok
  if (pwBaru && pwBaru.value.trim()) {
    if (pwLama && !_required(pwLama, 'Password Lama')) ok = false;
    if (pwBaru.value.length < 6) {
      _showError(pwBaru, 'Password baru minimal 6 karakter.');
      ok = false;
    } else {
      _clearError(pwBaru);
    }
    if (pwKonfirmasi && pwBaru.value !== pwKonfirmasi.value) {
      _showError(pwKonfirmasi, 'Konfirmasi password tidak cocok.');
      ok = false;
    } else if (pwKonfirmasi) {
      _clearError(pwKonfirmasi);
    }
  }

  return ok;
}


// ──────────────────────────────────────────────────────────
// DISPATCHER: Deteksi form berdasarkan data-form-type atau action URL
// ──────────────────────────────────────────────────────────
function _getValidator(form) {
  const type = form.dataset.formType || '';
  const action = form.action || '';

  if (type === 'login' || action.includes('/login')) return _validateLogin;
  if (type === 'mahasiswa' || action.includes('/mahasiswa')) return _validateMahasiswa;
  if (type === 'semester' || action.includes('/semester')) return _validateSemester;
  if (type === 'pengeluaran' || action.includes('/pengeluaran')) return _validatePengeluaran;
  if (type === 'pengaturan' || action.includes('/pengaturan')) return _validatePengaturan;
  if (type === 'profil' || action.includes('/profil')) return _validateProfil;

  return null;
}


// ──────────────────────────────────────────────────────────
// INISIALISASI
// ──────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {

  // 1. Pasang validasi ke semua form yang punya class .needs-validation
  document.querySelectorAll('form.needs-validation').forEach(form => {
    form.addEventListener('submit', (e) => {
      const validator = _getValidator(form);
      let valid = true;

      if (validator) {
        valid = validator(form);
      } else {
        // Fallback: HTML5 native constraint validation
        valid = form.checkValidity();
      }

      if (!valid) {
        e.preventDefault();
        e.stopPropagation();
        form.classList.add('was-validated');
        // Scroll ke error pertama
        const firstError = form.querySelector('.is-invalid');
        if (firstError) {
          firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
          firstError.focus();
        }
      } else {
        form.classList.add('was-validated');
      }
    });

    // Real-time: hapus error saat user mulai mengetik
    form.querySelectorAll('input, select, textarea').forEach(el => {
      el.addEventListener('input', () => {
        if (el.classList.contains('is-invalid')) {
          el.classList.remove('is-invalid');
          el.classList.add('is-valid');
          const fb = el.nextElementSibling;
          if (fb && fb.classList.contains('invalid-feedback')) {
            fb.textContent = '';
          }
        }
      });
    });
  });

  // 2. Konfirmasi delete — semua tombol dengan class .confirm-delete
  document.querySelectorAll('.confirm-delete').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const msg = btn.dataset.confirmMsg || 'Yakin ingin menghapus data ini?';
      if (!confirm(msg)) {
        e.preventDefault();
      }
    });
  });

  // 3. Limit file size upload: 5 MB
  document.querySelectorAll('input[type="file"]').forEach(input => {
    input.addEventListener('change', () => {
      const maxSize = 5 * 1024 * 1024; // 5 MB
      if (input.files[0] && input.files[0].size > maxSize) {
        _showError(input, 'Ukuran file maksimal 5 MB.');
        input.value = '';
      } else if (input.files[0]) {
        _clearError(input);
      }
    });
  });

  // 4. Format nominal input: tampilkan titik ribuan saat blur, simpan angka saat submit
  document.querySelectorAll('input[data-format="nominal"]').forEach(input => {
    input.addEventListener('blur', () => {
      const val = parseInt(input.value.replace(/\./g, ''), 10);
      if (!isNaN(val)) {
        input.setAttribute('data-raw', val);
      }
    });
  });

});

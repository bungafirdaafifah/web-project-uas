import os

from sqlalchemy.pool import NullPool

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Muat .env untuk dev lokal (no-op kalau python-dotenv tak ada / file tak ada)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, '.env'))
except ImportError:
    pass


def _normalize_db_url(url):
    """Supabase/Heroku kadang beri skema 'postgres://', SQLAlchemy butuh
    'postgresql://'. Normalkan supaya connection string mentah bisa langsung
    dipakai tanpa diedit."""
    if url and url.startswith('postgres://'):
        return url.replace('postgres://', 'postgresql://', 1)
    return url


class Config:
    # Flask Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key_kas_mahasiswa_12345')

    # Database — set DATABASE_URL ke connection string Postgres Supabase.
    # Fallback SQLite hanya untuk jalan lokal tanpa konfigurasi apa pun.
    SQLALCHEMY_DATABASE_URI = _normalize_db_url(
        os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'kas_management.db')}")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Supabase pakai PgBouncer (transaction pooler) di lingkungan serverless.
    # NullPool = jangan pooling di sisi app, biar tiap request pakai koneksi
    # bersih dari pooler Supabase. SQLite lokal tak terpengaruh.
    # ponytail: NullPool pas untuk Vercel serverless; ganti ke QueuePool kalau
    # nanti deploy ke server long-running biar koneksi di-reuse.
    if SQLALCHEMY_DATABASE_URI.startswith('postgresql://'):
        SQLALCHEMY_ENGINE_OPTIONS = {'poolclass': NullPool}

    # Upload Configurations
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # Limit uploads to 5MB

    # Ensure upload directories exist
    @staticmethod
    def init_app(app):
        profile_upload_dir = os.path.join(Config.UPLOAD_FOLDER, 'profile')
        logo_upload_dir = os.path.join(Config.UPLOAD_FOLDER)

        # Jangan membuat folder saat berjalan di Vercel
        if not os.environ.get("VERCEL"):
            os.makedirs(profile_upload_dir, exist_ok=True)
            os.makedirs(logo_upload_dir, exist_ok=True)
